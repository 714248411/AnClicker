"""Thread ownership shared by the table, graph and execution compiler."""
from dataclasses import replace

THREAD = '多线程启动'


def thread_parents(commands):
    parents, stack = {}, []
    for command in sorted(commands, key=lambda c: (c.order, c.id or 0)):
        if command.type_id != THREAD:
            continue
        depth = max(0, int(command.parameters.get('嵌套层级', 0)))
        depth = min(depth, len(stack))
        stack = stack[:depth]
        parents[command.id] = stack[-1] if stack else None
        stack.append(command.id)
    return parents


def thread_structure(commands, nodes, edges, *, exclusive=False):
    ordered = sorted(commands, key=lambda c: (c.order, c.id or 0))
    threads = {c.id: c for c in ordered if c.type_id == THREAD}
    by_id = {n.command_id: n.node_id for n in nodes if n.command_id is not None}
    by_node = {v: k for k, v in by_id.items()}
    starters = {by_id[cid]: cid for cid in threads if cid in by_id}
    outgoing = {}
    for edge in edges:
        outgoing.setdefault(edge.source, []).append(edge.target)
    parents = thread_parents(ordered)
    result = {}
    for cid, command in threads.items():
        explicit = int(command.parameters.get('入口编号', 0) or 0)
        entries = ([by_id[explicit]] if explicit in by_id else []) if explicit else list(outgoing.get(by_id[cid], ()))
        members, boundaries, pending = set(), set(), list(entries)
        while pending:
            current = pending.pop()
            if current in ('start', 'end') or current in members:
                continue
            if current in starters:
                boundaries.add(starters[current])
                continue
            members.add(current)
            pending.extend(outgoing.get(current, ()))
        result[cid] = {'direct': members, 'boundaries': boundaries, 'entries': entries,
                       'parent': parents[cid], 'node': by_id[cid], 'explicit': explicit}
    if exclusive:
        # A main-flow node or a shared continuation must not glue unrelated
        # thread cards into one movable lock group. Execution validation still
        # receives the full branch reachability (exclusive=False).
        main, pending = set(), list(outgoing.get('start', ()))
        while pending:
            current = pending.pop()
            if current in main or current in starters or current in ('start', 'end'):
                continue
            main.add(current)
            pending.extend(outgoing.get(current, ()))
        claims = {}
        for info in result.values():
            for node in info['direct']:
                claims[node] = claims.get(node, 0) + 1
        shared = main | {node for node, count in claims.items() if count > 1}
        for info in result.values():
            info['direct'].difference_update(shared)
    # Descendants are folded and moved together, regardless of their own state.
    for cid, info in result.items():
        members = {by_node[n] for n in info['direct'] if n in by_node}
        pending, visited = [child for child, p in parents.items() if p == cid], {cid}
        while pending:
            child = pending.pop()
            if child in visited:
                continue
            visited.add(child)
            members.add(child)
            members.update(by_node[n] for n in result[child]['direct'] if n in by_node)
            pending.extend(k for k, p in parents.items() if p == child)
        info['members'] = members
    return result


def thread_group_order(commands, nodes, edges):
    """Keep connected groups contiguous even when Start fans out to many roots."""
    structure = thread_structure(commands, nodes, edges, exclusive=True)
    positions = {c.id: i for i, c in enumerate(commands)}
    managed = {cid for cid, info in structure.items() if not info['explicit'] or info['parent'] is not None}
    for cid in list(managed):
        parent = structure[cid]['parent']
        while parent is not None:
            managed.add(parent)
            parent = structure[parent]['parent']
    owners = {}
    for cid, info in structure.items():
        if cid not in managed:
            continue
        for member in info['members']:
            # Prefer the innermost group for immediate children.
            previous = owners.get(member)
            if previous is None or cid in structure[previous]['members']:
                owners[member] = cid
    children = {}
    for member, owner in owners.items():
        if member != owner:
            children.setdefault(owner, []).append(member)
    result, visited = [], set()
    def emit(cid):
        if cid in visited:
            return
        visited.add(cid)
        result.append(cid)
        for child in sorted(children.get(cid, ()), key=lambda value: positions[value]):
            emit(child)
    for command in commands:
        if command.id not in owners:
            emit(command.id)
    for command in commands:
        emit(command.id)
    return result


def grouped_commands(commands, nodes, edges):
    structure = thread_structure(commands, nodes, edges, exclusive=True)
    depths = {}
    for cid, info in structure.items():
        depths[cid] = depths[info['parent']] + 1 if info['parent'] is not None else 0
    return tuple(replace(c, parameters={**c.parameters, '嵌套层级': depths[c.id],
                 '线程分组成员': sorted(structure[c.id]['members'])})
                 if c.id in structure else c for c in commands)
