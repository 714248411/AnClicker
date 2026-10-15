"""Stoppable flow traversal for explicit jumps; exceptional links are never fallbacks."""
from anclicker.domain.flow_jumps import JUMP_KINDS, row_node, target_config

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'execute_control_flow': ('from', 'anclicker.execution.flow_control_runtime', ('execute_control_flow',), 0),
    'comment_successors_snapshot_disabled_ids': ('from', 'anclicker.domain.flow_comments', ('comment_successors', 'snapshot_disabled_ids'), 0),
    'ordered_edges_jump_only_nodes': ('from', 'anclicker.execution.flow_control_runtime', ('ordered_edges', 'jump_only_nodes'), 0),
    'substitute_variables': ('from', 'anclicker.execution.actions', ('substitute_variables',), 0),
    'release_recorded_inputs': ('from', 'anclicker.execution.actions', ('release_recorded_inputs',), 0),
})



def execute_jump_flow(worker, snapshot, context, start_id=None, single=False):
    if any(command.type_id in {'循环', '条件循环'} for command in snapshot.commands):
        execute_control_flow = _module_imports.load('execute_control_flow')
        return execute_control_flow(worker, snapshot, context, start_id, single)
    comment_successors, snapshot_disabled_ids = _module_imports.load('comment_successors_snapshot_disabled_ids')
    commented = comment_successors(snapshot)
    disabled = snapshot_disabled_ids(snapshot)
    nodes = {node.node_id: node for node in snapshot.nodes}
    commands = {command.id: command for command in snapshot.commands}
    ordered = sorted((node for node in snapshot.nodes if node.command_id is not None),
                     key=lambda node: commands[node.command_id].order)
    active = [node.node_id for node in ordered if commands[node.command_id].type_id != '报错跳转']
    all_edges = {node_id: [] for node_id in nodes}
    normal = {node_id: [] for node_id in nodes}
    for edge in snapshot.edges:
        all_edges[edge.source].append(edge)
        if edge.kind not in JUMP_KINDS:
            normal[edge.source].append(edge)
    ordered_edges, jump_only_nodes = _module_imports.load('ordered_edges_jump_only_nodes')
    normal = {key: ordered_edges(edges, nodes) for key, edges in normal.items()}
    connected = {value for edge in snapshot.edges if edge.kind not in JUMP_KINDS
                 for value in (edge.source, edge.target)}
    incoming = {edge.target for edge in snapshot.edges if edge.kind not in JUMP_KINDS}
    pending = [edge.target for edge in normal.get('start',())]
    jump_only = jump_only_nodes(snapshot, normal, pending, active)
    run_unconnected = getattr(worker, 'run_unconnected', True)
    if run_unconnected:
        pending += [node_id for node_id in active if node_id in connected and node_id not in incoming and node_id not in jump_only]
        pending += [node_id for node_id in active if nodes[node_id].type_id in {'循环','条件循环'} and node_id in connected and node_id not in jump_only]
    pending = list(dict.fromkeys(pending))
    strict = start_id is not None
    if strict:
        pending.clear()
    current = start_id or 'end'
    visited, path, iterations = set(), set(), {}

    def following(node_id):
        edges = normal.get(node_id,())
        if edges:
            pending[0:0] = [edge.target for edge in edges[1:]]
            return edges[0].target
        if strict and node_id in active:
            index = active.index(node_id)+1
            return active[index] if index < len(active) else 'end'
        return 'end'

    def resolve(command, node_id, kind, prefix=''):
        mode,row,file_path = target_config(command.parameters,prefix)
        if mode == '连线节点':
            targets = [edge.target for edge in all_edges[node_id] if edge.kind == kind]
            if len(targets) != 1:
                raise ValueError(f'{command.type_id} {prefix}分支需要连接一个目标节点')
            return targets[0], True
        if mode == '当前项目行':
            return row_node(snapshot,row), True
        if mode == '其他项目行':
            substitute_variables = _module_imports.load('substitute_variables')
            worker._run_project(substitute_variables(context,file_path),context,start_row=row)
            return None, False
        return None, False

    def transfer(target):
        nonlocal strict
        strict = True
        pending.clear()
        path.clear()
        iterations.clear()
        # A backward jump must replay held-key timelines from a new time origin.
        context.metadata.pop('recorded_clocks',None)
        return target

    steps = 0
    while worker.start_state and not context.stop_requested:
        if current == 'end':
            pending[:] = [value for value in pending if value not in visited and value != 'end']
            if not pending and not strict and run_unconnected:
                pending[:] = [node_id for node_id in active if node_id not in visited and node_id not in connected and node_id not in jump_only]
            if not pending: return
            current = pending.pop(0)
            path.clear()
        steps += 1
        if steps > 500_000:
            raise ValueError('跳转流程超过 500000 步，已停止以避免无限跳转')
        if not worker.check_mutex(): return
        node = nodes.get(current)
        if node is None or node.command_id is None:
            raise ValueError('跳转目标不存在：'+str(current))
        if current in commented:
            if single:
                return
            if current in path:
                raise ValueError('注释区间跳转形成环路')
            path.add(current)
            visited.add(current)
            targets = commented[current]
            pending[0:0] = [target for target in targets[1:] if target != 'end']
            current = targets[0]
            continue
        command = commands[node.command_id]
        if command.type_id == '报错跳转':
            raise ValueError('报错模块不能作为普通执行入口')
        if current in path:
            if command.type_id not in {'循环','条件循环'}:
                raise ValueError('普通流程环路缺少循环控制节点')
            path.clear()
        elif current in visited and not strict and not iterations:
            current = 'end'
            continue
        path.add(current)
        visited.add(current)
        result, jumped = None, False
        while worker.start_state and not context.stop_requested:
            if not worker.check_mutex(): return
            try:
                result = worker._execute_one(command,context)
                worker._persist_variables(context.variables)
                if context.stop_requested:
                    worker.request_stop()
                    return
                if command.type_id == '变量比较':
                    prefix,kind = ('是',7) if bool(result) else ('否',8)
                    target,changed = resolve(command,current,kind,prefix)
                    if changed:
                        current = transfer(target)
                        jumped = True
                break
            except Exception as error:
                if context.stop_requested or not worker.start_state: return
                binding = next((edge for edge in all_edges[current] if edge.kind == 5
                                and nodes[edge.target].command_id not in disabled),None)
                if binding is not None:
                    release_recorded_inputs = _module_imports.load('release_recorded_inputs')
                    release_recorded_inputs(context)
                    handler = commands[nodes[binding.target].command_id]
                    context.emit(f'指令 {command.id} 报错，启用报错跳转 {handler.id}：{error}')
                    if not context.metadata.get('child_project'):
                        worker._notify_command(handler.type_id,str(handler.id))
                    try:
                        target,changed = resolve(handler,binding.target,6)
                    except Exception as jump_error:
                        context.emit(f'报错跳转配置或目标执行失败：{jump_error}')
                        worker.request_stop()
                        return
                    if changed:
                        current = transfer(target)
                        jumped = True
                    elif handler.parameters.get('旧版转移后结束') is True:
                        # Legacy cross-branch errors transfer, rather than call-and-return.
                        return
                    break
                action = worker._handle_command_error(command,error)
                if action == 'retry': continue
                if action == 'continue': break
                worker.request_stop()
                return
        if not worker.start_state or context.stop_requested: return
        if single: return
        if jumped: continue
        if command.type_id == '变量比较':
            # Explicit continue / child return resumes at the next table row.
            index = active.index(current)+1
            current = transfer(active[index] if index<len(active) else 'end')
            continue
        edges = normal.get(current,())
        if command.type_id in {'条件判断','颜色判断'}:
            kind = 1 if bool(result) else 2
        elif command.type_id in {'循环','条件循环'}:
            if command.type_id == '条件循环' or command.parameters.get('方式') in {'条件','cond'}:
                kind = 3 if bool(result) else 4
            else:
                count = iterations.get(current,0)
                kind = 3 if count < max(0,int(command.parameters.get('次数',1))) else 4
                if kind == 3: iterations[current] = count+1
                else: iterations.pop(current,None)
        else:
            current = following(current)
            continue
        edge = next((edge for edge in edges if edge.kind==kind),None)
        current = edge.target if edge else 'end'
