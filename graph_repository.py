"""Single-chain command graph persistence and workbook protocol.

The node graph is deliberately restricted to one complete chain::

    start -> instruction ... -> instruction -> end

The executor continues to consume :class:`CommandRecord` objects ordered by
``order``.  Connections are the source of truth whenever the chain changes;
the repository rewrites command ordering in the same transaction.
"""

from __future__ import annotations

import contextlib
import importlib
import json
import math
import sqlite3
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional

from instructions.models import CommandRecord, InstructionDraft


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
EDGE_SHEET_HEADERS = list(EDGE_COLUMNS)
SETTINGS_SHEET_HEADERS = ["类型", "名称", "值", "附加值", "排序"]
WORKBOOK_SHEETS = ("命令", "节点", "连线", "设置")


class GraphRepositoryError(RuntimeError):
    """Base error raised by the graph repository."""


class GraphSchemaError(GraphRepositoryError):
    """The database contains an unsupported command/graph schema."""


class GraphValidationError(GraphRepositoryError):
    """The stored or requested graph is not one complete single chain."""


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

    @property
    def role(self) -> Optional[str]:
        """Terminal role consumed directly by ``NodeEditorWidget``."""
        return self.node_type if self.node_type in {START_NODE_TYPE, END_NODE_TYPE} else None


@dataclass(frozen=True)
class EdgeRecord:
    source: str
    target: str

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


