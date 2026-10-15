"""Persistent graph values and workbook protocol constants."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional
from anclicker.domain.instructions import CommandRecord, InstructionDraft

START_NODE_ID = "start"
END_NODE_ID = "end"
START_NODE_TYPE = "start"
INSTRUCTION_NODE_TYPE = "instruction"
END_NODE_TYPE = "end"
NODE_TYPES = frozenset(
    {START_NODE_TYPE, INSTRUCTION_NODE_TYPE, END_NODE_TYPE}
)

COMMAND_COLUMNS = (
    "ID",
    "类型标识",
    "参数JSON",
    "重复次数",
    "异常处理",
    "备注",
    "排序",
)
NODE_COLUMNS = ("节点ID", "命令ID", "节点类型", "X", "Y")
EDGE_COLUMNS = ("源节点ID", "目标节点ID")

COMMAND_SHEET_HEADERS = list(COMMAND_COLUMNS)
NODE_SHEET_HEADERS = list(NODE_COLUMNS)
LEGACY_EDGE_SHEET_HEADERS = list(EDGE_COLUMNS)
EDGE_SHEET_HEADERS = [*EDGE_COLUMNS, "连接类型"]
SETTINGS_SHEET_HEADERS = ["类型", "名称", "值", "附加值", "排序"]
WORKBOOK_SHEETS = ("命令", "节点", "连线", "设置")


class GraphRepositoryError(RuntimeError):
    """Base error raised by the graph repository."""


class GraphSchemaError(GraphRepositoryError):
    """The database contains an unsupported command/graph schema."""


class GraphValidationError(GraphRepositoryError):
    """The stored or requested graph is not one complete valid flow."""


class WorkbookValidationError(GraphRepositoryError, ValueError):
    """The workbook does not conform to the node-editor protocol."""


@dataclass(frozen=True)
class NodeRecord:
    node_id: str
    command_id: Optional[int]
    node_type: str
    x: float
    y: float


@dataclass(frozen=True)
class NodeView:
    """Node-editor-ready node data returned by :meth:`snapshot`."""

    node_id: str
    command_id: Optional[int]
    node_type: str
    type_id: Optional[str]
    display_name: str
    x: float
    y: float
    repeat_count: int = 1
    parameters: Optional[dict[str, Any]] = None
    note: str = ""
    width: Optional[float] = None
    height: Optional[float] = None

    @property
    def role(self) -> Optional[str]:
        """Terminal role consumed directly by ``NodeEditorWidget``."""
        return self.node_type if self.node_type in {START_NODE_TYPE, END_NODE_TYPE} else None


@dataclass(frozen=True)
class EdgeRecord:
    source: str
    target: str
    kind: int = 0

    def __iter__(self):
        """Allow consumers that accept a two-item edge sequence."""
        yield self.source
        yield self.target


@dataclass(frozen=True)
class GraphSnapshot:
    commands: tuple[CommandRecord, ...]
    nodes: tuple[NodeView, ...]
    edges: tuple[EdgeRecord, ...]


@dataclass(frozen=True)
class _SerializedCommand:
    id: int
    type_id: str
    parameters_json: str
    repeat_count: int
    error_policy: str
    note: str
    order: int
