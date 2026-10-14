import json
from qt_compat.QtWidgets import QApplication, QToolButton
from qt_compat.QtTest import QTest
from test.test_hidden_stop import host
from view_workspace import FLOW_VIEW, TABLE_VIEW, CODE_VIEW
from toolbar_customization import SETTING


def test_toolbar_cycle_and_labels(host):
    view = host.view_workspace
    actions = host.toolBar.actions()
    assert view.code_action not in actions
    assert view.palette_side_action not in actions
    view.show_main()
    for index, label in [(FLOW_VIEW, '打开表格图'), (TABLE_VIEW, '打开多功能'), (CODE_VIEW, '打开流程图'), (FLOW_VIEW, '打开表格图')]:
        view.primary_action.trigger()
        assert view.tabs.currentIndex() == index
        assert view.primary_action.text() == label
    view.controls_action.setChecked(False)
    assert view.controls_action.text() == '展开控制栏'
    view.controls_action.setChecked(True)
    assert view.controls_action.text() == '收起控制栏'


def test_custom_toolbar_callbacks_and_persistence(host):
    custom = host.view_workspace.toolbar_customization
    custom.sync()
    assert {'文件', '界面方案', '视图', '界面字号', '工具'} <= {labels[0] for _, labels in custom.sources.values()}
    assert any(action.text() == '检查更新' for action, _ in custom.sources.values())
    key = next(k for k, (a, _) in custom.sources.items() if a.text() == '表格图')
    custom.select(key, True)
    assert json.loads(host.db.get_setting_value(SETTING)) == [key]
    custom.proxies[key].trigger()
    assert host.view_workspace.tabs.currentIndex() == TABLE_VIEW
    assert custom.proxies[key].text() == custom.sources[key][0].text()
    custom.sync()
    custom.sync()
    QTest.qWait(30)
    button = host.toolBar.widgetForAction(custom.proxies[key])
    assert button.isVisible()
    assert button.text() == custom.sources[key][0].text()
    assert host.toolBar.actions()[-1] == custom.add_action
    custom.select(key, False)
    assert key not in custom.proxies
    assert json.loads(host.db.get_setting_value(SETTING)) == []


def test_rebuilt_layout_action_and_overflow(host):
    custom = host.view_workspace.toolbar_customization
    presets = host.view_workspace.layout_presets
    presets.save()
    custom.sync()
    key = next(k for k in custom.sources if 'layout-preset-' in k)
    custom.select(key, True)
    presets.current()['name'] = '测试布局名称'
    presets.refresh()
    QTest.qWait(20)
    assert custom.proxies[key].text() == '测试布局名称'
    custom.proxies[key].trigger()
    assert presets.current()['name'] == '测试布局名称'
    for k in list(custom.sources):
        custom.select(k, True)
    host.resize(900, 700)
    QTest.qWait(80)
    extension = host.toolBar.findChild(QToolButton, 'qt_toolbar_ext_button')
    assert extension and extension.isVisible()
    assert host.toolBar.width() <= host.width()
    assert any(not host.toolBar.widgetForAction(a).isVisible() for a in custom.proxies.values())
    presets.delete()
    QTest.qWait(20)
    assert key not in custom.proxies
