"""Graph-derived loop groups for table order and folding."""
from flow_control_runtime import loop_regions


def loop_groups(snapshot):
    nodes = {node.node_id: node for node in snapshot.nodes}
    try:
        regions = loop_regions(snapshot)
    except ValueError:
        return {}  # An incomplete/crossed draft remains editable.
    groups = {nodes[header].command_id: {nodes[item].command_id for item in members
              if item in nodes and nodes[item].command_id is not None}
              for header, members in regions.items() if members}
    # Only properly nested or disjoint regions have an unambiguous table group.
    invalid = set()
    for a, a_body in groups.items():
        for b, b_body in groups.items():
            if a == b:
                continue
            if (a_body | {a}) & (b_body | {b}) and not (
                    a_body | {a} <= b_body | {b} or b_body | {b} <= a_body | {a}):
                invalid.update((a, b))
    return {header: members for header, members in groups.items() if header not in invalid}


def aligned_loop_order(snapshot):
    order = [command.id for command in sorted(snapshot.commands, key=lambda command: command.order)]
    groups = loop_groups(snapshot)
    by_node = {node.node_id: node.command_id for node in snapshot.nodes}
    entries = {by_node[edge.source]: by_node.get(edge.target)
               for edge in snapshot.edges if edge.kind == 3}

    def arrange(items, parent=None):
        available = set(items)
        headers = [header for header in groups if header in available and header != parent]
        outer = [header for header in headers if not any(header in groups[other] for other in headers if other != header)]
        owner = {item: header for header in outer for item in (groups[header] | {header}) & available}
        result, emitted = [], set()
        for item in items:
            header = owner.get(item)
            if header is None:
                result.append(item)
            elif header not in emitted:
                emitted.add(header)
                body = [member for member in items if member in groups[header]]
                entry = entries.get(header)
                if entry in body:
                    body.remove(entry)
                    body.insert(0, entry)
                result.extend([header] + arrange(body, header))
        return result

    return arrange(order)
