"""Execute loop regions atomically before ordinary continuations."""
from flow_jumps import JUMP_KINDS, row_node, target_config

LOOPS = {'循环', '条件循环'}
CONTROLS = LOOPS | {'条件判断', '颜色判断', '变量比较'}


def ordered_edges(edges, nodes):
    return sorted(edges, key=lambda edge: nodes[edge.target].type_id not in CONTROLS)


def reachable(start, outgoing, blocked=()):
    seen, pending = set(), list(start)
    while pending:
        node = pending.pop()
        if node in seen or node in blocked:
            continue
        seen.add(node)
        pending.extend(outgoing.get(node, ()))
    return seen


def jump_only_nodes(snapshot, normal, roots, active):
    """Keep side branches out of automatic roots in start-connected graphs."""
    if not any(root in active for root in roots):
        return set()  # Preserve row-order fallback in files without a main flow.
    adjacency = {node: [edge.target for edge in edges] for node, edges in normal.items()}
    targets = {edge.target for edge in snapshot.edges if edge.kind in (6, 7, 8)}
    commands = {command.id: command for command in snapshot.commands}
    nodes = {node.node_id: node for node in snapshot.nodes}
    for binding in snapshot.edges:
        if binding.kind != 5:
            continue
        handler = commands.get(nodes[binding.target].command_id)
        if handler is None:
            continue
        try:
            mode, row, _ = target_config(handler.parameters)
            if mode == '当前项目行':
                targets.add(row_node(snapshot, row))
        except (ValueError, KeyError):
            pass  # Invalid handlers report their error only when triggered.
    return reachable(targets, adjacency) - reachable(roots, adjacency)


def loop_regions(snapshot):
    headers = [node.node_id for node in snapshot.nodes if node.type_id in LOOPS]
    if not headers:
        return {}
    base = {}
    for edge in snapshot.edges:
        if edge.kind not in {3, 5, 6}:
            base.setdefault(edge.source, set()).add(edge.target)
    bodies = {header: [e.target for e in snapshot.edges if e.source == header and e.kind == 3]
              for header in headers}
    exits = {header: [e.target for e in snapshot.edges if e.source == header and e.kind == 4]
             for header in headers}
    regions = {header: set() for header in headers}
    # An inner return-loop can have an implicit continuation on its body node.
    # Summarize that continuation on its header when finding an outer region.
    for _ in range(len(headers) + 1):
        outgoing = {node: set(targets) for node, targets in base.items()}
        for header, members in regions.items():
            for member in members:
                outgoing.setdefault(header, set()).update(base.get(member, set()) - members - {header})
        incoming = {}
        for source, targets in outgoing.items():
            for target in targets:
                incoming.setdefault(target, set()).add(source)
        updated = {}
        for header in headers:
            forward = reachable(bodies[header], outgoing, {header, 'end'})
            reverse = reachable(incoming.get(header, ()), incoming, {header, 'start'})
            members = forward & reverse
            if not members and bodies[header]:
                members = forward - reachable(exits[header], outgoing)
            updated[header] = members
        for _ in headers:
            changed = False
            for header, members in updated.items():
                expanded = set(members)
                for nested in members & updated.keys():
                    if header not in updated[nested]:
                        expanded.update(updated[nested])
                if expanded != members:
                    updated[header] = expanded
                    changed = True
            if not changed:
                break
        if updated == regions:
            break
        regions = updated
    for header, members in regions.items():
        if header in members:
            raise ValueError('循环范围交叉，请将内外循环分别连接到各自的循环节点')
    return regions


class _Transfer(Exception):
    def __init__(self, target):
        self.target = target


class _Stop(Exception):
    pass


