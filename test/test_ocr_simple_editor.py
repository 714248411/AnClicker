import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PySide6.QtWidgets import QApplication
from instructions.registry import get_instruction_spec
from instructions.common.local_ocr_instruction import OCR_TYPES, fields_for
from instructions.models import InstructionDraft


@pytest.mark.parametrize('kind', OCR_TYPES)
def test_simplified_editor_preserves_all_parameters(kind):
    app = QApplication.instance() or QApplication([])
    values = {f.key: f.default for f in fields_for(kind)}
    if '区域' in values:
        values['区域'] = '10,20,300,200'
    if '目标文字' in values:
        values['目标文字'] = '测试'
    if '置信度' in values:
        values['置信度'] = .73
    editor = get_instruction_spec(kind).create_editor(draft=InstructionDraft(kind, values))
    try:
        assert not {'微信OCR路径', '微信运行目录', '微信接口目录'} & editor._controls.keys()
        assert editor.ocr_advanced_panel.isHidden()
        assert editor.get_draft().parameters == values
        editor.ocr_advanced_button.setChecked(True)
        assert not editor.ocr_advanced_panel.isHidden()
        editor.ocr_advanced_button.setChecked(False)
        assert editor.get_draft().parameters == values
        for index, field in enumerate(editor.FIELDS):
            container = getattr(editor.ui, f'parameterContainer_{index}')
            assert container.isAncestorOf(editor._controls[field.key])
            expected = editor.ocr_advanced_panel if field.key in editor._ocr_advanced_keys else editor.ui.parameterGroupBox
            assert expected.isAncestorOf(container)
    finally:
        editor.deleteLater()
        app.processEvents()
