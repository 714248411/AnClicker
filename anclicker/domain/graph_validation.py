"""Pure graph validation. No database or GUI dependencies."""
from __future__ import annotations
import json
import math
from collections.abc import Sequence, Mapping
from typing import Any
from anclicker.domain.graph_models import *
from anclicker.domain.graph_models import _SerializedCommand

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'flow_jumps_JUMP_KINDS_etc': ('from', 'anclicker.domain.flow_jumps', ('JUMP_KINDS', 'ERROR_BIND', 'ERROR_TARGET', 'COMPARE_TRUE', 'COMPARE_FALSE'), 0),
})


def decode_parameters(parameters_json: str) -> dict[str, Any]:
    try:
        parameters = json.loads(parameters_json)
    except (TypeError, json.JSONDecodeError) as error_:
        raise GraphValidationError("参数JSON不是有效 JSON") from error_
    if not isinstance(parameters, dict):
        raise GraphValidationError("参数JSON必须表示对象")
    return parameters


def encode_parameters(parameters: Any) -> str:
    if not isinstance(parameters, Mapping):
        raise ValueError("parameters 必须是字典或映射")
    try:
        return json.dumps(
            dict(parameters),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error_:
        raise ValueError("parameters 必须可以序列化为 JSON") from error_


def validate_records(
    commands: Sequence[_SerializedCommand],
    nodes: Sequence[NodeRecord],
    edges: Sequence[EdgeRecord],
    *,
    require_order: bool,
    allow_incomplete: bool = False,
    validate_cycles: bool = False,
) -> list[str]:
    command_ids = [command.id for command in commands]
    if len(command_ids) != len(set(command_ids)) or any(
        command_id <= 0 for command_id in command_ids
    ):
        raise GraphValidationError("命令 ID 必须是唯一的正整数")
    orders = [command.order for command in commands]
    if len(orders) != len(set(orders)) or any(order < 0 for order in orders):
        raise GraphValidationError("命令排序必须唯一且为非负整数")
    if require_order and sorted(orders) != list(range(len(commands))):
        raise GraphValidationError("命令排序必须从 0 开始连续且唯一")
    for command in commands:
        if not command.type_id.strip():
            raise GraphValidationError("命令类型标识不能为空")
        decode_parameters(command.parameters_json)
        if command.repeat_count <= 0:
            raise GraphValidationError("命令重复次数必须是正整数")

    node_ids = [node.node_id for node in nodes]
    if len(node_ids) != len(set(node_ids)) or any(not item for item in node_ids):
        raise GraphValidationError("节点 ID 必须唯一且不能为空")
    node_by_id = {node.node_id: node for node in nodes}
    if set(node_by_id) < {START_NODE_ID, END_NODE_ID}:
        raise GraphValidationError("节点图缺少固定的开始或结束节点")
    if (
        node_by_id[START_NODE_ID].node_type != START_NODE_TYPE
        or node_by_id[END_NODE_ID].node_type != END_NODE_TYPE
    ):
        raise GraphValidationError("固定节点的类型不正确")

    boundary_nodes = [node for node in nodes if node.node_type != INSTRUCTION_NODE_TYPE]
    if {node.node_id for node in boundary_nodes} != {START_NODE_ID, END_NODE_ID}:
        raise GraphValidationError("节点图只能有一个开始节点和一个结束节点")
    instruction_nodes = [
        node for node in nodes if node.node_type == INSTRUCTION_NODE_TYPE
    ]
    if any(node.node_type not in NODE_TYPES for node in nodes):
        raise GraphValidationError("节点类型不受支持")
    if any(node.command_id is not None for node in boundary_nodes):
        raise GraphValidationError("开始和结束节点不能关联命令")
    instruction_command_ids = [node.command_id for node in instruction_nodes]
    if any(command_id is None for command_id in instruction_command_ids):
        raise GraphValidationError("指令节点必须关联命令")
    if len(instruction_command_ids) != len(set(instruction_command_ids)):
        raise GraphValidationError("每条命令只能关联一个节点")
    if set(instruction_command_ids) != set(command_ids):
        raise GraphValidationError("所有命令必须且只能在图中出现一次")
    if any(not math.isfinite(node.x) or not math.isfinite(node.y) for node in nodes):
        raise GraphValidationError("节点坐标必须是有限数值")

    JUMP_KINDS, ERROR_BIND, ERROR_TARGET, COMPARE_TRUE, COMPARE_FALSE = _module_imports.load('flow_jumps_JUMP_KINDS_etc')
    command_by_id = {command.id: command for command in commands}
    type_by_node = {node.node_id: command_by_id[node.command_id].type_id
                    for node in instruction_nodes}
    jump_slots = set()
    outgoing: dict[str, set[str]] = {node_id: set() for node_id in node_by_id}
    incoming: dict[str, set[str]] = {node_id: set() for node_id in node_by_id}
    edge_pairs: set[tuple[str, str]] = set()
    for edge in edges:
        if edge.source not in node_by_id or edge.target not in node_by_id:
            raise GraphValidationError("连线引用了不存在的节点")
        pair = (edge.source, edge.target)
        if pair in edge_pairs:
            raise GraphValidationError("不能重复连接同一对节点")
        if edge.source == edge.target:
            raise GraphValidationError("节点不能连接到自身")
        edge_pairs.add(pair)
        if edge.kind not in range(9):
            raise GraphValidationError("未知连线类型")
        source_type = type_by_node.get(edge.source)
        target_type = type_by_node.get(edge.target)
        if edge.kind in JUMP_KINDS:
            if edge.source in {START_NODE_ID, END_NODE_ID} or edge.target == START_NODE_ID:
                raise GraphValidationError("开始/结束节点不能设置跳转输出，开始节点不能作为跳转目标")
            if (edge.source, edge.kind) in jump_slots:
                raise GraphValidationError("每个跳转接口只能连接一个目标")
            jump_slots.add((edge.source, edge.kind))
            if edge.kind == ERROR_BIND:
                if source_type == '报错跳转' or target_type != '报错跳转':
                    raise GraphValidationError("异常接口只能连接报错跳转模块")
            elif target_type == '报错跳转':
                raise GraphValidationError("跳转目标不能是报错跳转模块")
            elif edge.kind == ERROR_TARGET and source_type != '报错跳转':
                raise GraphValidationError("报错跳转目标线只能由报错模块发出")
            elif edge.kind in {COMPARE_TRUE,COMPARE_FALSE} and source_type != '变量比较':
                raise GraphValidationError("变量比较分支只能由变量比较模块发出")
            continue  # Exceptional edges do not change ordinary topology or form normal loops.
        if source_type in {'报错跳转','变量比较'} or target_type == '报错跳转':
            raise GraphValidationError("报错/变量比较模块必须使用专用跳转连线")
        outgoing[edge.source].add(edge.target)
        incoming[edge.target].add(edge.source)
    if incoming[START_NODE_ID] or outgoing[END_NODE_ID]:
        raise GraphValidationError("开始节点不能有输入，结束节点不能有输出")
    if len(outgoing[START_NODE_ID]) > 1 or (
        not allow_incomplete and len(outgoing[START_NODE_ID]) != 1
    ):
        raise GraphValidationError("开始节点必须连接一条输出")

    command_by_id = {command.id: command for command in commands}
    for node in instruction_nodes:
        command = command_by_id[int(node.command_id)]
        if command.type_id in {"条件判断", "颜色判断", "循环", "条件循环"}:
            branch_count = len(outgoing[node.node_id])
            if branch_count > 2:
                raise GraphValidationError("条件或循环节点最多只能连接两条输出")
            if not allow_incomplete and branch_count != 2:
                raise GraphValidationError("条件或循环节点必须连接两条输出")
            expected_kinds = {1, 2} if command.type_id in {"条件判断", "颜色判断"} else {3, 4}
            actual_kinds = {
                int(edge.kind) for edge in edges if edge.source == node.node_id and edge.kind not in JUMP_KINDS
            }
            if not actual_kinds <= expected_kinds or len(actual_kinds) != branch_count:
                raise GraphValidationError("条件或循环节点的分支类型无效或重复")
            if not allow_incomplete and actual_kinds != expected_kinds:
                raise GraphValidationError("条件或循环节点缺少完整的分支连线")

    command_order = {command.id: command.order for command in commands}
    def sort_key(node_id: str):
        node = node_by_id[node_id]
        if node_id == START_NODE_ID:
            return (-1, node_id)
        if node_id == END_NODE_ID:
            return (len(commands) + 1, node_id)
        return (command_order.get(node.command_id, len(commands)), node_id)

    indegree = {node_id: len(sources) for node_id, sources in incoming.items()}
    ready = sorted(
        (node_id for node_id, count in indegree.items() if count == 0),
        key=sort_key,
    )
    ordered_nodes: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered_nodes.append(current)
        for target in sorted(outgoing[current], key=sort_key):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort(key=sort_key)
    if len(ordered_nodes) != len(node_by_id):
        if allow_incomplete and not validate_cycles:
            remaining = sorted(set(node_by_id) - set(ordered_nodes), key=sort_key)
            return [*ordered_nodes, *remaining]
        loop_nodes = {
            node.node_id
            for node in instruction_nodes
            if command_by_id[int(node.command_id)].type_id in {"循环", "条件循环"}
        }
        index = 0
        indexes: dict[str, int] = {}
        lowlinks: dict[str, int] = {}
        stack: list[str] = []
        on_stack: set[str] = set()
        cyclic_components: list[set[str]] = []

        def strong_connect(node_id: str) -> None:
            nonlocal index
            indexes[node_id] = lowlinks[node_id] = index
            index += 1
            stack.append(node_id)
            on_stack.add(node_id)
            for target_id in outgoing[node_id]:
                if target_id not in indexes:
                    strong_connect(target_id)
                    lowlinks[node_id] = min(lowlinks[node_id], lowlinks[target_id])
                elif target_id in on_stack:
                    lowlinks[node_id] = min(lowlinks[node_id], indexes[target_id])
            if lowlinks[node_id] == indexes[node_id]:
                component: set[str] = set()
                while stack:
                    member = stack.pop()
                    on_stack.remove(member)
                    component.add(member)
                    if member == node_id:
                        break
                if len(component) > 1 or node_id in outgoing[node_id]:
                    cyclic_components.append(component)

        for node_id in node_by_id:
            if node_id not in indexes:
                strong_connect(node_id)
        if not cyclic_components or any(
            not (component & loop_nodes) for component in cyclic_components
        ):
            raise GraphValidationError("流程环路必须由循环或条件循环节点控制")
        # A structured loop has no topological order.  Preserve the stable
        # command order while traversal follows persisted links at runtime.
        ordered_nodes = sorted(node_by_id, key=sort_key)
    if allow_incomplete:
        return ordered_nodes

    reachable = {START_NODE_ID}
    pending = [START_NODE_ID]
    while pending:
        for target in outgoing[pending.pop()]:
            if target not in reachable:
                reachable.add(target)
                pending.append(target)
    can_reach_end = {END_NODE_ID}
    pending = [END_NODE_ID]
    while pending:
        for source in incoming[pending.pop()]:
            if source not in can_reach_end:
                can_reach_end.add(source)
                pending.append(source)
    missing_from_start = set(node_by_id) - reachable
    missing_to_end = set(node_by_id) - can_reach_end
    if missing_from_start or missing_to_end:
        raise GraphValidationError(
            "流程缺少完整连线：所有指令都必须从开始节点可达并最终连接到结束节点"
        )

    ordered_command_ids = [
        node_by_id[node_id].command_id
        for node_id in ordered_nodes
        if node_by_id[node_id].node_type == INSTRUCTION_NODE_TYPE
    ]
    if require_order:
        stored_command_ids = [
            command.id for command in sorted(commands, key=lambda item: item.order)
        ]
        if ordered_command_ids != stored_command_ids:
            raise GraphValidationError("命令排序与流程图拓扑顺序不一致")
    return ordered_nodes
