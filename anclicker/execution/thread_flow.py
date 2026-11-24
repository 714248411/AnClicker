"""Compile connected thread groups into isolated execution scopes."""
from dataclasses import replace
from anclicker.domain.graph_models import EdgeRecord
from anclicker.domain.thread_groups import thread_structure


def prepare_connected_flow(snapshot, context):
    if context.metadata.get('parallel_worker') and snapshot is context.metadata.get('parallel_scope_snapshot'):
        return snapshot
    structure = thread_structure(snapshot.commands, snapshot.nodes, snapshot.edges)
    managed = {cid for cid, info in structure.items() if not info['explicit'] or info['parent'] is not None}
    for cid in list(managed):
        parent = structure[cid]['parent']
        while parent is not None:
            managed.add(parent)
            parent = structure[parent]['parent']
    automatic = {cid: info for cid, info in structure.items() if cid in managed}
    if not automatic:
        for key in ('connected_thread_plans', 'connected_reserved', 'parallel_source_snapshot'):
            context.metadata.pop(key, None)
        return snapshot
    by_node = {n.node_id: n.command_id for n in snapshot.nodes}
    by_id = {n.command_id: n.node_id for n in snapshot.nodes}
    parents = {cid: info['parent'] if info['parent'] in automatic else None for cid, info in automatic.items()}
    owners = {}
    for cid, info in automatic.items():
        for node in info['direct']:
            if node in owners and owners[node] != cid:
                raise ValueError('多个多线程的步骤重叠，请将各线程分别连接到结束')
            owners[node] = cid
    commands = tuple(replace(c, parameters={**c.parameters, '_连线线程': c.id})
                     if c.id in automatic else c for c in snapshot.commands)
    source = replace(snapshot, commands=commands)
    context.metadata['parallel_source_snapshot'] = source
    def reachable(roots, edges):
        adjacency = {}
        for edge in edges:
            adjacency.setdefault(edge.source, []).append(edge.target)
        seen, pending = set(), list(roots)
        while pending:
            node = pending.pop()
            if node in seen or node == 'end':
                continue
            seen.add(node)
            pending.extend(adjacency.get(node, ()))
        return seen

    plans = {}
    for cid, info in automatic.items():
        children = {by_id[child] for child, parent in parents.items() if parent == cid}
        allowed = set(info['direct']) | children
        edges = []
        for edge in snapshot.edges:
            if edge.source not in allowed:
                continue
            child = by_node.get(edge.source)
            continuation = edge.source not in children or structure[child]['explicit']
            target = edge.target if edge.target in allowed and continuation else 'end'
            edges.append(replace(edge, target=target))
        roots = [node for node in info['entries'] if node in allowed]
        seen = reachable(roots, edges)
        # A child wired directly from Start moves into its parent's scope.
        # Sibling headers reached through another child's body also run in parallel.
        roots.extend(node for node in children if node not in seen)
        edges.extend(EdgeRecord('start', node) for node in dict.fromkeys(roots))
        sources = {edge.source for edge in edges}
        edges.extend(EdgeRecord(node, 'end') for node in allowed if node not in sources)
        plans[cid] = (replace(source, edges=tuple(dict.fromkeys(edges))), allowed)
    context.metadata['connected_thread_plans'] = plans
    hidden = set(owners) | {by_id[cid] for cid, parent in parents.items() if parent is not None}
    main_edges = []
    headers = {by_id[cid] for cid in automatic}
    for edge in snapshot.edges:
        if edge.source in hidden:
            continue
        if edge.target in hidden:
            if edge.source not in headers and edge.source != 'start':
                raise ValueError('主流程与多线程步骤重叠，请将各线程分别连接到结束')
            continue
        if edge.source not in headers or structure[by_node[edge.source]]['explicit']:
            main_edges.append(edge)
    reachable_main = reachable(['start'], snapshot.edges)
    for cid, parent in parents.items():
        if parent is None:
            node = by_id[cid]
            if not any(edge.source == node for edge in main_edges):
                main_edges.append(EdgeRecord(node, 'end'))
            if node in reachable_main:
                main_edges.append(EdgeRecord('start', node))
    context.metadata['connected_reserved'] = hidden
    return replace(source, edges=tuple(dict.fromkeys(main_edges)))
