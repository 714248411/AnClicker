"""Workbook parsing without database mutation."""
from __future__ import annotations
import math
from typing import Any, Sequence
from anclicker.domain.graph_models import *
from anclicker.domain.graph_models import _SerializedCommand
from anclicker.domain.graph_validation import decode_parameters, encode_parameters, validate_records

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'SettingsRepository': ('from', 'anclicker.storage.settings', ('SettingsRepository',), 0),
})


class WorkbookCodec:
    def __init__(self, is_known_type):
        self._is_known_type = is_known_type

    _decode_parameters = staticmethod(decode_parameters)
    _encode_parameters = staticmethod(encode_parameters)
    _validate_records = staticmethod(validate_records)

    @staticmethod
    def _replace_sheet(workbook: Any, title: str, headers: Sequence[str]):
        if title in workbook.sheetnames:
            del workbook[title]
        sheet = workbook.create_sheet(title)
        sheet.append(list(headers))
        return sheet


    @staticmethod
    def _sheet_rows(
        workbook: Any, sheet_name: str, headers: Sequence[str]
    ) -> list[tuple[Any, ...]]:
        sheet = workbook[sheet_name]
        if sheet.max_column != len(headers):
            raise WorkbookValidationError(f"“{sheet_name}”工作表列数不正确")
        actual_headers = [
            sheet.cell(1, column).value
            for column in range(1, len(headers) + 1)
        ]
        if actual_headers != list(headers):
            raise WorkbookValidationError(f"“{sheet_name}”工作表标题不正确")
        rows: list[tuple[Any, ...]] = []
        for row_index in range(2, sheet.max_row + 1):
            values = tuple(
                sheet.cell(row_index, column).value
                for column in range(1, len(headers) + 1)
            )
            if all(value is None for value in values):
                continue
            rows.append(values)
        return rows


    @classmethod
    def _edge_sheet_rows(cls, workbook: Any) -> list[tuple[Any, ...]]:
        """Read current three-column links and legacy two-column links."""
        sheet = workbook["连线"]
        if sheet.max_column not in {2, 3}:
            raise WorkbookValidationError("“连线”工作表列数不正确")
        headers = [sheet.cell(1, column).value for column in range(1, sheet.max_column + 1)]
        expected = EDGE_SHEET_HEADERS if sheet.max_column == 3 else LEGACY_EDGE_SHEET_HEADERS
        if headers != expected:
            raise WorkbookValidationError("“连线”工作表标题不正确")
        rows: list[tuple[Any, ...]] = []
        for row_index in range(2, sheet.max_row + 1):
            values = tuple(
                sheet.cell(row_index, column).value
                for column in range(1, sheet.max_column + 1)
            )
            if not all(value is None for value in values):
                rows.append(values)
        return rows


    def _parse_workbook(
        self, workbook: Any
    ) -> tuple[
        list[_SerializedCommand],
        list[NodeRecord],
        list[EdgeRecord],
        dict[str, list[tuple[str, Any, Any, Any]]],
    ]:
        if set(workbook.sheetnames) != set(WORKBOOK_SHEETS) or len(
            workbook.sheetnames
        ) != len(WORKBOOK_SHEETS):
            raise WorkbookValidationError(
                "工作簿必须且只能包含“命令、节点、连线、设置”四个工作表"
            )
        command_rows = self._sheet_rows(
            workbook, "命令", COMMAND_SHEET_HEADERS
        )
        node_rows = self._sheet_rows(workbook, "节点", NODE_SHEET_HEADERS)
        edge_rows = self._edge_sheet_rows(workbook)

        commands: list[_SerializedCommand] = []
        for row in command_rows:
            command_id, type_id, parameters_json, repeat_count, error_policy, note, order = row
            if (
                isinstance(command_id, bool)
                or not isinstance(command_id, int)
                or command_id <= 0
            ):
                raise WorkbookValidationError("命令 ID 必须是正整数")
            if not isinstance(type_id, str) or not type_id.strip():
                raise WorkbookValidationError("类型标识不能为空")
            if not self._is_known_type(type_id.strip()):
                raise WorkbookValidationError(f"未知指令类型：{type_id}")
            if not isinstance(parameters_json, str):
                raise WorkbookValidationError("参数JSON必须是文本")
            try:
                decoded = self._decode_parameters(parameters_json)
                canonical_json = self._encode_parameters(decoded)
            except (GraphValidationError, ValueError) as error_:
                raise WorkbookValidationError(str(error_)) from error_
            if (
                isinstance(repeat_count, bool)
                or not isinstance(repeat_count, int)
                or repeat_count <= 0
            ):
                raise WorkbookValidationError("重复次数必须是正整数")
            if (
                isinstance(order, bool)
                or not isinstance(order, int)
                or order < 0
            ):
                raise WorkbookValidationError("排序必须是非负整数")
            if error_policy is None:
                error_policy = ""
            if note is None:
                note = ""
            if not isinstance(error_policy, str) or not isinstance(note, str):
                raise WorkbookValidationError("异常处理和备注必须是文本")
            commands.append(
                _SerializedCommand(
                    command_id,
                    type_id.strip(),
                    canonical_json,
                    repeat_count,
                    error_policy,
                    note,
                    order,
                )
            )

        nodes: list[NodeRecord] = []
        for row in node_rows:
            node_id, command_id, node_type, x, y = row
            if not isinstance(node_id, str) or not node_id.strip():
                raise WorkbookValidationError("节点 ID 不能为空")
            if node_type not in NODE_TYPES:
                raise WorkbookValidationError(f"节点类型不受支持：{node_type}")
            if command_id is not None and (
                isinstance(command_id, bool)
                or not isinstance(command_id, int)
                or command_id <= 0
            ):
                raise WorkbookValidationError("节点关联命令 ID 必须是正整数")
            if (
                isinstance(x, bool)
                or isinstance(y, bool)
                or not isinstance(x, (int, float))
                or not isinstance(y, (int, float))
                or not math.isfinite(float(x))
                or not math.isfinite(float(y))
            ):
                raise WorkbookValidationError("节点坐标必须是有限数值")
            nodes.append(
                NodeRecord(node_id.strip(), command_id, node_type, float(x), float(y))
            )

        edges: list[EdgeRecord] = []
        command_type_by_id = {command.id: command.type_id for command in commands}
        source_type_by_node = {
            node.node_id: command_type_by_id.get(node.command_id, "") for node in nodes
        }
        legacy_branch_index: dict[str, int] = {}
        for edge_row in edge_rows:
            source, target = edge_row[:2]
            if len(edge_row) == 3:
                kind = edge_row[2]
            else:
                branch_index = legacy_branch_index.get(str(source), 0)
                legacy_branch_index[str(source)] = branch_index + 1
                source_type = source_type_by_node.get(str(source), "")
                if source_type in {"条件判断", "颜色判断"}:
                    kind = (1, 2)[min(branch_index, 1)]
                elif source_type in {"循环", "条件循环"}:
                    kind = (3, 4)[min(branch_index, 1)]
                else:
                    kind = 0
            if (
                not isinstance(source, str)
                or not source.strip()
                or not isinstance(target, str)
                or not target.strip()
            ):
                raise WorkbookValidationError("连线的源节点和目标节点不能为空")
            if isinstance(kind, bool) or not isinstance(kind, int) or kind not in range(9):
                raise WorkbookValidationError("连线类型必须是 0 到 4 的整数")
            edges.append(EdgeRecord(source.strip(), target.strip(), kind))
        try:
            self._validate_records(
                commands, nodes, edges, require_order=True, allow_incomplete=True
            )
        except GraphValidationError as error_:
            raise WorkbookValidationError(str(error_)) from error_

        SettingsRepository = _module_imports.load('SettingsRepository')

        settings = SettingsRepository._read_settings_from_excel(workbook)
        if settings is None:
            raise WorkbookValidationError("“设置”工作表格式或内容不正确")
        return commands, nodes, edges, settings


def write_graph_sheets(workbook, command_rows, node_rows, edge_rows):
    """Serialize already-read records; the caller owns storage and settings."""
    for worksheet in list(workbook.worksheets):
        workbook.remove(worksheet)
    for title, headers, rows in (
        ('命令', COMMAND_SHEET_HEADERS, command_rows),
        ('节点', NODE_SHEET_HEADERS, node_rows),
        ('连线', EDGE_SHEET_HEADERS, edge_rows),
    ):
        sheet = workbook.create_sheet(title)
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
