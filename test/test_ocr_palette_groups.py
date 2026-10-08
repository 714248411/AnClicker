import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from qt_compat.QtWidgets import QApplication
from instructions.registry import INSTRUCTION_SPECS
from instructions.common.local_ocr_instruction import OCR_TYPES
from node_editor.palette import InstructionPalette, TYPE_ID_ROLE


def test_online_and_offline_ocr_are_separate_searchable_groups():
    app = QApplication.instance() or QApplication([])
    palette = InstructionPalette(INSTRUCTION_SPECS)
    groups = {palette.tree.topLevelItem(i).text(0): palette.tree.topLevelItem(i)
              for i in range(palette.tree.topLevelItemCount())}
    def ids(group):
        return {group.child(i).data(0, TYPE_ID_ROLE) for i in range(group.childCount())}
    assert ids(groups['离线OCR']) == set(OCR_TYPES)
    assert '离线OCR · 常用操作' not in groups
    shortcuts = groups['离线OCR']
    assert shortcuts.childCount() == len(OCR_TYPES)
    assert [shortcuts.child(i).text(0) for i in range(4)] == [
        'OCR文字提取', 'OCR复制', 'OCR粘贴', 'OCR点击']
    assert shortcuts.child(3).data(0, TYPE_ID_ROLE) == 'OCR点击识别区域'
    activated = []
    palette.instructionActivated.connect(activated.append)
    palette.tree.itemDoubleClicked.emit(shortcuts.child(3), 0)
    assert activated == ['OCR点击识别区域']
    assert ids(groups['OCR']) == {'OCR识别'}
    assert 'OCR识别' not in ids(groups['获取变量'])
    assert '本地OCR' not in groups
    palette.search_edit.setText('离线OCR')
    assert not groups['离线OCR'].isHidden()
    assert groups['OCR'].isHidden()
    palette.search_edit.setText('OCR识别')
    assert not groups['OCR'].isHidden()
    palette.close()


def test_quick_capture_is_first_directory_action_and_click_is_draggable():
    app = QApplication.instance() or QApplication([])
    palette = InstructionPalette(INSTRUCTION_SPECS)
    group = palette.tree.topLevelItem(0)
    assert group.text(0) == '快捷功能栏'
    called = []
    palette.quickCaptureRequested.connect(lambda: called.append(True))
    palette.tree.itemClicked.emit(group.child(0), 0)
    assert called == [True]
    assert group.child(0).data(0, TYPE_ID_ROLE) is None
    palette.show_recent_capture('example.png')
    assert group.child(1).text(0) == '快捷截图（OCR）'
    assert group.child(2).text(0) == '点击快捷截图'
    assert group.child(2).data(0, TYPE_ID_ROLE) == '图像点击'
    palette.close()
