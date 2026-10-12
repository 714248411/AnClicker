"""Legacy image-wait import, editor and interruptible execution semantics."""
import os
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import pytest
from qt_compat.QtWidgets import QApplication
from openpyxl import Workbook
from graph_repository import GraphRepository
from legacy_workbook import LEGACY_HEADERS
from instructions.models import InstructionDraft, CommandRecord, ExecutionContext
from instructions.registry import get_instruction_spec
from instructions.common import actions
from 数据库操作 import DatabaseOperation


def parameters(mode):
    return {'图像路径': 'target.png', '等待类型': mode, '超时时间': 2,
            '区域': '(0,0,0,0)', '精度': .8}


def execute(values, ctx=None):
    return get_instruction_spec('图像等待').create_executor().execute(
        ctx or ExecutionContext(), CommandRecord(id=1, type_id='图像等待', parameters=values))


@pytest.mark.parametrize('old,new,timeout', [
    ('等待到指定图像出现', '等待出现', 2), ('等待到指定图像消失', '等待消失', 0)])
def test_legacy_import_and_editor_preserve_semantics(tmp_path, old, new, timeout):
    app = QApplication.instance() or QApplication([])
    book = Workbook()
    book.active.append(LEGACY_HEADERS)
    values = parameters(old)
    values.pop('图像路径')
    book.active.append([1, 'target.png', '图像等待', str(values), None, None, None, 1, '自动跳过', ''])
    database = DatabaseOperation(str(tmp_path / 'import.db'))
    repo = GraphRepository(database.db_path)
    repo.import_from_workbook(book)
    converted = repo.list_commands()[0].parameters
    assert converted['等待类型'] == new
    assert converted['超时时间'] == timeout
    assert converted['区域'] == ''
    editor = get_instruction_spec('图像等待').create_editor(
        draft=InstructionDraft('图像等待', parameters(old)))
    try:
        assert editor.get_draft().parameters == converted
    finally:
        editor.close()
        editor.deleteLater()
        app.processEvents()
        book.close()


@pytest.mark.parametrize('mode,found,expected', [
    ('等待到指定图像出现', [None, object()], True),
    ('等待到指定图像消失', [object(), None], False),
    ('等待出现', [None, object()], True),
    ('等待消失', [object(), None], False)])
def test_wait_modes_actually_poll(mode, found, expected):
    with patch('os.path.isfile', return_value=True), \
            patch.object(actions, 'locate_image', side_effect=found) as locate, \
            patch.object(actions, 'wait_seconds'):
        assert execute(parameters(mode)) is expected
    assert locate.call_count == 2


def test_appearance_timeout_is_not_silently_successful():
    with patch('os.path.isfile', return_value=True), \
            patch.object(actions, 'locate_image', return_value=None), \
            patch('time.monotonic', side_effect=[0, 3]):
        with pytest.raises(TimeoutError):
            execute(parameters('等待到指定图像出现'))


def test_unlimited_wait_can_stop_and_does_not_complete():
    ctx = ExecutionContext()
    messages = []
    ctx.output = messages.append
    def stop(delay):
        ctx.stop_requested = True
    values = dict(parameters('等待出现'), 超时时间=0)
    with patch('os.path.isfile', return_value=True), \
            patch.object(actions, 'locate_image', return_value=None) as locate, \
            patch.object(actions, 'wait_seconds', side_effect=stop):
        assert execute(values, ctx) is None
    assert locate.call_count == 1
    assert '图像等待完成' not in messages


def test_already_stopped_never_captures_screen():
    with patch.object(actions, 'locate_image') as locate:
        assert execute(parameters('等待出现'), ExecutionContext(stop_requested=True)) is None
    locate.assert_not_called()


def test_missing_file_is_not_interpreted_as_image_disappearance():
    with patch('os.path.isfile', return_value=False), patch.object(actions, 'locate_image') as locate:
        with pytest.raises(FileNotFoundError):
            execute(parameters('等待消失'))
    locate.assert_not_called()


def test_unlimited_editor_test_does_not_block_gui_thread():
    app = QApplication.instance() or QApplication([])
    editor = get_instruction_spec('图像等待').create_editor(
        draft=InstructionDraft('图像等待', dict(parameters('等待出现'), 超时时间=0)))
    requested = []
    editor.test_requested.connect(requested.append)
    try:
        with patch('qt_compat.QtWidgets.QMessageBox.information') as message:
            editor._test_if_valid()
        message.assert_called_once()
        assert requested == []
    finally:
        editor.close()
        editor.deleteLater()
        app.processEvents()
