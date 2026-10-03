"""指令编辑器与执行器之间的稳定数据协议。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, MutableMapping
import json


JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def _json_object(value: Mapping[str, Any] | str | None) -> dict[str, JsonValue]:
    if value is None:
        return {}
    if isinstance(value, str):
        decoded = json.loads(value)
    elif isinstance(value, Mapping):
        decoded = dict(value)
    else:
        raise TypeError("指令参数必须是 JSON 对象或其字符串表示")
    if not isinstance(decoded, dict):
        raise ValueError("指令参数的 JSON 根节点必须是对象")
    # 往返一次，拒绝 tuple、set、自定义对象等非 JSON 数据。
    return json.loads(json.dumps(decoded, ensure_ascii=False, allow_nan=False))


@dataclass(slots=True)
class InstructionDraft:
    type_id: str
    parameters: dict[str, JsonValue] = field(default_factory=dict)
    repeat_count: int = 1
    error_policy: str = "提示异常并暂停"
    note: str = ""

    def __post_init__(self) -> None:
        self.type_id = str(self.type_id).strip()
        if not self.type_id:
            raise ValueError("type_id 不能为空")
        self.parameters = _json_object(self.parameters)
        self.repeat_count = int(self.repeat_count)
        if self.repeat_count < 1:
            raise ValueError("repeat_count 必须大于等于 1")
        self.error_policy = str(self.error_policy or "提示异常并暂停")
        self.note = str(self.note or "")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "InstructionDraft":
        return cls(
            type_id=value.get("type_id", value.get("类型标识", "")),
            parameters=value.get("parameters", value.get("参数JSON", {})),
            repeat_count=value.get("repeat_count", value.get("重复次数", 1)),
            error_policy=value.get("error_policy", value.get("异常处理", "提示异常并暂停")),
            note=value.get("note", value.get("备注", "")),
        )

    def parameters_json(self) -> str:
        return json.dumps(
            self.parameters,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )


@dataclass(slots=True)
class CommandRecord:
    id: int | None
    type_id: str
    parameters: dict[str, JsonValue] = field(default_factory=dict)
    repeat_count: int = 1
    error_policy: str = "提示异常并暂停"
    note: str = ""
    order: int = 0

    def __post_init__(self) -> None:
        self.id = None if self.id is None else int(self.id)
        self.type_id = str(self.type_id).strip()
        if not self.type_id:
            raise ValueError("type_id 不能为空")
        self.parameters = _json_object(self.parameters)
        self.repeat_count = int(self.repeat_count)
        if self.repeat_count < 1:
            raise ValueError("repeat_count 必须大于等于 1")
        self.error_policy = str(self.error_policy or "提示异常并暂停")
        self.note = str(self.note or "")
        self.order = int(self.order)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CommandRecord":
        return cls(
            id=value.get("id", value.get("ID")),
            type_id=value.get("type_id", value.get("类型标识", "")),
            parameters=value.get("parameters", value.get("参数JSON", {})),
            repeat_count=value.get("repeat_count", value.get("重复次数", 1)),
            error_policy=value.get("error_policy", value.get("异常处理", "提示异常并暂停")),
            note=value.get("note", value.get("备注", "")),
            order=value.get("order", value.get("排序", 0)),
        )

    def to_draft(self) -> InstructionDraft:
        return InstructionDraft(
            self.type_id,
            self.parameters,
            self.repeat_count,
            self.error_policy,
            self.note,
        )


@dataclass(slots=True)
class ExecutionContext:
    """运行期依赖。

    services 允许宿主程序按名称注入键鼠、OCR、Excel 等实现；没有注入时，
    各指令才会惰性使用项目已有的第三方依赖。这样导入指令包不会触发外部操作。
    """

    variables: MutableMapping[str, Any] = field(default_factory=dict)
    services: Mapping[str, Callable[..., Any]] = field(default_factory=dict)
    output: Callable[[str], None] | None = None
    iteration: int = 1
    stop_requested: bool = False
    metadata: MutableMapping[str, Any] = field(default_factory=dict)

    def emit(self, message: str) -> None:
        if self.output is not None:
            self.output(str(message))

    def service(self, name: str) -> Callable[..., Any] | None:
        service_ = self.services.get(name)
        return service_ if callable(service_) else None

    def set_variable(self, name: str, value: Any) -> Any:
        if name:
            self.variables[str(name)] = value
        return value
