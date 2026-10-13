"""Comment ranges use persisted table order, independent of canvas positions."""
BELOW = '暂不运行以下指令'
ABOVE = '暂不运行以上指令'
MARKERS = {BELOW, ABOVE}


def disabled_command_ids(commands):
    ordered = sorted(commands, key=lambda command: (command.order, command.id or 0))
    disabled, stack = set(), []
    for index, command in enumerate(ordered):
        if command.type_id == BELOW:
            stack.append(index)
            disabled.add(command.id)
        elif command.type_id == ABOVE:
            start = stack.pop() if stack else 0
            disabled.update(item.id for item in ordered[start:index + 1])
    for start in stack:
        disabled.update(item.id for item in ordered[start:])
    return disabled


def graph_comment_nodes(snapshot):
    """Connected comments follow edges; isolated commands retain table ranges."""
    nodes = {n.node_id: n for n in snapshot.nodes}
    forward = {key: [] for key in nodes}
    backward = {key: [] for key in nodes}
    for edge in snapshot.edges:
        forward[edge.source].append(edge.target)
        backward[edge.target].append(edge.source)
    below = {n.node_id for n in snapshot.nodes if n.type_id == BELOW}
    above = {n.node_id for n in snapshot.nodes if n.type_id == ABOVE}

    def walk(start, links, stops):
        seen, pending = set(), [start]
        while pending:
            node = pending.pop()
            if node in seen:
                continue
            seen.add(node)
            if node not in stops or node == start:
                pending.extend(links[node])
        return seen

    disabled = set()
    paired_above = set()
    for start in below:
        if not forward[start] and not backward[start]:
            continue
        reached = walk(start, forward, above)
        ends = reached & above
        if ends:
            ancestors = set().union(*(walk(end, backward, {start}) for end in ends))
            disabled.update(reached & ancestors)
            paired_above.update(ends)
        else:
            disabled.update(reached)
    for end in above - paired_above:
        if forward[end] or backward[end]:
            disabled.update(walk(end, backward, below))
    isolated = [c for c in snapshot.commands
                if any(n.command_id == c.id and not forward[n.node_id] and not backward[n.node_id]
                       for n in snapshot.nodes)]
    table_disabled = disabled_command_ids(isolated)
    disabled.update(n.node_id for n in snapshot.nodes if n.command_id in table_disabled)
    disabled.update(below | above)
    return {key for key in disabled if nodes[key].command_id is not None}


def snapshot_disabled_ids(snapshot):
    disabled = graph_comment_nodes(snapshot)
    return {node.command_id for node in snapshot.nodes if node.node_id in disabled}


def comment_successors(snapshot):
    disabled = graph_comment_nodes(snapshot)
    outgoing = {n.node_id: [] for n in snapshot.nodes}
    connected = set()
    for edge in snapshot.edges:
        connected.update((edge.source, edge.target))
        # Error branches are never activated by skipping a command.
        if edge.kind != 5:
            outgoing[edge.source].append(edge.target)
    ordered = sorted(snapshot.commands, key=lambda c: (c.order, c.id or 0))
    nodes = {n.command_id: n.node_id for n in snapshot.nodes if n.command_id is not None}
    targets = {}
    for source in disabled:
        seen, exits, pending = set(), [], list(outgoing[source])
        if source not in connected:
            index = next(i for i,c in enumerate(ordered) if nodes[c.id] == source)
            pending = [nodes[c.id] for c in ordered[index + 1:] if nodes[c.id] not in disabled][:1]
        while pending:
            node = pending.pop(0)
            if node in seen:
                continue
            seen.add(node)
            if node in disabled:
                pending.extend(outgoing[node])
            else:
                exits.append(node)
        targets[source] = tuple(exits or ['end'])
    return targets


def fold_ranges(commands):
    """Return opener ID -> enclosed IDs, keeping both boundary rows visible."""
    ordered = sorted(commands, key=lambda command: (command.order, command.id or 0))
    stack, ranges = [], {}
    for index, command in enumerate(ordered):
        if command.type_id == BELOW:
            stack.append(index)
        elif command.type_id == ABOVE and stack:
            start = stack.pop()
            ranges[ordered[start].id] = {item.id for item in ordered[start + 1:index]}
    for start in stack:
        ranges[ordered[start].id] = {item.id for item in ordered[start + 1:]}
    return ranges


def aligned_marker_order(snapshot):
    """Move only comment markers; leave ordinary commands in their current order."""
    commands = sorted(snapshot.commands, key=lambda c: (c.order, c.id or 0))
    order = [c.id for c in commands]
    forward = {n.node_id: [] for n in snapshot.nodes}
    backward = {n.node_id: [] for n in snapshot.nodes}
    nodes = {n.command_id: n.node_id for n in snapshot.nodes if n.command_id is not None}
    by_node = {n.node_id: n.command_id for n in snapshot.nodes}
    ordinary = {c.id for c in commands if c.type_id not in MARKERS}
    for edge in snapshot.edges:
        if edge.kind >= 5:
            continue
        forward[edge.source].append(edge.target)
        backward[edge.target].append(edge.source)

    def reachable(start, links):
        seen, pending = {start}, list(links[start])
        while pending:
            node = pending.pop()
            if node in seen:
                continue
            seen.add(node)
            pending.extend(links[node])
        return {by_node[n] for n in seen if by_node[n] in ordinary}

    for command in commands:
        if command.type_id not in MARKERS:
            continue
        node = nodes[command.id]
        before, after = reachable(node, backward), reachable(node, forward)
        # Nodes on a loop are both before and after; they provide no ordering bound.
        before, after = before - after, after - before
        if not before and not after:
            continue
        order.remove(command.id)
        if command.type_id == BELOW and after:
            index = min(order.index(cid) for cid in after)
        elif before:
            index = max(order.index(cid) for cid in before) + 1
        else:
            index = min(order.index(cid) for cid in after)
        order.insert(index, command.id)
    return order


def connected_fold_ranges(snapshot):
    """Connected openers fold only their downstream paths, stopping at closers."""
    ranges = fold_ranges(snapshot.commands)
    nodes = {node.node_id: node for node in snapshot.nodes}
    outgoing = {key: [] for key in nodes}
    connected = set()
    for edge in snapshot.edges:
        connected.update((edge.source, edge.target))
        outgoing[edge.source].append(edge.target)
    for start in snapshot.nodes:
        if start.type_id != BELOW or start.node_id not in connected:
            continue
        seen, hidden, pending = {start.node_id}, set(), list(outgoing[start.node_id])
        while pending:
            key = pending.pop()
            if key in seen:
                continue
            seen.add(key)
            node = nodes[key]
            if node.type_id == ABOVE or node.command_id is None:
                continue
            hidden.add(node.command_id)
            pending.extend(outgoing[key])
        ranges[start.command_id] = hidden
    return ranges