def execute_control_flow(worker, snapshot, context, start_id=None, single=False):
    from flow_comments import comment_successors, snapshot_disabled_ids
    commented, disabled = comment_successors(snapshot), snapshot_disabled_ids(snapshot)
    nodes = {node.node_id: node for node in snapshot.nodes}
    commands = {command.id: command for command in snapshot.commands}
    ordered = sorted((node for node in snapshot.nodes if node.command_id is not None),
                     key=lambda node: commands[node.command_id].order)
    active = [node.node_id for node in ordered if node.type_id != '报错跳转']
    all_edges = {node: [] for node in nodes}
    normal = {node: [] for node in nodes}
    for edge in snapshot.edges:
        all_edges[edge.source].append(edge)
        if edge.kind not in JUMP_KINDS:
            normal[edge.source].append(edge)
    for node in normal:
        normal[node] = ordered_edges(normal[node], nodes)
    regions = {key: value for key, value in loop_regions(snapshot).items() if key not in commented}
    connected = {value for edges in normal.values() for edge in edges for value in (edge.source, edge.target)}
    incoming = {edge.target for edges in normal.values() for edge in edges}
    adjacency = {key: [edge.target for edge in edges] for key, edges in normal.items()}
    roots = [edge.target for edge in normal.get('start', ())]
    jump_only = jump_only_nodes(snapshot, normal, roots, active)
    run_unconnected = getattr(worker, 'run_unconnected', True)
    if run_unconnected:
        roots += [node for node in active if node in connected and node not in incoming and node not in jump_only]
        covered = reachable(roots, adjacency)
        for header in regions:
            if header in connected and header not in covered and header not in jump_only:
                roots.append(header)
                covered.update(reachable([header], adjacency))
        roots += [node for node in active if node not in connected and node not in jump_only]
    roots = list(dict.fromkeys(roots))
    visited, executing_loops = set(), []
    steps = 0
    strict = start_id is not None

    def checkpoint():
        nonlocal steps
        if not worker.start_state or context.stop_requested or not worker.check_mutex():
            raise _Stop()
        steps += 1
        if steps > 500_000:
            raise ValueError('流程执行超过 500000 步，已停止以避免卡死')

    def next_row(node):
        index = active.index(node) + 1
        return active[index] if index < len(active) else 'end'

    def resolve(command, node, kind, prefix=''):
        mode, row, path = target_config(command.parameters, prefix)
        if mode == '连线节点':
            targets = [edge.target for edge in all_edges[node] if edge.kind == kind]
            if len(targets) != 1:
                raise ValueError(f'{command.type_id} {prefix}分支需要连接一个目标节点')
            return targets[0], True
        if mode == '当前项目行':
            return row_node(snapshot, row), True
        if mode == '其他项目行':
            from instructions.common.actions import substitute_variables
            worker._run_project(substitute_variables(context, path), context, start_row=row)
        return None, False

    def execute(node):
        command = commands[nodes[node].command_id]
        visited.add(node)
        while worker.start_state and not context.stop_requested:
            checkpoint()
            try:
                result = worker._execute_one(command, context)
                worker._persist_variables(context.variables)
                if context.stop_requested:
                    worker.request_stop()
                    raise _Stop()
                return result
            except _Stop:
                raise
            except Exception as error:
                if context.stop_requested or not worker.start_state:
                    raise _Stop()
                binding = next((edge for edge in all_edges[node] if edge.kind == 5
                                and nodes[edge.target].command_id not in disabled), None)
                if binding is not None:
                    from instructions.common.actions import release_recorded_inputs
                    release_recorded_inputs(context)
                    handler = commands[nodes[binding.target].command_id]
                    context.emit(f'指令 {command.id} 报错，启用报错跳转 {handler.id}：{error}')
                    target, changed = resolve(handler, binding.target, 6)
                    if changed:
                        raise _Transfer(target)
                    if handler.parameters.get('旧版转移后结束') is True:
                        raise _Stop()
                    return None
                action = worker._handle_command_error(command, error)
                if action == 'retry':
                    continue
                if action == 'continue':
                    return None
                worker.request_stop()
                raise _Stop()
        raise _Stop()

    def run_loop(header, entry):
        if len(executing_loops) >= 100:
            raise ValueError('循环嵌套超过 100 层，请简化流程')
        members = regions[header]
        command = commands[nodes[header].command_id]
        body = next((e.target for e in normal[header] if e.kind == 3), None)
        exit_target = next((e.target for e in normal[header] if e.kind == 4), None)
        conditional = command.type_id == '条件循环' or command.parameters.get('方式') in {'条件', 'cond'}
        count = max(0, int(command.parameters.get('次数', 1))) if not conditional else 0
        completed, deferred = 0, []
        executing_loops.append(header)
        try:
            # A return loop entered through its body counts that first pass.
            if entry != header and (conditional or count > 0):
                deferred += walk(entry, members, header)
                completed = 1
            while True:
                result = execute(header)
                if (not conditional and completed >= count) or (conditional and not bool(result)) or body is None:
                    break
                deferred += walk(body, members, header)
                completed += 1
            return list(dict.fromkeys(([exit_target] if exit_target else []) + deferred))
        finally:
            executing_loops.pop()

    def walk(start, allowed=None, boundary=None):
        pending, seen, deferred = [start], set(), []
        while pending:
            checkpoint()
            current = pending.pop(0)
            if current in (None, 'end', boundary):
                continue
            if allowed is not None and current not in allowed:
                deferred.append(current)
                continue
            if current in seen or (allowed is None and current in visited and not strict):
                continue
            node = nodes.get(current)
            if node is None or node.command_id is None:
                raise ValueError('流程目标不存在：' + str(current))
            seen.add(current)
            if current in commented:
                visited.add(current)
                pending[0:0] = commented[current]
                continue
            owners = [header for header, members in regions.items()
                      if header not in executing_loops and (current == header or current in members)
                      and (allowed is None or header in allowed)]
            if owners and not single:
                header = max(owners, key=lambda key: len(regions[key]))
                deferred_targets = run_loop(header, current)
                seen.update(regions[header] | {header})
                visited.update(regions[header] | {header})
                pending[0:0] = deferred_targets
                continue
            command = commands[node.command_id]
            try:
                result = execute(current)
            except _Transfer as transfer:
                if transfer.target == boundary:
                    pending = []
                    continue
                if allowed is not None and transfer.target in allowed:
                    pending, seen = [transfer.target], set()
                    continue
                raise
            if single:
                return deferred
            if command.type_id == '变量比较':
                target, changed = resolve(command, current, 7 if bool(result) else 8, '是' if bool(result) else '否')
                if changed:
                    if target == boundary:
                        pending = []
                        continue
                    if allowed is not None and target in allowed:
                        pending, seen = [target], set()
                        continue
                    raise _Transfer(target)
                pending[0:0] = [next_row(current)]
                continue
            edges = normal[current]
            if command.type_id in {'条件判断', '颜色判断'}:
                kind = 1 if bool(result) else 2
                edges = [edge for edge in edges if edge.kind == kind]
            targets = [edge.target for edge in edges]
            if not targets and strict and allowed is None and command.type_id not in CONTROLS:
                targets = [next_row(current)]
            pending[0:0] = targets
        return deferred

    try:
        pending = [start_id] if strict else roots
        while pending:
            current = pending.pop(0)
            if current in visited and not strict:
                continue
            try:
                walk(current)
            except _Transfer as transfer:
                strict = True
                pending = [transfer.target] if transfer.target != 'end' else []
                context.metadata.pop('recorded_clocks', None)
    except _Stop:
        return
