import pytest
from instruction_code import parse_instruction_code
from instructions.models import InstructionDraft
from instructions.registry import iter_instruction_specs
from graph_repository import GraphRepository
from 数据库操作 import DatabaseOperation


def test_all_templates_round_trip_and_fill_missing_fields():
    from instruction_guidance import command_template, Suggestion
    for spec in iter_instruction_specs():
        template = command_template(Suggestion(spec.display_name, spec.type_id))
        full = parse_instruction_code(template)[0][1]
        default = parse_instruction_code(spec.type_id + '()')[0][1]
        assert full.parameters == default.parameters


def test_json_literals_comments_and_parenthesized_names():
    entry = parse_instruction_code('# [1] #42 test\n时间等待({"时长": 5, "变量": true, "文本": "null # false"}) # 保留备注')[0]
    assert entry[0] == 42
    assert entry[1].parameters['变量'] is True
    assert entry[1].parameters['文本'] == 'null # false'
    assert entry[1].note == '保留备注'
    assert entry[1].parameters['单位'] == '秒'


@pytest.mark.parametrize('text', ['时间等待(__import__("os").system("bad"))', '时间等待({}, 重复次数=0)', '时间等待({}, 重复次数=True)', '时间等待({}, 未知=1)', '未知指令()', '时间等待({})\nimport os'])
def test_bad_code_rejected(text):
    with pytest.raises(ValueError, match='第 '):
        parse_instruction_code(text)


def test_atomic_write_preserves_ids_links_and_table_editing(tmp_path):
    database = DatabaseOperation(str(tmp_path / 'test.db'))
    repository = GraphRepository(database.db_path)
    ids = repository.write_instruction_code(parse_instruction_code('时间等待()\n坐标点击()'))
    before = repository.snapshot()
    entries = parse_instruction_code(f'# [1] #{ids[0]} wait\n时间等待({{"时长": 8}})\n# [2] #{ids[1]} click\n坐标点击()')
    assert repository.write_instruction_code(entries) == ids
    assert repository.snapshot().edges == before.edges
    assert repository.list_commands()[0].parameters['时长'] == 8
    repository.update_command_note(ids[0], '表格修改')
    assert repository.list_commands()[0].note == '表格修改'
    before = repository.snapshot()
    with pytest.raises(ValueError):
        repository.write_instruction_code([entries[0], entries[0]])
    assert repository.snapshot() == before
    repository.write_instruction_code(parse_instruction_code('时间等待({"时长": 1})'))
    assert len(repository.list_commands()) == 1
    repository.validate_graph()


def test_real_multifunction_button_fills_table_and_flow(tmp_path):
    from unittest.mock import Mock, patch
    from qt_compat.QtWidgets import QApplication
    from Start_Win import Main_window
    app = QApplication.instance() or QApplication([])
    database = DatabaseOperation(str(tmp_path / 'ui.db'))
    with patch('Start_Win.DatabaseOperation', return_value=database), patch('main_work.DatabaseOperation', return_value=database), patch('Start_Win.SystemHotkey', return_value=Mock()), patch('Start_Win.is_hotkey_valid', return_value=True):
        window = Main_window()
    view = window.view_workspace
    view.show_code()
    view.code_editor.setPlainText('时间等待({"时长": 3})\n打开网页({"url": "https://www.hao123.com"})')
    original_text = view.code_editor.toPlainText()
    with patch('instruction_conversion_dialog.InstructionConversionDialog.exec', return_value=0):
        view.write_code_button.click()
    assert window.workspace.repository.list_commands() == []
    assert view.code_editor.toPlainText() == original_text
    with patch('instruction_conversion_dialog.InstructionConversionDialog.exec', return_value=1):
        view.write_code_button.click()
    assert view.command_table.rowCount() == 2
    assert window.workspace.repository.list_commands()[0].parameters['单位'] == '秒'
    window.workspace.repository.validate_graph()
    ids = [c.id for c in window.workspace.repository.list_commands()]
    with patch('instruction_conversion_dialog.InstructionConversionDialog.exec', return_value=1):
        view.write_code_button.click()
    assert [c.id for c in window.workspace.repository.list_commands()] == ids
    window.close()
    window.deleteLater()


def test_conversion_reports_positions_and_completes_missing_values():
    from instruction_code import prepare_instruction_conversion
    plan = prepare_instruction_conversion('时间等待({"时长":\n坐标点击()')
    assert not plan.errors
    assert len(plan.entries) == 2
    assert plan.entries[0][1].parameters['时长'] == 1
    assert any('第 1 行，第 11 个字符后' in item for item in plan.notices)
    assert any('第 2 行' in item for item in plan.notices)
    plan = prepare_instruction_conversion('文本输入({"文本": "a:} b=)"})')
    assert not plan.errors
    assert plan.entries[0][1].parameters['文本'] == 'a:} b=)'


def test_conversion_dialog_top_buttons_and_cancel_preserve_flow(tmp_path):
    from qt_compat.QtWidgets import QApplication
    from instruction_conversion_dialog import InstructionConversionDialog
    from instruction_code import prepare_instruction_conversion
    app = QApplication.instance() or QApplication([])
    plan = prepare_instruction_conversion('时间等待(')
    dialog = InstructionConversionDialog(plan)
    dialog.show()
    app.processEvents()
    assert dialog.convert_button.text() == '继续转换'
    assert dialog.cancel_button.text() == '不转换'
    assert dialog.convert_button.y() == dialog.cancel_button.y()
    assert dialog.details.y() > dialog.convert_button.y()
    assert dialog.convert_button.isEnabled()
    dialog.cancel_button.click()
    assert dialog.result() == 0
    assert '第 1 行' in dialog.details.toPlainText()


def test_unresolved_targets_skip_until_saved_in_table_editor():
    from unittest.mock import Mock, patch
    from instruction_code import prepare_instruction_conversion
    from instructions.models import CommandRecord, ExecutionContext
    from main_work import CommandThread
    from qt_compat.QtWidgets import QApplication
    from instructions.registry import get_instruction_spec
    app = QApplication.instance() or QApplication([])
    plan = prepare_instruction_conversion('打开网页()')
    draft = plan.entries[0][1]
    assert draft.parameters['_待补充参数'] == ['网页地址']
    host = Mock()
    with patch('main_work.get_instruction_spec') as resolve:
        assert CommandThread._execute_one(host, CommandRecord(None, draft.type_id, draft.parameters), ExecutionContext()) is None
        resolve.assert_not_called()
    editor = get_instruction_spec('打开网页').create_editor(draft=draft)
    editor._controls['url'].setText('https://www.hao123.com')
    assert '_待补充参数' not in editor.get_draft().parameters
    editor.close()
