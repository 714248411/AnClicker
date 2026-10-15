"""Resolve the binding that can reach an editor without executing its flow."""
import json


def previous_binding(snapshot, command_id=None):
    commands = {command.id: command for command in snapshot.commands}
    nodes = {node.node_id: node for node in snapshot.nodes}
    current = next((n for n in snapshot.nodes if n.command_id == command_id), None) if command_id is not None else None
    incoming = {}
    for edge in snapshot.edges:
        incoming.setdefault(edge.target, []).append(edge.source)
    states = {}

    def record(command):
        value = dict(command.parameters) if command is not None and command.type_id == '绑定选择窗口' else None
        states[json.dumps(value, sort_keys=True, ensure_ascii=False)] = value

    if current is not None and incoming.get(current.node_id):
        visited = {current.node_id}
        pending = list(incoming[current.node_id])
        while pending:
            node_id = pending.pop()
            if node_id in visited:
                continue
            visited.add(node_id)
            node = nodes.get(node_id)
            command = commands.get(node.command_id) if node is not None else None
            if command is not None and command.type_id in ('绑定选择窗口', '解除后台绑定'):
                record(command)
            elif incoming.get(node_id):
                pending.extend(incoming[node_id])
            else:
                record(None)
    else:
        binding = None
        for command in sorted(snapshot.commands, key=lambda item: item.order):
            if command.id == command_id:
                break
            if command.type_id == '绑定选择窗口':
                binding = command
            elif command.type_id == '解除后台绑定':
                binding = None
        record(binding)
    if len(states) > 1:
        raise ValueError('上方分支使用了不同的后台绑定（或已解除绑定），请明确连接目标窗口后再截图或取点。')
    return next(iter(states.values()), None)
