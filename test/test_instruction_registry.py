"""独立指令注册表、编辑器和执行器的契约测试。"""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import Mock
import xml.etree.ElementTree as ElementTree


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from instructions.models import (  # noqa: E402
    CommandRecord,
    ExecutionContext,
    InstructionDraft,
)
from instructions.registry import INSTRUCTION_SPECS, hidden_imports  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INSTRUCTIONS_ROOT = PROJECT_ROOT / "instructions"


class InstructionRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application_ = QApplication.instance() or QApplication([])

    def test_registry_contains_exactly_32_unique_instruction_types(self):
        type_ids_ = [spec_.type_id for spec_ in INSTRUCTION_SPECS]
        module_paths_ = [spec_.module_path for spec_ in INSTRUCTION_SPECS]

        self.assertEqual(len(type_ids_), 32)
        self.assertEqual(len(set(type_ids_)), 32)
        self.assertEqual(len(set(module_paths_)), 32)
        self.assertEqual(tuple(module_paths_), hidden_imports())
        for spec_ in INSTRUCTION_SPECS:
            self.assertTrue(spec_.display_name)
            self.assertTrue(spec_.category)
            self.assertEqual(spec_.input_ports, ("flow",))
            self.assertEqual(spec_.output_ports, ("flow",))

    def test_each_instruction_has_independent_source_and_ui_files(self):
        ui_hashes_ = set()
        auxiliary_keys_ = {
            "图像路径",
            "工作簿",
            "文件路径",
            "保存路径",
            "坐标",
            "开始位置",
            "结束位置",
            "点击位置",
            "区域",
            "单元格",
            "代码",
            "变量",
        }
        for spec_ in INSTRUCTION_SPECS:
            with self.subTest(type_id=spec_.type_id):
                folder_ = INSTRUCTIONS_ROOT / spec_.category / spec_.type_id
                expected_files_ = (
                    folder_ / f"{spec_.type_id}.ui",
                    folder_ / f"{spec_.type_id}_ui.py",
                    folder_ / f"{spec_.type_id}.py",
                )
                self.assertTrue(folder_.is_dir())
                for path_ in expected_files_:
                    self.assertTrue(path_.is_file(), str(path_))
                    self.assertGreater(path_.stat().st_size, 0, str(path_))

                ui_path_, generated_path_, _ = expected_files_
                ui_source_ = ui_path_.read_text(encoding="utf-8")
                generated_source_ = generated_path_.read_text(encoding="utf-8")
                ui_hashes_.add(hashlib.sha256(ui_source_.encode("utf-8")).hexdigest())
                ui_root_ = ElementTree.fromstring(ui_source_)
                widget_names_ = {
                    widget_.attrib.get("name", "")
                    for widget_ in ui_root_.iter("widget")
                }
                editor_class_ = spec_.load_editor_class()
                for index_, field_ in enumerate(editor_class_.FIELDS):
                    parameter_name_ = f"parameter_{index_}"
                    self.assertIn(parameter_name_, widget_names_)
                    self.assertIn(f"self.{parameter_name_}", generated_source_)
                    if field_.key in auxiliary_keys_:
                        auxiliary_name_ = f"auxiliary_{index_}"
                        self.assertIn(auxiliary_name_, widget_names_)
                        self.assertIn(f"self.{auxiliary_name_}", generated_source_)
                for common_name_ in (
                    "repeatSpinBox",
                    "errorPolicyComboBox",
                    "noteEdit",
                    "testButton",
                    "buttonBox",
                ):
                    self.assertIn(common_name_, widget_names_)
                    self.assertIn(f"self.{common_name_}", generated_source_)

        self.assertGreater(len(ui_hashes_), 1, "32 个独立 UI 不得是同一个空壳模板")

    def test_common_editor_only_binds_controls_declared_in_ui(self):
        source_ = (INSTRUCTIONS_ROOT / "common" / "editor.py").read_text(encoding="utf-8")
        for constructor_ in (
            "QLineEdit(",
            "QPlainTextEdit(",
            "QComboBox(",
            "QSpinBox(",
            "QDoubleSpinBox(",
            "QCheckBox(",
        ):
            self.assertNotIn(constructor_, source_)

    @staticmethod
    def _draft_parameters(editor_):
        parameters_ = {}
        for field_ in editor_.FIELDS:
            value_ = field_.default
            if field_.required and (value_ is None or str(value_) == ""):
                if field_.key == "单元格":
                    value_ = "A1"
                elif field_.key == "区域":
                    value_ = "0,0,10,10"
                else:
                    value_ = "test"
            parameters_[field_.key] = value_
        return parameters_

    def test_all_editors_instantiate_and_round_trip_json_drafts(self):
        for spec_ in INSTRUCTION_SPECS:
            with self.subTest(type_id=spec_.type_id):
                editor_ = spec_.create_editor()
                try:
                    parameters_ = self._draft_parameters(editor_)
                    source_ = InstructionDraft(
                        type_id=spec_.type_id,
                        parameters=parameters_,
                        repeat_count=3,
                        error_policy="自动跳过",
                        note="JSON round trip",
                    )
                    editor_.load_draft(source_)
                    restored_ = editor_.get_draft()

                    self.assertEqual(restored_.type_id, spec_.type_id)
                    self.assertEqual(restored_.parameters, parameters_)
                    self.assertEqual(restored_.repeat_count, 3)
                    self.assertEqual(restored_.error_policy, "自动跳过")
                    self.assertEqual(restored_.note, "JSON round trip")
                    self.assertEqual(
                        json.loads(restored_.parameters_json()),
                        restored_.parameters,
                    )
                finally:
                    editor_.close()
                    editor_.deleteLater()
        self.application_.processEvents()

    def test_editors_validate_text_formats_and_cross_field_constraints(self):
        invalid_parameters_ = {
            "图像点击": {"图像路径": "test.png", "区域": "0,0,-1,20"},
            "坐标点击": {"坐标": "invalid"},
            "获取Excel": {"工作簿": "test.xlsx", "单元格": "A0"},
            "时间等待": {
                "类型": "随机等待",
                "最小": 5,
                "最小单位": "秒",
                "最大": 1,
                "最大单位": "秒",
            },
        }
        specs_ = {spec_.type_id: spec_ for spec_ in INSTRUCTION_SPECS}
        for type_id_, overrides_ in invalid_parameters_.items():
            with self.subTest(type_id=type_id_):
                editor_ = specs_[type_id_].create_editor()
                try:
                    parameters_ = self._draft_parameters(editor_)
                    parameters_.update(overrides_)
                    editor_.load_draft(
                        InstructionDraft(type_id=type_id_, parameters=parameters_)
                    )
                    with self.assertRaises(ValueError):
                        editor_.get_draft()
                finally:
                    editor_.close()
                    editor_.deleteLater()
        self.application_.processEvents()

    def test_all_executors_are_lazy_mapped_and_honor_repeat_count(self):
        for spec_ in INSTRUCTION_SPECS:
            with self.subTest(type_id=spec_.type_id):
                service_ = Mock(return_value=spec_.type_id)
                context_ = ExecutionContext(services={spec_.type_id: service_})
                command_ = CommandRecord(
                    id=1,
                    type_id=spec_.type_id,
                    parameters={},
                    repeat_count=3,
                    error_policy="自动跳过",
                    note="",
                    order=1,
                )

                executor_class_ = spec_.load_executor_class()
                executor_ = spec_.create_executor()
                self.assertIsInstance(executor_, executor_class_)
                self.assertEqual(executor_class_.__module__, spec_.module_path)
                self.assertEqual(executor_.execute(context_, command_), spec_.type_id)
                self.assertEqual(service_.call_count, 3)
                for call_ in service_.call_args_list:
                    self.assertIs(call_.kwargs["context"], context_)
                    self.assertIs(call_.kwargs["command"], command_)

    def test_active_instruction_modules_have_no_legacy_import_or_eval(self):
        forbidden_import_parts_ = ("old_ins", "导航窗口", "功能类")
        for path_ in INSTRUCTIONS_ROOT.rglob("*.py"):
            with self.subTest(path=str(path_.relative_to(PROJECT_ROOT))):
                source_ = path_.read_text(encoding="utf-8")
                tree_ = ast.parse(source_, filename=str(path_))

                for node_ in ast.walk(tree_):
                    self.assertFalse(isinstance(node_, ast.Call) and
                                     isinstance(node_.func, ast.Name) and
                                     node_.func.id == "eval")
                    if isinstance(node_, ast.Import):
                        import_names_ = [alias_.name for alias_ in node_.names]
                    elif isinstance(node_, ast.ImportFrom):
                        import_names_ = [node_.module or ""]
                    else:
                        continue
                    for import_name_ in import_names_:
                        self.assertFalse(
                            any(part_ in import_name_ for part_ in forbidden_import_parts_),
                            import_name_,
                        )


if __name__ == "__main__":
    unittest.main()
