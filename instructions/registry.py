"""正式指令的唯一注册清单。"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Iterator


@dataclass(frozen=True, slots=True)
class InstructionSpec:
    type_id: str
    display_name: str
    category: str
    module_path: str
    editor_class: str = "InstructionEditor"
    executor_class: str = "InstructionExecutor"
    icon: str = ""
    node_color: str = "#3b82f6"
    input_ports: tuple[str, ...] = ("flow",)
    output_ports: tuple[str, ...] = ("flow",)

    def load_editor_class(self):
        return getattr(import_module(self.module_path), self.editor_class)

    def load_executor_class(self):
        return getattr(import_module(self.module_path), self.executor_class)

    def create_editor(self, parent=None, draft=None, context=None):
        return self.load_editor_class()(parent=parent, draft=draft, context=context)

    def create_executor(self):
        return self.load_executor_class()()


def _spec(name_: str, category_: str, color_: str) -> InstructionSpec:
    return InstructionSpec(
        type_id=name_,
        display_name=name_,
        category=category_,
        module_path=f"instructions.{category_}.{name_}.{name_}",
        node_color=color_,
    )


INSTRUCTION_SPECS: tuple[InstructionSpec, ...] = (
    *(_spec(name_, "键鼠", "#2f80ed") for name_ in (
        "图像点击", "多图点击", "坐标点击", "移动鼠标", "鼠标点击",
        "滚轮滑动", "按下键盘", "文本输入", "中键激活", "鼠标拖拽", "悬停后点击", "颜色判断",
    )),
    *(_spec(name_, "等待", "#f2a900") for name_ in (
        "时间等待", "图像等待", "倒计时窗口", "按键等待", "窗口焦点等待",
    )),
    *(_spec(name_, "获取变量", "#64748b") for name_ in (
        "获取时间", "获取Excel", "获取鼠标位置", "获取剪切板", "获取对话框",
        "数字验证码", "OCR识别",
    )),
    _spec("写入单元格", "Excel", "#5b6fdc"),
    *(_spec(name_, "其他", "#8e44ad") for name_ in (
        "运行Python", "运行cmd", "运行外部文件", "窗口控制", "信息录入",
        "屏幕截图", "提示音", "提示窗口",
    )),
    _spec("终止流程", "流程", "#eb5757"),
    InstructionSpec(
        "循环", "循环", "流程", "instructions.流程.循环.循环", node_color="#5b6fdc",
    ),
    InstructionSpec(
        "条件判断", "条件判断", "流程", "instructions.流程.条件判断.条件判断", node_color="#d09b43",
    ),
    InstructionSpec(
        "条件循环", "条件循环", "流程", "instructions.流程.条件循环.条件循环", node_color="#9b6bd3",
    ),
)

_SPEC_BY_ID = {spec_.type_id: spec_ for spec_ in INSTRUCTION_SPECS}
if len(INSTRUCTION_SPECS) != 37 or len(_SPEC_BY_ID) != 37:
    raise RuntimeError("指令注册表必须包含 37 个唯一 type_id")


def get_instruction_spec(type_id: str) -> InstructionSpec:
    try:
        return _SPEC_BY_ID[type_id]
    except KeyError as error_:
        raise KeyError(f"未知指令类型：{type_id}") from error_


def iter_instruction_specs(category: str | None = None) -> Iterator[InstructionSpec]:
    return (spec_ for spec_ in INSTRUCTION_SPECS if category is None or spec_.category == category)


def hidden_imports() -> tuple[str, ...]:
    return tuple(spec_.module_path for spec_ in INSTRUCTION_SPECS)
