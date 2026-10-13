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
    *(_spec(name_, "后台功能", "#6979d8") for name_ in (
        "绑定选择窗口", "解除后台绑定", "后台文字识别", "后台字库管理", "后台图色操作",
        "后台键鼠操作", "后台窗口操作", "后台信息窗口", "后台内存操作", "后台汇编操作", "后台答题器",
    )),
    *(_spec(name_, "键鼠", "#2f80ed") for name_ in (
        "图像点击", "多图点击", "坐标点击", "多坐标点击", "移动鼠标", "鼠标点击",
        "滚轮滑动", "按下键盘", "文本输入", "中键激活", "鼠标拖拽", "悬停后点击", "颜色判断",
    )),
    *(_spec(name_, "等待", "#f2a900") for name_ in (
        "时间等待", "图像等待", "倒计时窗口", "按键等待", "窗口焦点等待",
    )),
    *(_spec(name_, "获取变量", "#64748b") for name_ in (
        "获取时间", "获取Excel", "获取鼠标位置", "获取剪切板", "获取对话框",
        "数字验证码", "OCR识别",
    )),
    InstructionSpec("写入单元格", "写入单元格（独立文件）", "Excel", "instructions.Excel.写入单元格.写入单元格", node_color="#5b6fdc"),
    *(_spec(name_, "本地OCR", "#527cbb") for name_ in (
        "OCR文字提取", "OCR精准找字点击", "OCR模糊找字返回坐标",
        "OCR范围找字", "OCR等待文字出现", "OCR等待文字消失",
        "截图OCR", "OCR复制", "OCR粘贴",
        "OCR识别区域返回坐标", "OCR点击识别区域",
    )),
    *(_spec(name_, "其他", "#8e44ad") for name_ in (
        "运行Python", "运行cmd", "运行外部文件", "窗口控制", "信息录入",
        "屏幕截图", "提示音", "提示窗口", "发送消息",
    )),
    InstructionSpec("粘贴到单元格", "粘贴到单元格", "Excel", "instructions.Excel.粘贴到单元格.粘贴到单元格", node_color="#16a085"),
    InstructionSpec("打开Excel", "打开Excel", "Excel", "instructions.Excel.打开Excel.打开Excel", node_color="#16a085"),
    InstructionSpec("读取单元格", "读取单元格", "Excel", "instructions.Excel.读取单元格.读取单元格", node_color="#16a085"),
    InstructionSpec("Excel写入单元格", "写入单元格", "Excel", "instructions.Excel.Excel写入单元格.Excel写入单元格", node_color="#16a085"),
    InstructionSpec("读取区域", "读取区域", "Excel", "instructions.Excel.读取区域.读取区域", node_color="#16a085"),
    InstructionSpec("写入区域", "写入区域", "Excel", "instructions.Excel.写入区域.写入区域", node_color="#16a085"),
    InstructionSpec("复制粘贴（选择性粘贴）", "复制粘贴(选择性粘贴)", "Excel", "instructions.Excel.复制粘贴（选择性粘贴）.复制粘贴（选择性粘贴）", node_color="#16a085"),
    InstructionSpec("表格复制粘贴", "表格复制粘贴", "Excel", "instructions.Excel.表格复制粘贴.表格复制粘贴", node_color="#16a085"),
    InstructionSpec("插入行", "插入行", "Excel", "instructions.Excel.插入行.插入行", node_color="#16a085"),
    InstructionSpec("插入列", "插入列", "Excel", "instructions.Excel.插入列.插入列", node_color="#16a085"),
    InstructionSpec("删除行", "删除行", "Excel", "instructions.Excel.删除行.删除行", node_color="#16a085"),
    InstructionSpec("删除列", "删除列", "Excel", "instructions.Excel.删除列.删除列", node_color="#16a085"),
    InstructionSpec("获取行数", "获取行数", "Excel", "instructions.Excel.获取行数.获取行数", node_color="#16a085"),
    InstructionSpec("新建Excel", "新建Excel", "Excel", "instructions.Excel.新建Excel.新建Excel", node_color="#16a085"),
    InstructionSpec("保存Excel", "保存Excel", "Excel", "instructions.Excel.保存Excel.保存Excel", node_color="#16a085"),
    InstructionSpec("表格另存为", "表格另存为", "Excel", "instructions.Excel.表格另存为.表格另存为", node_color="#16a085"),
    InstructionSpec("处理文件（白话）", "处理文件(白话)", "白话指令", "instructions.白话指令.处理文件（白话）.处理文件（白话）", node_color="#d35400"),
    InstructionSpec("重命名文件（白话）", "重命名文件(白话)", "白话指令", "instructions.白话指令.重命名文件（白话）.重命名文件（白话）", node_color="#d35400"),
    InstructionSpec("查找文件（白话）", "查找文件(白话)", "白话指令", "instructions.白话指令.查找文件（白话）.查找文件（白话）", node_color="#d35400"),
    InstructionSpec("统计文件（白话）", "统计文件(白话)", "白话指令", "instructions.白话指令.统计文件（白话）.统计文件（白话）", node_color="#d35400"),
    InstructionSpec("表格复制粘贴（白话）", "表格复制粘贴(白话)", "白话指令", "instructions.白话指令.表格复制粘贴（白话）.表格复制粘贴（白话）", node_color="#d35400"),
    InstructionSpec("打开网页", "打开网页", "网页自动化", "instructions.网页自动化.打开网页.打开网页", node_color="#4a6cf7"),
    InstructionSpec("点击元素", "点击元素", "网页自动化", "instructions.网页自动化.点击元素.点击元素", node_color="#4a6cf7"),
    InstructionSpec("输入文本", "输入文本", "网页自动化", "instructions.网页自动化.输入文本.输入文本", node_color="#4a6cf7"),
    InstructionSpec("获取文本", "获取文本", "网页自动化", "instructions.网页自动化.获取文本.获取文本", node_color="#4a6cf7"),
    InstructionSpec("网页截图", "网页截图", "网页自动化", "instructions.网页自动化.网页截图.网页截图", node_color="#4a6cf7"),
    InstructionSpec("等待元素出现", "等待元素出现", "网页自动化", "instructions.网页自动化.等待元素出现.等待元素出现", node_color="#4a6cf7"),
    InstructionSpec("等待页面加载完成", "等待页面加载完成", "网页自动化", "instructions.网页自动化.等待页面加载完成.等待页面加载完成", node_color="#4a6cf7"),
    InstructionSpec("诊断页面（排错）", "诊断页面(排错)", "网页自动化", "instructions.网页自动化.诊断页面（排错）.诊断页面（排错）", node_color="#98a2b3"),
    InstructionSpec("坐标点击（可多点）", "网页内坐标点击（可多点）", "网页自动化", "instructions.网页自动化.坐标点击（可多点）.坐标点击（可多点）", node_color="#4a6cf7"),
    InstructionSpec("等待（秒）", "等待(秒)", "网页自动化", "instructions.网页自动化.等待（秒）.等待（秒）", node_color="#4a6cf7"),
    InstructionSpec("按键", "按键", "网页自动化", "instructions.网页自动化.按键.按键", node_color="#4a6cf7"),
    InstructionSpec("点击并全选复制", "点击并全选复制", "网页自动化", "instructions.网页自动化.点击并全选复制.点击并全选复制", node_color="#4a6cf7"),
    InstructionSpec("点击并粘贴", "点击并粘贴", "网页自动化", "instructions.网页自动化.点击并粘贴.点击并粘贴", node_color="#4a6cf7"),
    InstructionSpec("复制到剪贴板", "复制到剪贴板", "网页自动化", "instructions.网页自动化.复制到剪贴板.复制到剪贴板", node_color="#e67e22"),
    InstructionSpec("粘贴到网页元素", "粘贴到网页元素", "网页自动化", "instructions.网页自动化.粘贴到网页元素.粘贴到网页元素", node_color="#4a6cf7"),
    InstructionSpec("提取文本到表格", "提取文本到表格", "网页自动化", "instructions.网页自动化.提取文本到表格.提取文本到表格", node_color="#e67e22"),
    InstructionSpec("拾取元素", "拾取元素", "网页自动化", "instructions.网页自动化.拾取元素.拾取元素", node_color="#4a6cf7"),
    InstructionSpec("抓取文本", "抓取文本", "数据抓取", "instructions.数据抓取.抓取文本.抓取文本", node_color="#e67e22"),
    InstructionSpec("抓取属性", "抓取属性", "数据抓取", "instructions.数据抓取.抓取属性.抓取属性", node_color="#e67e22"),
    InstructionSpec("抓取列表", "抓取列表", "数据抓取", "instructions.数据抓取.抓取列表.抓取列表", node_color="#e67e22"),
    InstructionSpec("抓取导出Excel", "抓取导出Excel", "数据抓取", "instructions.数据抓取.抓取导出Excel.抓取导出Excel", node_color="#e67e22"),
    _spec("暂不运行以下指令", "流程", "#64748b"),
    _spec("暂不运行以上指令", "流程", "#64748b"),
    _spec("终止流程", "流程", "#eb5757"),
    _spec("运行项目", "流程", "#5b6fdc"),
    _spec("报错跳转", "流程", "#d99653"),
    _spec("变量比较", "流程", "#d09b43"),
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
if len(INSTRUCTION_SPECS) != len(_SPEC_BY_ID):
    raise RuntimeError("指令注册表存在重复 type_id")


def get_instruction_spec(type_id: str) -> InstructionSpec:
    try:
        return _SPEC_BY_ID[type_id]
    except KeyError as error_:
        raise KeyError(f"未知指令类型：{type_id}") from error_


def iter_instruction_specs(category: str | None = None) -> Iterator[InstructionSpec]:
    return (spec_ for spec_ in INSTRUCTION_SPECS if category is None or spec_.category == category)


def hidden_imports() -> tuple[str, ...]:
    return tuple(spec_.module_path for spec_ in INSTRUCTION_SPECS)
