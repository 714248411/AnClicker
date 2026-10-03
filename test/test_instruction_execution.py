"""正式指令真实 fallback 的执行语义回归测试。"""

from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
import os
import sys
import unittest
from unittest.mock import Mock, patch

from instructions.common import actions
from instructions.models import CommandRecord, ExecutionContext
from instructions.registry import INSTRUCTION_SPECS


class _Point:
    x = 12
    y = 34


class _Workbook:
    def __init__(self):
        self.cell = SimpleNamespace(value="测试中文")
        self.save = Mock()
        self.close = Mock()


def _command(type_id_: str, parameters_: dict) -> CommandRecord:
    return CommandRecord(
        id=1,
        type_id=type_id_,
        parameters=parameters_,
        repeat_count=1,
        error_policy="自动跳过",
        order=1,
    )


class InstructionFallbackTests(unittest.TestCase):
    def setUp(self):
        self.messages_ = []
        self.context_ = ExecutionContext(output=self.messages_.append)
        self.gui_ = SimpleNamespace(
            moveTo=Mock(), moveRel=Mock(), click=Mock(), scroll=Mock(),
            keyDown=Mock(), keyUp=Mock(), hotkey=Mock(), write=Mock(),
            mouseDown=Mock(), mouseUp=Mock(), dragTo=Mock(),
            position=Mock(return_value=_Point()),
            size=Mock(return_value=SimpleNamespace(width=1920, height=1080)),
            screenshot=Mock(return_value=SimpleNamespace(save=Mock(), convert=Mock())),
            getActiveWindowTitle=Mock(return_value="目标窗口"),
        )
        self.workbook_ = _Workbook()
        self.pyperclip_ = SimpleNamespace(copy=Mock(), paste=Mock(return_value="剪切板内容"))
        self.keyboard_ = SimpleNamespace(wait=Mock())
        self.mouse_ = SimpleNamespace(wait=Mock(), click=Mock())
        self.pymsgbox_ = SimpleNamespace(
            STOP="STOP", WARNING="WARNING", INFO="INFO", QUESTION="QUESTION",
            prompt=Mock(return_value="对话框内容"), alert=Mock(),
        )
        self.window_ = SimpleNamespace(
            activate=Mock(), minimize=Mock(), maximize=Mock(), restore=Mock(), close=Mock()
        )
        self.pygetwindow_ = SimpleNamespace(getWindowsWithTitle=Mock(return_value=[self.window_]))
        self.winsound_ = SimpleNamespace(
            SND_ALIAS=1, PlaySound=Mock(), MessageBeep=Mock(), Beep=Mock()
        )

    @staticmethod
    def _parameters() -> dict[str, dict]:
        return {
            "图像点击": {"图像路径": "a.png", "动作": "左键双击", "异常": "2", "点击位置": "0,0"},
            "多图点击": {"图像路径": "a.png\nb.png", "动作": "右键双击", "异常": "自动略过"},
            "坐标点击": {"动作": "左键双击", "坐标": "10,20", "自定义次数": 1},
            "移动鼠标": {"类型": "指定坐标", "坐标": "10,20", "持续": 0.1},
            "鼠标点击": {"鼠标": "左键", "次数": 2, "间隔": 1, "按压": 1, "辅助键": "ctrl"},
            "滚轮滑动": {"类型": "滚轮滑动", "方向": "向下", "距离": 5},
            "按下键盘": {"按键": "ctrl+a", "按压时长": 1},
            "文本输入": {"内容": "中文", "手动输入": False},
            "中键激活": {"类型": "模拟点击", "次数": 2},
            "鼠标拖拽": {"开始位置": "1,2", "结束位置": "3,4", "移动速度": 0.1},
            "时间等待": {"类型": "时间等待", "时长": 1, "单位": "毫秒"},
            "图像等待": {"图像路径": "a.png", "等待类型": "等待出现", "超时时间": 1},
            "倒计时窗口": {"标题": "倒计时", "内容": "等待", "秒数": 1},
            "按键等待": {"按键": "enter", "等待类型": "按键等待"},
            "窗口焦点等待": {"标题包含": "目标", "检测频率": 0.01, "等待时间": 1, "等待类型": "获得焦点"},
            "获取时间": {"变量": "时间", "时间格式": "年-月-日"},
            "获取Excel": {"工作簿": "a.xlsx", "工作表": "Sheet1", "单元格": "A1", "变量": "Excel"},
            "获取鼠标位置": {"变量": "鼠标"},
            "获取剪切板": {"变量": "剪切板"},
            "获取对话框": {"标题": "标题", "提示": "提示", "变量": "对话框"},
            "数字验证码": {"区域": "0,0,10,10", "验证码类型": "通用数英1-4位", "变量": "验证码"},
            "OCR识别": {"区域": "0,0,10,10", "变量": "OCR"},
            "写入单元格": {"工作簿": "a.xlsx", "工作表": "Sheet1", "单元格": "A1", "文本": "{{值}}"},
            "运行Python": {"代码": "answer = ☾值☽ + 1", "返回值": "answer", "变量": "Python"},
            "运行cmd": {"命令": "echo ok", "等待完成": True},
            "运行外部文件": {"文件路径": "a.exe", "参数": ""},
            "窗口控制": {"标题包含": "目标", "操作": "激活", "报错": True},
            "信息录入": {"图像路径": "a.png", "工作簿": "a.xlsx", "工作表": "Sheet1", "单元格": "A1", "模拟输入": False, "异常": 2, "空值处理": "抛出异常"},
            "屏幕截图": {"截图类型": "全屏截图", "保存路径": "shot.png", "截图后": "保存到路径"},
            "提示音": {"类型": "系统提示音", "提示类型": "系统警告", "次数": 1},
            "提示窗口": {"标题": "标题", "内容": "内容", "图标": "警告"},
            "终止流程": {"终止类型": "终止所有任务"},
        }

    def test_all_32_real_fallbacks_execute_without_delegated_service(self):
        parameters_ = self._parameters()
        self.assertEqual(set(parameters_), {spec_.type_id for spec_ in INSTRUCTION_SPECS})
        self.context_.variables["值"] = 2
        process_result_ = SimpleNamespace(stdout="ok\n", returncode=0)

        with ExitStack() as stack_:
            stack_.enter_context(patch.object(actions, "pyautogui_module", return_value=self.gui_))
            stack_.enter_context(patch.object(actions, "wait_seconds"))
            stack_.enter_context(patch.object(actions, "locate_image", return_value=_Point()))
            stack_.enter_context(patch.object(actions, "locate_image_with_policy", return_value=(_Point(), False)))
            stack_.enter_context(patch.object(actions, "image_random_offset", return_value=(0, 0)))
            stack_.enter_context(patch.object(actions, "workbook_cell", return_value=(self.workbook_, None, self.workbook_.cell)))
            stack_.enter_context(patch.object(actions, "current_time", return_value="2026-08-10"))
            stack_.enter_context(patch.object(actions, "run_process", return_value=process_result_))
            stack_.enter_context(patch.object(actions, "ensure_parent"))
            stack_.enter_context(patch.object(os, "startfile", create=True))
            stack_.enter_context(patch.dict(sys.modules, {
                "pyperclip": self.pyperclip_, "keyboard": self.keyboard_, "mouse": self.mouse_,
                "pymsgbox": self.pymsgbox_, "pygetwindow": self.pygetwindow_, "winsound": self.winsound_,
            }))

            for spec_ in INSTRUCTION_SPECS:
                with self.subTest(type_id=spec_.type_id):
                    executor_ = spec_.create_executor()
                    if spec_.type_id == "数字验证码":
                        stack_.enter_context(patch.object(executor_, "_recognize", return_value="1234"))
                    elif spec_.type_id == "OCR识别":
                        stack_.enter_context(patch.object(executor_, "_recognize", return_value="文字"))
                    elif spec_.type_id == "倒计时窗口":
                        stack_.enter_context(patch.object(executor_, "_show_countdown"))
                    executor_.execute(self.context_, _command(spec_.type_id, parameters_[spec_.type_id]))

        self.assertEqual(self.context_.variables["Python"], 3)
        self.assertEqual(self.context_.variables["剪切板"], "剪切板内容")
        self.assertEqual(self.context_.variables["验证码"], "1234")
        self.assertEqual(self.context_.variables["OCR"], "文字")
        self.pymsgbox_.alert.assert_called_with(text="内容", title="标题", icon="WARNING")
        self.winsound_.PlaySound.assert_called_with("SystemAsterisk", 1)

    def test_exposed_fields_are_consumed_by_executor_or_shared_runtime(self):
        common_source_ = (Path(actions.__file__).read_text(encoding="utf-8"))
        for spec_ in INSTRUCTION_SPECS:
            with self.subTest(type_id=spec_.type_id):
                module_ = sys.modules.get(spec_.module_path)
                if module_ is None:
                    spec_.load_executor_class()
                    module_ = sys.modules[spec_.module_path]
                source_ = Path(module_.__file__).read_text(encoding="utf-8")
                executor_source_ = source_[source_.index("class InstructionExecutor"):]
                for field_ in spec_.load_editor_class().FIELDS:
                    self.assertIn(field_.key, executor_source_ + common_source_)

    def test_mouse_action_uses_action_default_click_count(self):
        with patch.object(actions, "pyautogui_module", return_value=self.gui_):
            actions.mouse_action("左键双击", 1, 2)
            self.assertEqual(self.gui_.click.call_args.kwargs["clicks"], 2)
            actions.mouse_action("左键三击", 1, 2)
            self.assertEqual(self.gui_.click.call_args.kwargs["clicks"], 3)
            actions.mouse_action("右键双击", 1, 2, count_=1)
            self.assertEqual(self.gui_.click.call_args.kwargs["clicks"], 2)
            actions.mouse_action("左键（自定义次数）", 1, 2, count_=4)
            self.assertEqual(self.gui_.click.call_args.kwargs["clicks"], 4)

    def test_coordinate_double_click_is_not_overridden_by_custom_count_field(self):
        spec_ = next(spec_ for spec_ in INSTRUCTION_SPECS if spec_.type_id == "坐标点击")
        with patch.object(actions, "pyautogui_module", return_value=self.gui_):
            spec_.create_executor().execute(
                self.context_,
                _command(
                    "坐标点击",
                    {"动作": "左键双击", "坐标": "10,20", "自定义次数": 1},
                ),
            )
        self.assertEqual(self.gui_.click.call_args.kwargs["clicks"], 2)

    def test_information_entry_empty_policy_and_unicode_paste(self):
        spec_ = next(spec_ for spec_ in INSTRUCTION_SPECS if spec_.type_id == "信息录入")
        executor_ = spec_.create_executor()
        empty_book_ = _Workbook()
        empty_book_.cell.value = None
        parameters_ = self._parameters()["信息录入"]
        with patch.object(actions, "workbook_cell", return_value=(empty_book_, None, empty_book_.cell)):
            with self.assertRaisesRegex(ValueError, "值为空"):
                executor_.execute(self.context_, _command("信息录入", parameters_))

        with patch.object(actions, "workbook_cell", return_value=(self.workbook_, None, self.workbook_.cell)), \
                patch.object(actions, "locate_image_with_policy", return_value=(_Point(), False)), \
                patch.object(actions, "mouse_action") as mouse_action_, \
                patch.object(actions, "pyautogui_module", return_value=self.gui_), \
                patch.dict(sys.modules, {"pyperclip": self.pyperclip_}):
            executor_.execute(self.context_, _command("信息录入", parameters_))
        mouse_action_.assert_called_once_with("左键三击", 12, 34)
        self.pyperclip_.copy.assert_called_with("测试中文")
        self.gui_.hotkey.assert_called_with("ctrl", "v")

    def test_image_timeout_and_random_offset_use_real_image_size(self):
        self.assertEqual(actions.image_error_timeout({"异常": "2.5"}), (False, 2.5))
        self.assertEqual(actions.image_error_timeout({"异常": "自动略过"}), (True, 1.0))
        locator_ = Mock(return_value=_Point())
        image_ = SimpleNamespace(size=(80, 40))
        image_context_ = Mock()
        image_context_.__enter__ = Mock(return_value=image_)
        image_context_.__exit__ = Mock(return_value=False)
        with patch.object(actions, "resolve_image_path", return_value="a.png"), \
                patch.object(actions, "pyautogui_module", return_value=SimpleNamespace(locateCenterOnScreen=locator_)), \
                patch("PIL.Image.open", return_value=image_context_), \
                patch.object(actions.random, "randint", side_effect=lambda low_, high_: high_):
            actions.locate_image({"图像路径": "a.png"}, min_search_time=2.5)
            offset_ = actions.image_random_offset({"图像路径": "a.png"})
        self.assertEqual(locator_.call_args.kwargs["minSearchTime"], 2.5)
        self.assertEqual(offset_, (40, 20))

    def test_countdown_fallback_creates_topmost_stoppable_window(self):
        root_ = Mock()
        root_.winfo_screenwidth.return_value = 1920
        root_.winfo_screenheight.return_value = 1080
        root_.winfo_width.return_value = 300
        root_.winfo_height.return_value = 200
        root_.after.side_effect = lambda _delay_, callback_: callback_()
        label_ = Mock()
        label_.pack.return_value = None
        button_ = Mock()
        button_.pack.return_value = None
        ttk_ = SimpleNamespace(Button=Mock(return_value=button_))
        tkinter_ = SimpleNamespace(
            Tk=Mock(return_value=root_), Label=Mock(return_value=label_),
            TclError=RuntimeError, ttk=ttk_,
        )
        spec_ = next(spec_ for spec_ in INSTRUCTION_SPECS if spec_.type_id == "倒计时窗口")
        with patch.dict(sys.modules, {"tkinter": tkinter_, "tkinter.ttk": ttk_}):
            spec_.create_executor()._show_countdown(self.context_, "标题", "内容", 1)
        root_.attributes.assert_any_call("-topmost", True)
        ttk_.Button.assert_called_once()
        root_.destroy.assert_called_once()
        self.assertIn("已结束等待窗口", self.messages_)

    def test_run_python_old_result_name_and_variable_substitution(self):
        context_ = ExecutionContext(variables={"数字": 4})
        result_ = actions.run_python_code(
            context_, "answer = ☾数字☽ + 3", "answer", "目标"
        )
        self.assertEqual(result_, 7)
        self.assertEqual(context_.variables["目标"], 7)

    def test_legacy_time_units_and_formats(self):
        spec_ = next(spec_ for spec_ in INSTRUCTION_SPECS if spec_.type_id == "时间等待")
        executor_ = spec_.create_executor()
        self.assertEqual(executor_._duration_seconds("500-毫秒"), 0.5)
        self.assertEqual(executor_._duration_seconds("2-分钟"), 120)
        value_ = actions.current_time("年-月-日 小时:分钟:秒")
        self.assertNotIn("小时", value_)
        self.assertEqual(len(value_), 19)

    def test_missing_coordinate_variable_raises_instead_of_moving_to_origin(self):
        spec_ = next(spec_ for spec_ in INSTRUCTION_SPECS if spec_.type_id == "移动鼠标")
        executor_ = spec_.create_executor()
        with patch.object(actions, "pyautogui_module", return_value=self.gui_):
            with self.assertRaisesRegex(KeyError, "变量不存在"):
                executor_.execute(
                    ExecutionContext(),
                    _command("移动鼠标", {"类型": "变量坐标", "变量": "缺失"}),
                )
        self.gui_.moveTo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
