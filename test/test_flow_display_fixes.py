import os
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest

from flow_condition_checks import condition_summary
from flow_condition_editor import ConditionPanel
from test.test_background_presets import app
from test.test_control_priority import Graph
from test.test_image_click_editor import editor
from test.test_hidden_stop import host


@pytest.mark.parametrize('path', [r'C:\images\截图.png', '/images/截图.png', '截图.png'])
def test_image_summary_uses_only_filename_and_condition(path):
    assert condition_summary({'判断类型': '图片存在', '图像路径': path,
                              '满足条件': '不存在 / 不相等'}) == '图片存在：截图.png'


@pytest.mark.parametrize('found', [False, True])
@pytest.mark.parametrize('direction', ['存在 / 相等', '不存在 / 不相等'])
def test_screen_image_existence_selects_corresponding_branch(tmp_path, found, direction):
    image = tmp_path / 'target.png'
    image.write_bytes(b'fixture')
    graph = Graph(tmp_path / 'graph.db')
    condition = graph.add('condition', '条件判断', 判断类型='图片存在',
                          图像路径=str(image), 满足条件=direction)
    yes, no = graph.add('yes'), graph.add('no')
    graph.link('start', condition)
    graph.link(condition, yes, 1)
    graph.link(condition, no, 2)
    with patch('instructions.common.actions.pyautogui_module'), \
         patch('instructions.common.image_match.best_image_match', return_value=(10, 20) if found else None):
        assert graph.run() == ['condition', 'yes' if found else 'no']


def test_saved_inverse_image_direction_is_normalized_in_editor(app):
    panel = ConditionPanel()
    try:
        panel.load({'判断类型': '图片存在', '图像路径': r'C:\images\target.png',
                    '满足条件': '不存在 / 不相等'})
        assert panel.parameters()['满足条件'] == '存在 / 相等'
        assert panel.rows['满足条件'].isHidden()
        assert panel.parameters()['图像路径'] == r'C:\images\target.png'
    finally:
        panel.deleteLater()


def test_switching_from_numeric_click_timeout_defaults_detection_to_one_second(editor):
    widget, _ = editor
    widget.skip_check.setChecked(False)
    widget.timeout_spin.setValue(10)
    widget.ui.parameter_1.setCurrentText('无操作')
    assert widget.get_draft().parameters['异常'] == '1'
    widget.timeout_spin.setValue(7)
    saved = widget.get_draft()
    widget.load_draft(saved)
    assert widget.get_draft().parameters['异常'] == '7'


def test_view_menu_checkboxes_control_and_follow_canvas_settings(host):
    menu = host.view_workspace.view_menu
    actions = {a.text(): a for a in menu.actions()}
    arrows = actions['流程图箭头动画']
    continuous = actions['流程图持续动画']
    view = host.workspace.editor.view
    assert arrows.isCheckable() and continuous.isCheckable()
    view.set_arrows_visible(True)
    arrows.trigger()
    assert not view.arrows_visible
    assert host.db.get_setting_value('流程图显示箭头') == 'False'
    arrows.trigger()
    continuous.trigger()
    assert view.arrows_visible and view.continuous_animation
    assert host.db.get_setting_value('流程图持续动画') == 'True'
    view.set_continuous_animation(False)
    assert not continuous.isChecked()
    with patch('node_editor.view.monotonic', return_value=100) as clock:
        view.play_run_animation()
        clock.return_value = 106
        view._advance_flow_arrows()
        menu.aboutToShow.emit()
        assert not arrows.isChecked()
        assert host.db.get_setting_value('流程图显示箭头') == 'True'
        arrows.trigger()
        assert view.arrows_visible