class GraphRepository:
    """Transactional persistence for the linear command graph.

    ``instruction_resolver`` may return an ``InstructionSpec`` (or a mapping)
    for a type ID.  It is used for node display names and strict workbook type
    validation.  ``valid_type_ids`` is useful for tests and headless tools.
    When neither is supplied the central ``instructions.registry`` is lazily
    discovered; if it is not importable yet, non-empty type IDs are accepted.
    """

    def __init__(
        self,
        db_path: str,
        *,
        instruction_resolver: Optional[Callable[[str], Any]] = None,
        valid_type_ids: Optional[Iterable[str]] = None,
    ) -> None:
        self.db_path = db_path
        self._instruction_resolver = instruction_resolver
        self._valid_type_ids = (
            frozenset(str(item) for item in valid_type_ids)
            if valid_type_ids is not None
            else None
        )

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    @classmethod
    def initialize_schema(cls, connection: sqlite3.Connection) -> None:
        """Create the graph tables or reject any unknown existing shape."""
        connection.execute("PRAGMA foreign_keys=ON")
        existing_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }

        cls._create_or_validate_command_table(connection, existing_tables)
        cls._create_or_validate_node_table(connection, existing_tables)
        cls._create_or_validate_edge_table(connection, existing_tables)

        node_count = connection.execute("SELECT COUNT(*) FROM 节点").fetchone()[0]
        command_count = connection.execute("SELECT COUNT(*) FROM 命令").fetchone()[0]
        edge_count = connection.execute("SELECT COUNT(*) FROM 节点连接").fetchone()[0]
        if node_count == 0 and command_count == 0 and edge_count == 0:
            connection.executemany(
                "INSERT INTO 节点(节点ID, 命令ID, 节点类型, X, Y) "
                "VALUES (?, NULL, ?, ?, ?)",
                [
                    (START_NODE_ID, START_NODE_TYPE, 0.0, 0.0),
                    (END_NODE_ID, END_NODE_TYPE, 320.0, 0.0),
                ],
            )
            connection.execute(
                "INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
                (START_NODE_ID, END_NODE_ID),
            )
        elif node_count == 0 or edge_count == 0:
            raise GraphSchemaError("命令与节点图必须同时存在，不能初始化不完整的图结构")

        cls._validate_connection(connection, require_order=True)

    @staticmethod
    def _table_columns(
        connection: sqlite3.Connection, table_name: str
    ) -> tuple[str, ...]:
        return tuple(
            row[1]
            for row in connection.execute(f'PRAGMA table_info("{table_name}")')
        )

    @staticmethod
    def _table_signature(
        connection: sqlite3.Connection, table_name: str
    ) -> tuple[tuple[str, str, int, int], ...]:
        return tuple(
            (str(row[1]), str(row[2]).upper(), int(row[3]), int(row[5]))
            for row in connection.execute(f'PRAGMA table_info("{table_name}")')
        )

    @staticmethod
    def _table_sql(connection: sqlite3.Connection, table_name: str) -> str:
        row = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        return "" if row is None or row[0] is None else " ".join(str(row[0]).upper().split())

    @staticmethod
    def _unique_indexes(
        connection: sqlite3.Connection, table_name: str
    ) -> set[tuple[str, ...]]:
        indexes: set[tuple[str, ...]] = set()
        for row in connection.execute(f'PRAGMA index_list("{table_name}")'):
            if not row[2]:
                continue
            indexes.add(
                tuple(
                    item[2]
                    for item in connection.execute(
                        f'PRAGMA index_info("{row[1]}")'
                    )
                )
            )
        return indexes

    @staticmethod
    def _foreign_keys(
        connection: sqlite3.Connection, table_name: str
    ) -> set[tuple[str, str, str, str]]:
        return {
            (row[3], row[2], row[4], row[6].upper())
            for row in connection.execute(f'PRAGMA foreign_key_list("{table_name}")')
        }

    @classmethod
    def _create_or_validate_command_table(
        cls, connection: sqlite3.Connection, existing_tables: set[str]
    ) -> None:
        if "命令" not in existing_tables:
            connection.execute(
                "CREATE TABLE 命令 ("
                "ID INTEGER PRIMARY KEY AUTOINCREMENT, "
                "类型标识 TEXT NOT NULL, "
                "参数JSON TEXT NOT NULL, "
                "重复次数 INTEGER NOT NULL, "
                "异常处理 TEXT NOT NULL, "
                "备注 TEXT NOT NULL, "
                "排序 INTEGER NOT NULL UNIQUE)"
            )
            return
        columns = cls._table_columns(connection, "命令")
        if columns != COMMAND_COLUMNS:
            raise GraphSchemaError(
                "命令表必须使用节点编辑器新结构："
                "ID、类型标识、参数JSON、重复次数、异常处理、备注、排序"
            )
        if ("排序",) not in cls._unique_indexes(connection, "命令"):
            raise GraphSchemaError("命令.排序必须具有唯一约束")
        expected_signature = (
            ("ID", "INTEGER", 0, 1),
            ("类型标识", "TEXT", 1, 0),
            ("参数JSON", "TEXT", 1, 0),
            ("重复次数", "INTEGER", 1, 0),
            ("异常处理", "TEXT", 1, 0),
            ("备注", "TEXT", 1, 0),
            ("排序", "INTEGER", 1, 0),
        )
        if cls._table_signature(connection, "命令") != expected_signature:
            raise GraphSchemaError("命令表字段类型或约束不正确")
        if "AUTOINCREMENT" not in cls._table_sql(connection, "命令"):
            raise GraphSchemaError("命令.ID必须是稳定的自增主键")

    @classmethod
    def _create_or_validate_node_table(
        cls, connection: sqlite3.Connection, existing_tables: set[str]
    ) -> None:
        if "节点" not in existing_tables:
            connection.execute(
                "CREATE TABLE 节点 ("
                "节点ID TEXT NOT NULL PRIMARY KEY, "
                "命令ID INTEGER UNIQUE, "
                "节点类型 TEXT NOT NULL CHECK(节点类型 IN "
                "('start', 'instruction', 'end')), "
                "X REAL NOT NULL, Y REAL NOT NULL, "
                "CHECK((节点类型='instruction' AND 命令ID IS NOT NULL) OR "
                "(节点类型 IN ('start', 'end') AND 命令ID IS NULL)), "
                "FOREIGN KEY(命令ID) REFERENCES 命令(ID) ON DELETE CASCADE)"
            )
            return
        if cls._table_columns(connection, "节点") != NODE_COLUMNS:
            raise GraphSchemaError("节点表结构不受支持")
        expected_signature = (
            ("节点ID", "TEXT", 1, 1),
            ("命令ID", "INTEGER", 0, 0),
            ("节点类型", "TEXT", 1, 0),
            ("X", "REAL", 1, 0),
            ("Y", "REAL", 1, 0),
        )
        if cls._table_signature(connection, "节点") != expected_signature:
            raise GraphSchemaError("节点表字段类型或约束不正确")
        if ("命令ID",) not in cls._unique_indexes(connection, "节点"):
            raise GraphSchemaError("节点.命令ID必须具有唯一约束")
        expected = {("命令ID", "命令", "ID", "CASCADE")}
        if not expected <= cls._foreign_keys(connection, "节点"):
            raise GraphSchemaError("节点.命令ID缺少级联外键")

    @classmethod
    def _create_or_validate_edge_table(
        cls, connection: sqlite3.Connection, existing_tables: set[str]
    ) -> None:
        if "节点连接" not in existing_tables:
            connection.execute(
                "CREATE TABLE 节点连接 ("
                "源节点ID TEXT NOT NULL PRIMARY KEY, "
                "目标节点ID TEXT NOT NULL UNIQUE, "
                "FOREIGN KEY(源节点ID) REFERENCES 节点(节点ID) ON DELETE CASCADE, "
                "FOREIGN KEY(目标节点ID) REFERENCES 节点(节点ID) ON DELETE CASCADE)"
            )
            return
        if cls._table_columns(connection, "节点连接") != EDGE_COLUMNS:
            raise GraphSchemaError("节点连接表结构不受支持")
        expected_signature = (
            ("源节点ID", "TEXT", 1, 1),
            ("目标节点ID", "TEXT", 1, 0),
        )
        if cls._table_signature(connection, "节点连接") != expected_signature:
            raise GraphSchemaError("节点连接表字段类型或约束不正确")
        if ("目标节点ID",) not in cls._unique_indexes(connection, "节点连接"):
            raise GraphSchemaError("节点连接.目标节点ID必须具有唯一约束")
        expected = {
            ("源节点ID", "节点", "节点ID", "CASCADE"),
            ("目标节点ID", "节点", "节点ID", "CASCADE"),
        }
        if not expected <= cls._foreign_keys(connection, "节点连接"):
            raise GraphSchemaError("节点连接缺少级联外键")

    # ------------------------------------------------------------------
    # Connections and record conversion
    # ------------------------------------------------------------------
    @contextlib.contextmanager
    def _connection(self):
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield connection
        finally:
            connection.close()

    @contextlib.contextmanager
    def _transaction(self):
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
                self._validate_connection(connection, require_order=True)
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _decode_parameters(parameters_json: str) -> dict[str, Any]:
        try:
            parameters = json.loads(parameters_json)
        except (TypeError, json.JSONDecodeError) as error_:
            raise GraphValidationError("参数JSON不是有效 JSON") from error_
        if not isinstance(parameters, dict):
            raise GraphValidationError("参数JSON必须表示对象")
        return parameters

    @staticmethod
    def _encode_parameters(parameters: Any) -> str:
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

    @classmethod
    def _command_from_row(cls, row: Sequence[Any]) -> CommandRecord:
        return CommandRecord(
            id=int(row[0]),
            type_id=str(row[1]),
            parameters=cls._decode_parameters(row[2]),
            repeat_count=int(row[3]),
            error_policy=str(row[4]),
            note=str(row[5]),
            order=int(row[6]),
        )

    @staticmethod
    def _node_from_row(row: Sequence[Any]) -> NodeRecord:
        return NodeRecord(
            node_id=str(row[0]),
            command_id=None if row[1] is None else int(row[1]),
            node_type=str(row[2]),
            x=float(row[3]),
            y=float(row[4]),
        )

    @staticmethod
    def _draft_value(draft: Any, key: str, default: Any = None) -> Any:
        if isinstance(draft, Mapping):
            return draft.get(key, default)
        return getattr(draft, key, default)

    @classmethod
    def _normalize_draft(cls, draft: Any) -> tuple[str, str, int, str, str]:
        if isinstance(draft, Mapping):
            draft = InstructionDraft.from_mapping(draft)
        type_id = cls._draft_value(draft, "type_id")
        parameters = cls._draft_value(draft, "parameters", {})
        repeat_count = cls._draft_value(draft, "repeat_count", 1)
        error_policy = cls._draft_value(
            draft, "error_policy", "提示异常并暂停"
        )
        note = cls._draft_value(draft, "note", "")
        if not isinstance(type_id, str) or not type_id.strip():
            raise ValueError("type_id 必须是非空字符串")
        if isinstance(repeat_count, bool) or not isinstance(repeat_count, int):
            raise ValueError("repeat_count 必须是正整数")
        if repeat_count <= 0:
            raise ValueError("repeat_count 必须是正整数")
        if error_policy is None:
            error_policy = ""
        if note is None:
            note = ""
        if not isinstance(error_policy, str) or not isinstance(note, str):
            raise ValueError("error_policy 和 note 必须是字符串")
        return (
            type_id.strip(),
            cls._encode_parameters(parameters),
            repeat_count,
            error_policy,
            note,
        )

    # ------------------------------------------------------------------
    # Queries and graph validation
    # ------------------------------------------------------------------
    def list_commands(self) -> list[CommandRecord]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT ID, 类型标识, 参数JSON, 重复次数, 异常处理, 备注, 排序 "
                "FROM 命令 ORDER BY 排序"
            ).fetchall()
        return [self._command_from_row(row) for row in rows]

    def get_command(self, command_id: int) -> Optional[CommandRecord]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT ID, 类型标识, 参数JSON, 重复次数, 异常处理, 备注, 排序 "
                "FROM 命令 WHERE ID=?",
                (command_id,),
            ).fetchone()
        return None if row is None else self._command_from_row(row)

    @classmethod
    def _validate_connection(
        cls, connection: sqlite3.Connection, *, require_order: bool
    ) -> list[str]:
        command_rows = connection.execute(
            "SELECT ID, 类型标识, 参数JSON, 重复次数, 异常处理, 备注, 排序 "
            "FROM 命令 ORDER BY 排序"
        ).fetchall()
        commands = [
            _SerializedCommand(
                id=int(row[0]),
                type_id=str(row[1]),
                parameters_json=str(row[2]),
                repeat_count=int(row[3]),
                error_policy=str(row[4]),
                note=str(row[5]),
                order=int(row[6]),
            )
            for row in command_rows
        ]
        nodes = [
            cls._node_from_row(row)
            for row in connection.execute(
                "SELECT 节点ID, 命令ID, 节点类型, X, Y FROM 节点"
            )
        ]
        edges = [
            EdgeRecord(str(row[0]), str(row[1]))
            for row in connection.execute(
                "SELECT 源节点ID, 目标节点ID FROM 节点连接"
            )
        ]
        return cls._validate_records(
            commands, nodes, edges, require_order=require_order
        )

    @classmethod
    def _validate_records(
        cls,
        commands: Sequence[_SerializedCommand],
        nodes: Sequence[NodeRecord],
        edges: Sequence[EdgeRecord],
        *,
        require_order: bool,
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
            cls._decode_parameters(command.parameters_json)
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

        outgoing: dict[str, str] = {}
        incoming: dict[str, str] = {}
        for edge in edges:
            if edge.source not in node_by_id or edge.target not in node_by_id:
                raise GraphValidationError("连线引用了不存在的节点")
            if edge.source in outgoing:
                raise GraphValidationError("节点不能拥有多个输出")
            if edge.target in incoming:
                raise GraphValidationError("节点不能拥有多个输入")
            outgoing[edge.source] = edge.target
            incoming[edge.target] = edge.source
        if START_NODE_ID in incoming or END_NODE_ID in outgoing:
            raise GraphValidationError("开始节点不能有输入，结束节点不能有输出")
        if outgoing.get(START_NODE_ID) is None or incoming.get(END_NODE_ID) is None:
            raise GraphValidationError("开始到结束之间必须存在完整连线")
        for node in instruction_nodes:
            if node.node_id not in incoming or node.node_id not in outgoing:
                raise GraphValidationError("每个指令节点必须各有一个输入和输出")
        if len(edges) != len(nodes) - 1:
            raise GraphValidationError("单链的连线数量不正确")

        chain: list[str] = [START_NODE_ID]
        visited = {START_NODE_ID}
        current = START_NODE_ID
        while current != END_NODE_ID:
            target = outgoing.get(current)
            if target is None:
                raise GraphValidationError("节点链在到达结束节点前中断")
            if target in visited:
                raise GraphValidationError("节点链不能包含环路")
            chain.append(target)
            visited.add(target)
            current = target
        if visited != set(node_by_id):
            raise GraphValidationError("存在未接入主链的节点")

        chain_command_ids = [
            node_by_id[node_id].command_id
            for node_id in chain[1:-1]
        ]
        if require_order:
            ordered_command_ids = [
                command.id for command in sorted(commands, key=lambda item: item.order)
            ]
            if chain_command_ids != ordered_command_ids:
                raise GraphValidationError("命令排序与节点连线顺序不一致")
        return chain

    def validate_graph(self) -> GraphSnapshot:
        with self._connection() as connection:
            self._validate_connection(connection, require_order=True)
        return self.snapshot()

    def _resolve_spec(self, type_id: str) -> Any:
        if self._instruction_resolver is not None:
            return self._instruction_resolver(type_id)
        try:
            registry = importlib.import_module("instructions.registry")
        except ImportError:
            return None
        for function_name in (
            "get_instruction_spec",
            "get_spec",
            "resolve_instruction",
        ):
            function = getattr(registry, function_name, None)
            if callable(function):
                try:
                    return function(type_id)
                except (KeyError, LookupError):
                    return None
        for mapping_name in (
            "INSTRUCTION_SPECS",
            "INSTRUCTION_REGISTRY",
            "REGISTRY",
        ):
            mapping = getattr(registry, mapping_name, None)
            if isinstance(mapping, Mapping):
                return mapping.get(type_id)
        return None

    def _is_known_type(self, type_id: str) -> bool:
        if self._valid_type_ids is not None:
            return type_id in self._valid_type_ids
        try:
            registry = importlib.import_module("instructions.registry")
        except ImportError:
            return True
        spec = self._resolve_spec(type_id)
        if spec is not None:
            return True
        # A registry module exists, therefore an unresolved type is unknown.
        return False

    def _display_name(self, type_id: str) -> str:
        spec = self._resolve_spec(type_id)
        if spec is None:
            return type_id
        if isinstance(spec, Mapping):
            return str(spec.get("display_name") or type_id)
        return str(getattr(spec, "display_name", type_id))

    def snapshot(self) -> GraphSnapshot:
        with self._connection() as connection:
            command_rows = connection.execute(
                "SELECT ID, 类型标识, 参数JSON, 重复次数, 异常处理, 备注, 排序 "
                "FROM 命令 ORDER BY 排序"
            ).fetchall()
            commands = tuple(self._command_from_row(row) for row in command_rows)
            command_by_id = {command.id: command for command in commands}
            node_rows = connection.execute(
                "SELECT 节点ID, 命令ID, 节点类型, X, Y FROM 节点 "
                "ORDER BY CASE 节点类型 WHEN 'start' THEN -1 WHEN 'end' THEN 999999 "
                "ELSE COALESCE((SELECT 排序 FROM 命令 WHERE ID=节点.命令ID), 999998) END"
            ).fetchall()
            edges = tuple(
                EdgeRecord(str(row[0]), str(row[1]))
                for row in connection.execute(
                    "SELECT 源节点ID, 目标节点ID FROM 节点连接 ORDER BY rowid"
                )
            )
        node_views: list[NodeView] = []
        for row in node_rows:
            node = self._node_from_row(row)
            command = (
                command_by_id.get(node.command_id)
                if node.command_id is not None
                else None
            )
            if node.node_type == START_NODE_TYPE:
                type_id, display_name = None, "开始"
            elif node.node_type == END_NODE_TYPE:
                type_id, display_name = None, "结束"
            else:
                type_id = command.type_id if command is not None else None
                display_name = self._display_name(type_id or "")
            node_views.append(
                NodeView(
                    node_id=node.node_id,
                    command_id=node.command_id,
                    node_type=node.node_type,
                    type_id=type_id,
                    display_name=display_name,
                    x=node.x,
                    y=node.y,
                )
            )
        return GraphSnapshot(commands, tuple(node_views), edges)

    def delete_node_connections(self, node_id: str, mode: str = "all") -> int:
        """Delete incoming/outgoing draft edges without deleting the node."""
        node_id = str(node_id)
        if mode not in {"all", "incoming", "outgoing"}:
            raise ValueError(f"不支持的连线删除方式：{mode}")
        with self._transaction() as connection:
            if connection.execute(
                "SELECT 1 FROM 节点 WHERE 节点ID=?", (node_id,)
            ).fetchone() is None:
                raise KeyError(f"节点不存在：{node_id}")
            clauses, parameters = [], []
            if mode in {"all", "incoming"}:
                clauses.append("目标节点ID=?")
                parameters.append(node_id)
            if mode in {"all", "outgoing"}:
                clauses.append("源节点ID=?")
                parameters.append(node_id)
            cursor = connection.execute(
                f"DELETE FROM 节点连接 WHERE {' OR '.join(clauses)}", parameters
            )
            return int(cursor.rowcount)

    def connect_nodes(self, source_id: str, target_id: str) -> None:
        """Connect two draft nodes, replacing conflicting single-flow edges."""
        source_id, target_id = str(source_id), str(target_id)
        if source_id == target_id:
            raise GraphValidationError("节点不能连接到自身")
        with self._transaction() as connection:
            rows = connection.execute(
                "SELECT 节点ID, 节点类型 FROM 节点 WHERE 节点ID IN (?, ?)",
                (source_id, target_id),
            ).fetchall()
            node_types = {str(row[0]): str(row[1]) for row in rows}
            if set(node_types) != {source_id, target_id}:
                raise KeyError("连接的节点不存在")
            if node_types[source_id] == END_NODE_TYPE:
                raise GraphValidationError("结束节点不能拉出连接线")
            if node_types[target_id] == START_NODE_TYPE:
                raise GraphValidationError("开始节点不能接收连接线")
            connection.execute(
                "DELETE FROM 节点连接 WHERE 源节点ID=? OR 目标节点ID=?",
                (source_id, target_id),
            )
            connection.execute(
                "INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
                (source_id, target_id),
            )
            # Reject cycles while allowing a temporarily incomplete draft.
            outgoing = dict(connection.execute(
                "SELECT 源节点ID, 目标节点ID FROM 节点连接"
            ).fetchall())
            seen, current = set(), source_id
            while current in outgoing:
                if current in seen:
                    raise GraphValidationError("流程连接不能形成环")
                seen.add(current)
                current = str(outgoing[current])

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------
    @staticmethod
    def _set_command_orders(
        connection: sqlite3.Connection, command_ids: Sequence[int]
    ) -> None:
        if not command_ids:
            return
        existing_ids = {
            row[0] for row in connection.execute("SELECT ID FROM 命令")
        }
        if set(command_ids) != existing_ids or len(command_ids) != len(existing_ids):
            raise GraphValidationError("重排必须包含全部命令且每条命令只出现一次")
        max_order = connection.execute(
            "SELECT COALESCE(MAX(排序), -1) FROM 命令"
        ).fetchone()[0]
        offset = int(max_order) + len(command_ids) + 1
        connection.execute("UPDATE 命令 SET 排序=排序+?", (offset,))
        connection.executemany(
            "UPDATE 命令 SET 排序=? WHERE ID=?",
            [(order, command_id) for order, command_id in enumerate(command_ids)],
        )

    @classmethod
    def _sync_orders_from_chain(cls, connection: sqlite3.Connection) -> None:
        chain = cls._validate_connection(connection, require_order=False)
        command_ids = [
            row[0]
            for node_id in chain[1:-1]
            for row in connection.execute(
                "SELECT 命令ID FROM 节点 WHERE 节点ID=?", (node_id,)
            )
        ]
        cls._set_command_orders(connection, command_ids)

    @staticmethod
    def _edge_tuple(edge: Any) -> tuple[str, str]:
        if isinstance(edge, EdgeRecord):
            return edge.source, edge.target
        if isinstance(edge, Mapping):
            return str(edge["source"]), str(edge["target"])
        if isinstance(edge, Sequence) and not isinstance(edge, (str, bytes)):
            if len(edge) == 2:
                return str(edge[0]), str(edge[1])
        raise ValueError("split_edge 必须包含 source 和 target")

    def add_command(
        self,
        draft: Any,
        *,
        x: Optional[float] = None,
        y: Optional[float] = None,
        split_edge: Any = None,
        before_node_id: Optional[str] = None,
    ) -> CommandRecord:
        type_id, parameters_json, repeat_count, error_policy, note = (
            self._normalize_draft(draft)
        )
        if not self._is_known_type(type_id):
            raise ValueError(f"未知指令类型：{type_id}")
        if split_edge is not None and before_node_id is not None:
            raise ValueError("split_edge 与 before_node_id 不能同时指定")
        with self._transaction() as connection:
            if split_edge is not None:
                source, target = self._edge_tuple(split_edge)
            else:
                target = before_node_id or END_NODE_ID
                incoming = connection.execute(
                    "SELECT 源节点ID FROM 节点连接 WHERE 目标节点ID=?", (target,)
                ).fetchone()
                if incoming is None:
                    raise GraphValidationError("目标节点没有可拆分的输入连线")
                source = str(incoming[0])
            if connection.execute(
                "SELECT 1 FROM 节点连接 WHERE 源节点ID=? AND 目标节点ID=?",
                (source, target),
            ).fetchone() is None:
                raise GraphValidationError("指定连线不存在，无法插入节点")
            if source == END_NODE_ID or target == START_NODE_ID:
                raise GraphValidationError("不能在无效方向的连线上插入节点")

            source_position = connection.execute(
                "SELECT X, Y FROM 节点 WHERE 节点ID=?", (source,)
            ).fetchone()
            target_position = connection.execute(
                "SELECT X, Y FROM 节点 WHERE 节点ID=?", (target,)
            ).fetchone()
            node_x = (
                float(x)
                if x is not None
                else (float(source_position[0]) + float(target_position[0])) / 2
            )
            node_y = (
                float(y)
                if y is not None
                else (float(source_position[1]) + float(target_position[1])) / 2
            )
            if not math.isfinite(node_x) or not math.isfinite(node_y):
                raise ValueError("节点坐标必须是有限数值")

            temporary_order = connection.execute(
                "SELECT COALESCE(MAX(排序), -1) + 1 FROM 命令"
            ).fetchone()[0]
            cursor = connection.execute(
                "INSERT INTO 命令(类型标识, 参数JSON, 重复次数, 异常处理, 备注, 排序) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    type_id,
                    parameters_json,
                    repeat_count,
                    error_policy,
                    note,
                    temporary_order,
                ),
            )
            command_id = int(cursor.lastrowid)
            node_id = uuid.uuid4().hex
            connection.execute(
                "INSERT INTO 节点(节点ID, 命令ID, 节点类型, X, Y) "
                "VALUES (?, ?, 'instruction', ?, ?)",
                (node_id, command_id, node_x, node_y),
            )
            connection.execute(
                "DELETE FROM 节点连接 WHERE 源节点ID=? AND 目标节点ID=?",
                (source, target),
            )
            connection.executemany(
                "INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
                [(source, node_id), (node_id, target)],
            )
            self._sync_orders_from_chain(connection)
        record = self.get_command(command_id)
        if record is None:  # pragma: no cover - transaction invariant
            raise GraphRepositoryError("新增命令后无法读取记录")
        return record

    def update_command(self, command_id: int, draft: Any) -> CommandRecord:
        type_id, parameters_json, repeat_count, error_policy, note = (
            self._normalize_draft(draft)
        )
        if not self._is_known_type(type_id):
            raise ValueError(f"未知指令类型：{type_id}")
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE 命令 SET 类型标识=?, 参数JSON=?, 重复次数=?, "
                "异常处理=?, 备注=? WHERE ID=?",
                (
                    type_id,
                    parameters_json,
                    repeat_count,
                    error_policy,
                    note,
                    command_id,
                ),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"命令不存在：{command_id}")
        record = self.get_command(command_id)
        if record is None:  # pragma: no cover - transaction invariant
            raise GraphRepositoryError("修改命令后无法读取记录")
        return record

    def duplicate_command(self, command_id: int) -> CommandRecord:
        command = self.get_command(command_id)
        if command is None:
            raise KeyError(f"命令不存在：{command_id}")
        with self._connection() as connection:
            node = connection.execute(
                "SELECT 节点ID, X, Y FROM 节点 WHERE 命令ID=?", (command_id,)
            ).fetchone()
            if node is None:
                raise GraphValidationError("命令缺少对应节点")
            successor = connection.execute(
                "SELECT 目标节点ID FROM 节点连接 WHERE 源节点ID=?", (node[0],)
            ).fetchone()
            if successor is None:
                raise GraphValidationError("命令节点缺少输出连线")
        draft = {
            "type_id": command.type_id,
            "parameters": command.parameters,
            "repeat_count": command.repeat_count,
            "error_policy": command.error_policy,
            "note": command.note,
        }
        return self.add_command(
            draft,
            x=float(node[1]) + 30.0,
            y=float(node[2]) + 30.0,
            split_edge=(str(node[0]), str(successor[0])),
        )

    def delete_commands(self, command_ids: Iterable[int]) -> int:
        unique_ids = tuple(dict.fromkeys(int(item) for item in command_ids))
        if not unique_ids:
            return 0
        with self._transaction() as connection:
            existing = {
                row[0]
                for row in connection.execute(
                    "SELECT ID FROM 命令 WHERE ID IN ({})".format(
                        ",".join("?" for _ in unique_ids)
                    ),
                    unique_ids,
                )
            }
            if not existing:
                return 0
            chain = self._validate_connection(connection, require_order=True)
            remaining_nodes = [
                node_id
                for node_id in chain
                if (
                    connection.execute(
                        "SELECT 命令ID FROM 节点 WHERE 节点ID=?", (node_id,)
                    ).fetchone()[0]
                    not in existing
                )
            ]
            connection.execute("DELETE FROM 节点连接")
            connection.execute(
                "DELETE FROM 命令 WHERE ID IN ({})".format(
                    ",".join("?" for _ in existing)
                ),
                tuple(existing),
            )
            connection.executemany(
                "INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
                zip(remaining_nodes, remaining_nodes[1:]),
            )
            self._sync_orders_from_chain(connection)
            deleted_count = len(existing)
        return deleted_count

    def clear(self) -> None:
        with self._transaction() as connection:
            connection.execute("DELETE FROM 节点连接")
            connection.execute("DELETE FROM 命令")
            connection.execute(
                "DELETE FROM 节点 WHERE 节点类型='instruction'"
            )
            connection.execute(
                "INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
                (START_NODE_ID, END_NODE_ID),
            )

    def save_node_position(self, node_id: str, x: float, y: float) -> None:
        self.save_node_positions({node_id: (x, y)})

    def save_node_positions(
        self, positions: Mapping[str, Sequence[float]]
    ) -> None:
        normalized = self._normalize_node_positions(positions)
        if not normalized:
            return
        with self._transaction() as connection:
            self._save_node_positions(connection, normalized)

    @staticmethod
    def _normalize_node_positions(
        positions: Mapping[str, Sequence[float]],
    ) -> list[tuple[float, float, str]]:
        normalized: list[tuple[float, float, str]] = []
        for node_id, position in positions.items():
            if len(position) != 2:
                raise ValueError("节点位置必须包含 X 和 Y")
            x, y = float(position[0]), float(position[1])
            if not math.isfinite(x) or not math.isfinite(y):
                raise ValueError("节点坐标必须是有限数值")
            normalized.append((x, y, str(node_id)))
        return normalized

    @staticmethod
    def _save_node_positions(
        connection: sqlite3.Connection,
        normalized: Sequence[tuple[float, float, str]],
    ) -> None:
        existing = {
            row[0]
            for row in connection.execute(
                "SELECT 节点ID FROM 节点 WHERE 节点ID IN ({})".format(
                    ",".join("?" for _ in normalized)
                ),
                tuple(item[2] for item in normalized),
            )
        }
        requested = {item[2] for item in normalized}
        missing = requested - existing
        if missing:
            raise KeyError(f"节点不存在：{', '.join(sorted(missing))}")
        connection.executemany(
            "UPDATE 节点 SET X=?, Y=? WHERE 节点ID=?", normalized
        )

    @staticmethod
    def _reorder_chain(
        connection: sqlite3.Connection, normalized_ids: Sequence[int]
    ) -> None:
        rows = connection.execute(
            "SELECT 命令ID, 节点ID FROM 节点 WHERE 节点类型='instruction'"
        ).fetchall()
        node_by_command = {int(row[0]): str(row[1]) for row in rows}
        if set(normalized_ids) != set(node_by_command):
            raise GraphValidationError("重排必须包含全部命令且每条命令只出现一次")
        chain = [START_NODE_ID]
        chain.extend(node_by_command[command_id] for command_id in normalized_ids)
        chain.append(END_NODE_ID)
        connection.execute("DELETE FROM 节点连接")
        connection.executemany(
            "INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
            zip(chain, chain[1:]),
        )
        GraphRepository._set_command_orders(connection, normalized_ids)

    def reorder_chain(self, command_ids: Sequence[int]) -> None:
        normalized_ids = [int(item) for item in command_ids]
        if len(normalized_ids) != len(set(normalized_ids)):
            raise GraphValidationError("重排列表不能包含重复命令")
        with self._transaction() as connection:
            self._reorder_chain(connection, normalized_ids)

    def reorder_chain_and_save_positions(
        self,
        command_ids: Sequence[int],
        positions: Mapping[str, Sequence[float]],
    ) -> None:
        """在同一事务中持久化单链拓扑、排序和节点位置。"""
        normalized_ids = [int(item) for item in command_ids]
        if len(normalized_ids) != len(set(normalized_ids)):
            raise GraphValidationError("重排列表不能包含重复命令")
        normalized_positions = self._normalize_node_positions(positions)
        with self._transaction() as connection:
            self._reorder_chain(connection, normalized_ids)
            if normalized_positions:
                self._save_node_positions(connection, normalized_positions)

    # ------------------------------------------------------------------
    # Workbook protocol
    # ------------------------------------------------------------------
    @staticmethod
    def _replace_sheet(workbook: Any, title: str, headers: Sequence[str]):
        if title in workbook.sheetnames:
            del workbook[title]
        sheet = workbook.create_sheet(title)
        sheet.append(list(headers))
        return sheet

    def export_to_workbook(self, workbook: Any, database_operation: Any = None) -> None:
        """Replace workbook contents with the exact four-sheet protocol."""
        for worksheet in list(workbook.worksheets):
            workbook.remove(worksheet)
        command_sheet = workbook.create_sheet("命令")
        command_sheet.append(COMMAND_SHEET_HEADERS)
        node_sheet = workbook.create_sheet("节点")
        node_sheet.append(NODE_SHEET_HEADERS)
        edge_sheet = workbook.create_sheet("连线")
        edge_sheet.append(EDGE_SHEET_HEADERS)
        with self._connection() as connection:
            command_sheet_rows = connection.execute(
                "SELECT ID, 类型标识, 参数JSON, 重复次数, 异常处理, 备注, 排序 "
                "FROM 命令 ORDER BY 排序"
            ).fetchall()
            node_sheet_rows = connection.execute(
                "SELECT 节点ID, 命令ID, 节点类型, X, Y FROM 节点 "
                "ORDER BY CASE 节点类型 WHEN 'start' THEN 0 "
                "WHEN 'instruction' THEN 1 ELSE 2 END, rowid"
            ).fetchall()
            edge_sheet_rows = connection.execute(
                "SELECT 源节点ID, 目标节点ID FROM 节点连接 ORDER BY rowid"
            ).fetchall()
        for row in command_sheet_rows:
            command_sheet.append(row)
        for row in node_sheet_rows:
            node_sheet.append(row)
        for row in edge_sheet_rows:
            edge_sheet.append(row)

        if database_operation is None:
            from 数据库操作 import DatabaseOperation

            database_operation = DatabaseOperation(self.db_path)
        database_operation.export_settings_to_excel(workbook)
        if tuple(workbook.sheetnames) != WORKBOOK_SHEETS:
            raise GraphRepositoryError("导出的工作表结构不完整")

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
        edge_rows = self._sheet_rows(workbook, "连线", EDGE_SHEET_HEADERS)

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
        for source, target in edge_rows:
            if (
                not isinstance(source, str)
                or not source.strip()
                or not isinstance(target, str)
                or not target.strip()
            ):
                raise WorkbookValidationError("连线的源节点和目标节点不能为空")
            edges.append(EdgeRecord(source.strip(), target.strip()))
        try:
            self._validate_records(commands, nodes, edges, require_order=True)
        except GraphValidationError as error_:
            raise WorkbookValidationError(str(error_)) from error_

        from 数据库操作 import DatabaseOperation

        settings = DatabaseOperation._read_settings_from_excel(workbook)
        if settings is None:
            raise WorkbookValidationError("“设置”工作表格式或内容不正确")
        return commands, nodes, edges, settings

    def validate_workbook(self, workbook: Any) -> None:
        """Raise :class:`WorkbookValidationError` unless the workbook is valid."""
        self._parse_workbook(workbook)

    def import_from_workbook(self, workbook: Any) -> None:
        """Validate everything first, then atomically replace graph and settings."""
        commands, nodes, edges, settings = self._parse_workbook(workbook)
        from 数据库操作 import DatabaseOperation

        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute("DELETE FROM 节点连接")
                connection.execute("DELETE FROM 节点")
                connection.execute("DELETE FROM 命令")
                connection.executemany(
                    "INSERT INTO 命令(ID, 类型标识, 参数JSON, 重复次数, "
                    "异常处理, 备注, 排序) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        (
                            command.id,
                            command.type_id,
                            command.parameters_json,
                            command.repeat_count,
                            command.error_policy,
                            command.note,
                            command.order,
                        )
                        for command in commands
                    ],
                )
                connection.executemany(
                    "INSERT INTO 节点(节点ID, 命令ID, 节点类型, X, Y) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [
                        (
                            node.node_id,
                            node.command_id,
                            node.node_type,
                            node.x,
                            node.y,
                        )
                        for node in nodes
                    ],
                )
                connection.executemany(
                    "INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
                    [(edge.source, edge.target) for edge in edges],
                )
                DatabaseOperation._apply_parsed_settings(connection, settings)
                self._validate_connection(connection, require_order=True)
                connection.commit()
            except Exception:
                connection.rollback()
                raise


__all__ = [
    "COMMAND_COLUMNS",
    "COMMAND_SHEET_HEADERS",
    "EDGE_COLUMNS",
    "EDGE_SHEET_HEADERS",
    "END_NODE_ID",
    "EdgeRecord",
    "GraphRepository",
    "GraphRepositoryError",
    "GraphSchemaError",
    "GraphSnapshot",
    "GraphValidationError",
    "NODE_COLUMNS",
    "NODE_SHEET_HEADERS",
    "NodeRecord",
    "NodeView",
    "SETTINGS_SHEET_HEADERS",
    "START_NODE_ID",
    "WORKBOOK_SHEETS",
    "WorkbookValidationError",
    "CommandRecord",
]
