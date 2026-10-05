"""Branch-capable command graph persistence and workbook protocol.

The node graph is a complete directed acyclic flow::

    start -> instruction -> branch ... -> merge -> end

The executor continues to consume :class:`CommandRecord` objects ordered by
``order``.  Connections are the source of truth whenever the graph changes;
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


class GraphRepository:
    """Transactional persistence for a directed acyclic command graph.

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
        connection.execute(
            "CREATE TABLE IF NOT EXISTS flow_edge_metadata ("
            "source_id TEXT NOT NULL, target_id TEXT NOT NULL, kind INTEGER NOT NULL DEFAULT 0, "
            "PRIMARY KEY(source_id, target_id))"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS 节点布局 ("
            "节点ID TEXT PRIMARY KEY, 宽度 REAL NOT NULL, 高度 REAL NOT NULL, "
            "FOREIGN KEY(节点ID) REFERENCES 节点(节点ID) ON DELETE CASCADE)"
        )

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
        elif node_count == 0:
            raise GraphSchemaError("命令与节点图必须同时存在，不能初始化不完整的图结构")

        cls._validate_draft_connection(connection)
        command_orders = connection.execute(
            "SELECT ID, 排序 FROM 命令 ORDER BY 排序, ID"
        ).fetchall()
        if [row[1] for row in command_orders] != list(range(len(command_orders))):
            cls._set_command_orders(connection, [row[0] for row in command_orders])

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
                "源节点ID TEXT NOT NULL, "
                "目标节点ID TEXT NOT NULL, "
                "PRIMARY KEY(源节点ID, 目标节点ID), "
                "FOREIGN KEY(源节点ID) REFERENCES 节点(节点ID) ON DELETE CASCADE, "
                "FOREIGN KEY(目标节点ID) REFERENCES 节点(节点ID) ON DELETE CASCADE)"
            )
            return
        if cls._table_columns(connection, "节点连接") != EDGE_COLUMNS:
            raise GraphSchemaError("节点连接表结构不受支持")
        expected_signature = (
            ("源节点ID", "TEXT", 1, 1),
            ("目标节点ID", "TEXT", 1, 2),
        )
        old_signature = (
            ("源节点ID", "TEXT", 1, 1),
            ("目标节点ID", "TEXT", 1, 0),
        )
        signature = cls._table_signature(connection, "节点连接")
        if signature == old_signature and ("目标节点ID",) in cls._unique_indexes(
            connection, "节点连接"
        ):
            connection.execute("ALTER TABLE 节点连接 RENAME TO 节点连接_单链旧表")
            connection.execute(
                "CREATE TABLE 节点连接 ("
                "源节点ID TEXT NOT NULL, 目标节点ID TEXT NOT NULL, "
                "PRIMARY KEY(源节点ID, 目标节点ID), "
                "FOREIGN KEY(源节点ID) REFERENCES 节点(节点ID) ON DELETE CASCADE, "
                "FOREIGN KEY(目标节点ID) REFERENCES 节点(节点ID) ON DELETE CASCADE)"
            )
            connection.execute(
                "INSERT INTO 节点连接(源节点ID, 目标节点ID) "
                "SELECT 源节点ID, 目标节点ID FROM 节点连接_单链旧表"
            )
            connection.execute("DROP TABLE 节点连接_单链旧表")
        elif signature != expected_signature:
            raise GraphSchemaError("节点连接表字段类型或约束不正确")
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
    def _transaction(self, *, validate_graph: bool = True):
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
                if validate_graph:
                    self._validate_connection(connection, require_order=True)
                else:
                    self._validate_draft_connection(connection)
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
    def _edge_records(cls, connection: sqlite3.Connection) -> list[EdgeRecord]:
        """Load links with stable branch roles, migrating older databases lazily."""
        rows = connection.execute(
            "SELECT 源节点ID, 目标节点ID FROM 节点连接 ORDER BY rowid"
        ).fetchall()
        metadata = {
            (str(row[0]), str(row[1])): int(row[2])
            for row in connection.execute(
                "SELECT source_id, target_id, kind FROM flow_edge_metadata"
            )
        }
        valid_pairs = {(str(row[0]), str(row[1])) for row in rows}
        for stale_source, stale_target in set(metadata) - valid_pairs:
            connection.execute(
                "DELETE FROM flow_edge_metadata WHERE source_id=? AND target_id=?",
                (stale_source, stale_target),
            )
        source_types = {
            str(row[0]): str(row[1])
            for row in connection.execute(
                "SELECT 节点.节点ID, 命令.类型标识 FROM 节点 "
                "JOIN 命令 ON 节点.命令ID=命令.ID"
            )
        }
        seen: dict[str, int] = {}
        records: list[EdgeRecord] = []
        for source, target in ((str(row[0]), str(row[1])) for row in rows):
            index = seen.get(source, 0)
            seen[source] = index + 1
            kind = metadata.get((source, target))
            if kind is None:
                source_type = source_types.get(source, "")
                if source_type == "条件判断":
                    kind = (1, 2)[min(index, 1)]
                elif source_type in {"循环", "条件循环"}:
                    kind = (3, 4)[min(index, 1)]
                else:
                    kind = 0
                connection.execute(
                    "INSERT OR IGNORE INTO flow_edge_metadata(source_id, target_id, kind) "
                    "VALUES (?, ?, ?)",
                    (source, target, kind),
                )
            records.append(EdgeRecord(source, target, kind))
        return records

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
        edges = cls._edge_records(connection)
        return cls._validate_records(
            commands, nodes, edges, require_order=require_order
        )

    @classmethod
    def _validate_draft_connection(cls, connection: sqlite3.Connection, *, validate_cycles=False) -> list[str]:
        """Validate stored records and DAG safety while allowing missing edges."""
        command_rows = connection.execute(
            "SELECT ID, 类型标识, 参数JSON, 重复次数, 异常处理, 备注, 排序 "
            "FROM 命令 ORDER BY 排序"
        ).fetchall()
        commands = [
            _SerializedCommand(
                int(row[0]), str(row[1]), str(row[2]), int(row[3]),
                str(row[4]), str(row[5]), int(row[6])
            )
            for row in command_rows
        ]
        nodes = [
            cls._node_from_row(row)
            for row in connection.execute(
                "SELECT 节点ID, 命令ID, 节点类型, X, Y FROM 节点"
            )
        ]
        edges = cls._edge_records(connection)
        return cls._validate_records(
            commands, nodes, edges, require_order=False, allow_incomplete=True,
            validate_cycles=validate_cycles,
        )

    @classmethod
    def _validate_records(
        cls,
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
            if command.type_id in {"条件判断", "循环", "条件循环"}:
                branch_count = len(outgoing[node.node_id])
                if branch_count > 2:
                    raise GraphValidationError("条件或循环节点最多只能连接两条输出")
                if not allow_incomplete and branch_count != 2:
                    raise GraphValidationError("条件或循环节点必须连接两条输出")
                expected_kinds = {1, 2} if command.type_id == "条件判断" else {3, 4}
                actual_kinds = {
                    int(edge.kind) for edge in edges if edge.source == node.node_id
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

    def validate_graph(self) -> GraphSnapshot:
        with self._connection() as connection:
            self._validate_connection(connection, require_order=True)
        return self.snapshot()

    def execution_snapshot(self) -> GraphSnapshot:
        """Validate structure without requiring a fully connected, sorted graph."""
        with self._connection() as connection:
            self._validate_draft_connection(connection, validate_cycles=True)
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
            edges = tuple(self._edge_records(connection))
            layout_by_node = {
                str(row[0]): (float(row[1]), float(row[2]))
                for row in connection.execute("SELECT 节点ID, 宽度, 高度 FROM 节点布局")
            }
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
                    repeat_count=command.repeat_count if command is not None else 1,
                    parameters=dict(command.parameters) if command is not None else None,
                    note=command.note if command is not None else "",
                    width=layout_by_node.get(node.node_id, (None, None))[0],
                    height=layout_by_node.get(node.node_id, (None, None))[1],
                )
            )
        return GraphSnapshot(commands, tuple(node_views), edges)

    def delete_node_connections(self, node_id: str, mode: str = "all") -> int:
        """Delete incoming/outgoing draft edges without deleting the node."""
        node_id = str(node_id)
        if mode not in {"all", "incoming", "outgoing"}:
            raise ValueError(f"不支持的连线删除方式：{mode}")
        with self._transaction(validate_graph=False) as connection:
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
            if mode == "all":
                connection.execute(
                    "DELETE FROM flow_edge_metadata WHERE source_id=? OR target_id=?",
                    (node_id, node_id),
                )
            elif mode == "incoming":
                connection.execute(
                    "DELETE FROM flow_edge_metadata WHERE target_id=?", (node_id,)
                )
            else:
                connection.execute(
                    "DELETE FROM flow_edge_metadata WHERE source_id=?", (node_id,)
                )
            return int(cursor.rowcount)

    def connect_nodes(self, source_id: str, target_id: str, kind: int | None = None) -> bool:
        """Add one DAG edge and finalize command order when the graph is complete."""
        source_id, target_id = str(source_id), str(target_id)
        if source_id == target_id:
            raise GraphValidationError("节点不能连接到自身")
        complete = False
        with self._transaction(validate_graph=False) as connection:
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
            source_type = connection.execute(
                "SELECT 命令.类型标识 FROM 节点 JOIN 命令 ON 节点.命令ID=命令.ID "
                "WHERE 节点.节点ID=?", (source_id,)
            ).fetchone()
            source_type_id = str(source_type[0]) if source_type else ""
            if source_type_id in {"条件判断", "循环", "条件循环"}:
                branch_count = int(connection.execute(
                    "SELECT COUNT(*) FROM 节点连接 WHERE 源节点ID=?", (source_id,)
                ).fetchone()[0])
                existing_edge = connection.execute(
                    "SELECT 1 FROM 节点连接 WHERE 源节点ID=? AND 目标节点ID=?",
                    (source_id, target_id),
                ).fetchone()
                if branch_count >= 2 and existing_edge is None:
                    raise GraphValidationError("条件或循环节点最多只能连接两条输出")
            existing_edge = connection.execute(
                "SELECT 1 FROM 节点连接 WHERE 源节点ID=? AND 目标节点ID=?",
                (source_id, target_id),
            ).fetchone()
            connection.execute(
                "INSERT OR IGNORE INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
                (source_id, target_id),
            )
            if existing_edge is None or kind is not None:
                if kind is None:
                    used = {
                        int(row[0]) for row in connection.execute(
                            "SELECT kind FROM flow_edge_metadata WHERE source_id=?",
                            (source_id,),
                        )
                    }
                    candidates = (
                        (1, 2) if source_type_id == "条件判断"
                        else (3, 4) if source_type_id in {"循环", "条件循环"}
                        else (0,)
                    )
                    kind = next((item for item in candidates if item not in used), candidates[-1])
                connection.execute(
                    "INSERT OR REPLACE INTO flow_edge_metadata(source_id, target_id, kind) "
                    "VALUES (?, ?, ?)",
                    (source_id, target_id, int(kind)),
                )
            self._validate_draft_connection(connection)
            try:
                ordered_nodes = self._validate_connection(
                    connection, require_order=False
                )
            except GraphValidationError:
                pass
            else:
                node_commands = dict(connection.execute(
                    "SELECT 节点ID, 命令ID FROM 节点 "
                    "WHERE 节点类型='instruction'"
                ).fetchall())
                self._set_command_orders(
                    connection,
                    [int(node_commands[node_id]) for node_id in ordered_nodes
                     if node_id in node_commands],
                )
                complete = True
        return complete

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

    def append_recording(self, drafts: Sequence[InstructionDraft], *, connect=True) -> list[int]:
        """Append one recording atomically without changing existing links."""
        normalized = [self._normalize_draft(draft) for draft in drafts]
        for type_id, *_ in normalized:
            if not self._is_known_type(type_id):
                raise ValueError(f"未知指令类型：{type_id}")
        if not normalized:
            return []
        ids, nodes = [], []
        with self._transaction(validate_graph=False) as connection:
            count = connection.execute("SELECT COUNT(*) FROM 命令").fetchone()[0]
            order = connection.execute("SELECT COALESCE(MAX(排序), -1)+1 FROM 命令").fetchone()[0]
            base_y = float(connection.execute("SELECT COALESCE(MAX(Y), 0) FROM 节点").fetchone()[0]) + 180
            for index, record in enumerate(normalized):
                type_id, parameters, repeat, policy, note = record
                cursor = connection.execute(
                    "INSERT INTO 命令(类型标识, 参数JSON, 重复次数, 异常处理, 备注, 排序) VALUES (?, ?, ?, ?, ?, ?)",
                    (type_id, parameters, repeat, policy, note, order + index))
                command_id, node_id = int(cursor.lastrowid), uuid.uuid4().hex
                row, column = divmod(index, 6)
                connection.execute(
                    "INSERT INTO 节点(节点ID, 命令ID, 节点类型, X, Y) VALUES (?, ?, 'instruction', ?, ?)",
                    (node_id, command_id, 160 + column * 280, base_y + row * 160))
                ids.append(command_id)
                nodes.append(node_id)
            if count == 0:
                connection.execute("DELETE FROM 节点连接 WHERE 源节点ID=? AND 目标节点ID=?", (START_NODE_ID, END_NODE_ID))
            if connect:
                connection.executemany("INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)", zip(nodes, nodes[1:]))
                # A new empty task is a complete start-to-end recording.
                if count == 0:
                    connection.executemany("INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
                                           [(START_NODE_ID, nodes[0]), (nodes[-1], END_NODE_ID)])
        return ids

    def add_command(
        self,
        draft: Any,
        *,
        x: Optional[float] = None,
        y: Optional[float] = None,
        split_edge: Any = None,
        before_node_id: Optional[str] = None,
        unconnected: bool = False,
    ) -> CommandRecord:
        type_id, parameters_json, repeat_count, error_policy, note = (
            self._normalize_draft(draft)
        )
        if not self._is_known_type(type_id):
            raise ValueError(f"未知指令类型：{type_id}")
        if split_edge is not None and before_node_id is not None:
            raise ValueError("split_edge 与 before_node_id 不能同时指定")
        with self._transaction(validate_graph=not unconnected) as connection:
            sequence = int(connection.execute("SELECT COUNT(*) FROM 命令").fetchone()[0])
            source = target = None
            if not unconnected:
                if split_edge is not None:
                    source, target = self._edge_tuple(split_edge)
                else:
                    target = before_node_id or END_NODE_ID
                    incoming = connection.execute(
                        "SELECT 源节点ID FROM 节点连接 WHERE 目标节点ID=? "
                        "ORDER BY rowid LIMIT 1", (target,)
                    ).fetchone()
                    if incoming is None:
                        raise GraphValidationError("目标节点没有可拆分的输入连线")
                    source = str(incoming[0])
                if connection.execute(
                    "SELECT 1 FROM 节点连接 WHERE 源节点ID=? AND 目标节点ID=?",
                    (source, target),
                ).fetchone() is None:
                    raise GraphValidationError("指定连线不存在，无法插入节点")
                source_position = connection.execute(
                    "SELECT X, Y FROM 节点 WHERE 节点ID=?", (source,)
                ).fetchone()
                target_position = connection.execute(
                    "SELECT X, Y FROM 节点 WHERE 节点ID=?", (target,)
                ).fetchone()
                default_x = (float(source_position[0]) + float(target_position[0])) / 2
                default_y = (float(source_position[1]) + float(target_position[1])) / 2
            else:
                default_x = 160.0 + (sequence % 4) * 180.0
                default_y = 120.0 + (sequence // 4) * 120.0
            node_x = float(x) if x is not None else default_x
            node_y = float(y) if y is not None else default_y
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
            if unconnected and sequence == 0:
                connection.execute(
                    "DELETE FROM 节点连接 WHERE 源节点ID=? AND 目标节点ID=?",
                    (START_NODE_ID, END_NODE_ID),
                )
            elif not unconnected:
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
        with self._transaction(validate_graph=False) as connection:
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

    def update_command_note(self, command_id: int, note: str) -> None:
        with self._transaction(validate_graph=False) as connection:
            cursor = connection.execute(
                "UPDATE 命令 SET 备注=? WHERE ID=?", (str(note), int(command_id))
            )
            if cursor.rowcount != 1:
                raise KeyError(f"命令不存在：{command_id}")

    def duplicate_command(self, command_id: int, *, unconnected: bool = False) -> CommandRecord:
        command = self.get_command(command_id)
        if command is None:
            raise KeyError(f"命令不存在：{command_id}")
        with self._connection() as connection:
            node = connection.execute(
                "SELECT 节点ID, X, Y FROM 节点 WHERE 命令ID=?", (command_id,)
            ).fetchone()
            if node is None:
                raise GraphValidationError("命令缺少对应节点")
            outgoing = connection.execute(
                "SELECT 目标节点ID FROM 节点连接 WHERE 源节点ID=? ORDER BY rowid LIMIT 1",
                (node[0],),
            ).fetchone()
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
            split_edge=None if unconnected or outgoing is None else (node[0], outgoing[0]),
            unconnected=unconnected,
        )

    def delete_commands(
        self, command_ids: Iterable[int], *, preserve_flow: bool = True
    ) -> int:
        unique_ids = tuple(dict.fromkeys(int(item) for item in command_ids))
        if not unique_ids:
            return 0
        with self._transaction(validate_graph=preserve_flow) as connection:
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
            if preserve_flow:
                chain = self._validate_connection(connection, require_order=True)
                remaining_nodes = [
                    node_id for node_id in chain
                    if connection.execute(
                        "SELECT 命令ID FROM 节点 WHERE 节点ID=?", (node_id,)
                    ).fetchone()[0] not in existing
                ]
                connection.execute("DELETE FROM 节点连接")
            connection.execute(
                "DELETE FROM 命令 WHERE ID IN ({})".format(
                    ",".join("?" for _ in existing)
                ),
                tuple(existing),
            )
            if preserve_flow:
                connection.executemany(
                    "INSERT INTO 节点连接(源节点ID, 目标节点ID) VALUES (?, ?)",
                    zip(remaining_nodes, remaining_nodes[1:]),
                )
                self._sync_orders_from_chain(connection)
            else:
                remaining_ids = [row[0] for row in connection.execute(
                    "SELECT ID FROM 命令 ORDER BY 排序, ID"
                )]
                self._set_command_orders(connection, remaining_ids)
            deleted_count = len(existing)
        return deleted_count

    def clear(self) -> None:
        with self._transaction(validate_graph=False) as connection:
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

    def save_node_size(self, node_id: str, width: float, height: float) -> None:
        width, height = float(width), float(height)
        if not math.isfinite(width) or not math.isfinite(height):
            raise ValueError("节点大小必须是有限数值")
        if width < 90 or height < 40:
            raise ValueError("节点大小低于允许范围")
        with self._transaction(validate_graph=False) as connection:
            row = connection.execute(
                "SELECT 1 FROM 节点 WHERE 节点ID=? AND 节点类型='instruction'",
                (node_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"指令节点不存在：{node_id}")
            connection.execute(
                "INSERT INTO 节点布局(节点ID, 宽度, 高度) VALUES (?, ?, ?) "
                "ON CONFLICT(节点ID) DO UPDATE SET 宽度=excluded.宽度, 高度=excluded.高度",
                (node_id, round(width, 2), round(height, 2)),
            )

    def save_node_positions(
        self, positions: Mapping[str, Sequence[float]]
    ) -> None:
        normalized = self._normalize_node_positions(positions)
        if not normalized:
            return
        with self._transaction(validate_graph=False) as connection:
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
            edge_sheet_rows = [
                (edge.source, edge.target, edge.kind)
                for edge in self._edge_records(connection)
            ]
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
                if source_type == "条件判断":
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
            if isinstance(kind, bool) or not isinstance(kind, int) or kind not in range(5):
                raise WorkbookValidationError("连线类型必须是 0 到 4 的整数")
            edges.append(EdgeRecord(source.strip(), target.strip(), kind))
        try:
            self._validate_records(
                commands, nodes, edges, require_order=True, allow_incomplete=True
            )
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
                connection.execute("DELETE FROM flow_edge_metadata")
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
                connection.executemany(
                    "INSERT INTO flow_edge_metadata(source_id, target_id, kind) VALUES (?, ?, ?)",
                    [(edge.source, edge.target, edge.kind) for edge in edges],
                )
                DatabaseOperation._apply_parsed_settings(connection, settings)
                self._validate_draft_connection(connection)
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
