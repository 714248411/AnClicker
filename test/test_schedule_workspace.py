import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
from qt_compat.QtCore import Qt, QDate, QDateTime, QPoint, QPointF, QEvent
from qt_compat.QtGui import QWheelEvent, QMouseEvent
from qt_compat.QtTest import QTest
from qt_compat.QtWidgets import QApplication

from test.test_hidden_stop import host
from test.test_project_call import project, mark
from test.test_schedule_project_drop import dialog
from scheduled_tasks import SETTING, TaskScheduler


def add_task(host, tmp_path, name='原任务', enabled=True):
    path = tmp_path / (name + '.xlsx')
    project(path, [mark(name)])
    return host.task_scheduler.add(dict(
        description=name, path=str(path), repeat='每天', enabled=enabled,
        next_run=(datetime.now() + timedelta(days=1)).isoformat(timespec='seconds'),
    ))


def wheel(field, delta):
    center = field.rect().center()
    event = QWheelEvent(QPointF(center), QPointF(field.mapToGlobal(center)), QPoint(),
                        QPoint(0, delta), Qt.NoButton, Qt.NoModifier, Qt.NoScrollPhase, False)
    QApplication.sendEvent(field, event)
    assert event.isAccepted()


def test_alarm_has_left_list_and_right_settings_with_two_line_description(dialog):
    assert dialog.sidebar.geometry().right() < dialog.editor_panel.geometry().left()
    assert dialog.new_button.text() == '＋  新建任务'
    assert dialog.enable_button.text() == '开启'
    assert dialog.disable_button.text() == '未开启'
    assert dialog.description.height() >= dialog.description.two_line_height()
    assert dialog.description.height() <= dialog.description.two_line_height() + 4
    height, top = dialog.height(), dialog.y()
    dialog.description.heightRequested.emit(dialog.description.height() + 40)
    assert dialog.height() >= height + 40
    assert dialog.y() == top
    dialog.description.heightRequested.emit(1)
    assert dialog.description.height() >= dialog.description.two_line_height()


def test_right_click_edit_saves_same_task_and_persists_enable_choice(dialog, host, tmp_path):
    task_id = add_task(host, tmp_path)
    dialog.entries.setCurrentRow(0)
    assert dialog._task_id == task_id and not dialog._editing
    assert dialog.description.toPlainText() == '原任务'
    assert not dialog.form_card.isEnabled()
    menu = dialog.build_task_menu(task_id)
    assert menu.actions()[0].text() == '编辑'
    menu.actions()[0].trigger()
    assert dialog._editing and dialog.form_card.isEnabled()
    dialog.description.setPlainText('修改后的任务')
    dialog.repeat.setCurrentText('每周')
    dialog.disable_button.click()
    assert host.task_scheduler.task_by_id(task_id)['description'] == '原任务'
    dialog.save_button.click()
    assert len(host.task_scheduler.tasks) == 1
    task = host.task_scheduler.task_by_id(task_id)
    assert task['description'] == '修改后的任务' and task['repeat'] == '每周'
    assert not task['enabled'] and task['id'] == task_id
    saved = json.loads(host.db.get_setting_value(SETTING))
    assert saved == host.task_scheduler.tasks
    assert not dialog._editing
    assert dialog.disable_button.isChecked() and not dialog.enable_button.isChecked()
    dialog.enable_button.click()
    assert task['enabled']
    assert dialog.enable_button.isChecked() and not dialog.disable_button.isChecked()
    card = dialog.entries.itemWidget(dialog.entries.currentItem())
    assert card.edit_button.isEnabled()
    card.edit_button.click()
    assert dialog._editing
    menu.deleteLater()


def test_task_card_edit_corner_targets_correct_task_after_filtering(dialog, host, tmp_path):
    add_task(host, tmp_path, '甲任务')
    second = add_task(host, tmp_path, '乙任务', enabled=False)
    dialog.search.setText('乙任务')
    QTest.qWait(20)
    card = dialog.entries.itemWidget(dialog.entries.item(0))
    assert card.edit_button.text() == '🖊'
    assert card.state_label.text() == '未开启'
    assert card.edit_button.geometry().right() < card.title_label.geometry().left()
    assert card.state_label.x() > card.details_label.x()
    assert card.edit_button.geometry().bottom() < card.state_label.geometry().top()
    card.edit_button.click()
    assert dialog._task_id == second and dialog._editing
    dialog.enable_button.click()
    dialog.save_button.click()
    card = dialog.entries.itemWidget(dialog.entries.item(0))
    assert card.state_label.text() == '开启'
    assert host.task_scheduler.task_by_id(second)['enabled']


def test_task_card_single_click_views_and_running_task_disables_edit(dialog, host, tmp_path):
    task_id = add_task(host, tmp_path)
    QTest.qWait(20)
    card = dialog.entries.itemWidget(dialog.entries.item(0))
    QTest.mouseClick(card, Qt.LeftButton, pos=card.title_label.geometry().center())
    assert dialog._task_id == task_id and not dialog._editing
    host.task_scheduler.active = dict(host.task_scheduler.task_by_id(task_id))
    try:
        dialog.refresh()
        card = dialog.entries.itemWidget(dialog.entries.item(0))
        assert not card.edit_button.isEnabled()
    finally:
        host.task_scheduler.active = None


def drag_window_edge(dialog, position, delta):
    start = dialog.mapToGlobal(position)
    QTest.mousePress(dialog, Qt.LeftButton, pos=position)
    assert dialog._resize_start is not None
    end = start + delta
    event = QMouseEvent(QEvent.MouseMove, QPointF(dialog.mapFromGlobal(end)), QPointF(end),
                        Qt.NoButton, Qt.LeftButton, Qt.NoModifier)
    QApplication.sendEvent(dialog, event)
    event = QMouseEvent(QEvent.MouseButtonRelease, QPointF(dialog.mapFromGlobal(end)), QPointF(end),
                        Qt.LeftButton, Qt.NoButton, Qt.NoModifier)
    QApplication.sendEvent(dialog, event)
    QTest.qWait(10)
    assert dialog._resize_start is None


@pytest.mark.parametrize('horizontal,vertical', [
    (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1),
])
def test_schedule_window_resizes_from_edges_and_corners(dialog, horizontal, vertical):
    original = dialog.geometry()
    position = QPoint(8 if horizontal < 0 else dialog.width()-9 if horizontal > 0 else dialog.width()//2,
                      8 if vertical < 0 else dialog.height()-9 if vertical > 0 else dialog.height()//2)
    drag_window_edge(dialog, position, QPoint(horizontal*30, vertical*25))
    assert dialog.width() == original.width() + abs(horizontal)*30
    assert dialog.height() == original.height() + abs(vertical)*25
    if horizontal < 0:
        assert dialog.geometry().right() == original.right()
    if vertical < 0:
        assert dialog.geometry().bottom() == original.bottom()
    assert dialog.enable_button.isVisible() and dialog.disable_button.isVisible()


def test_window_resize_respects_minimum_and_keeps_calendar_button_centered(dialog):
    minimum = dialog.minimumSize().expandedTo(dialog.minimumSizeHint())
    drag_window_edge(dialog, QPoint(dialog.width()-8, dialog.height()-8), QPoint(-1000, -1000))
    assert dialog.width() >= minimum.width() and dialog.height() >= minimum.height()
    edit = dialog.when
    assert abs(edit.calendar_button.geometry().center().y() - edit.rect().center().y()) <= 1
    assert edit.rect().contains(edit.calendar_button.geometry())
    edit.calendar_button.click()
    assert edit.calendar_popup.isVisible()
    edit.calendar_popup.hide()


def test_new_disabled_task_can_be_saved_without_running(dialog, host, tmp_path):
    path = tmp_path / '稍后启用.xlsx'
    project(path, [mark('not-run')])
    dialog.path.setText(str(path))
    dialog.when.setDateTime(QDateTime.currentDateTime().addSecs(-60))
    dialog.disable_button.click()
    assert not host.task_scheduler.tasks
    dialog.save_button.click()
    task = host.task_scheduler.tasks[0]
    assert not task['enabled']
    host.task_scheduler.tick()
    assert not host.task_scheduler.busy
    dialog.new_button.click()
    assert dialog._task_id is None and not dialog.path.text()
    assert dialog.form_card.isEnabled()


def test_active_task_cannot_be_edited_or_deleted(dialog, host, tmp_path):
    task_id = add_task(host, tmp_path)
    host.task_scheduler.active = dict(host.task_scheduler.task_by_id(task_id))
    try:
        menu = dialog.build_task_menu(task_id)
        assert not menu.actions()[0].isEnabled()
        assert not menu.actions()[-1].isEnabled()
        with pytest.raises(ValueError, match='正在执行'):
            host.task_scheduler.update_task(task_id, dict(description='bad'))
        with pytest.raises(ValueError, match='先结束'):
            host.task_scheduler.remove_task(task_id)
        assert host.task_scheduler.task_by_id(task_id)['description'] == '原任务'
        menu.deleteLater()
    finally:
        host.task_scheduler.active = None


@pytest.mark.parametrize('operation', ['edit', 'disable', 'delete'])
def test_changing_pending_task_removes_old_queued_occurrence(dialog, host, tmp_path, operation):
    task_id = add_task(host, tmp_path)
    scheduler = host.task_scheduler
    scheduler.queue.append(dict(scheduler.task_by_id(task_id)))
    if operation == 'edit':
        scheduler.update_task(task_id, dict(description='新的设置'))
    elif operation == 'disable':
        scheduler.set_enabled(task_id, False)
    else:
        scheduler.remove_task(task_id)
    assert not scheduler.queue


def test_failed_edit_preserves_task_and_queue(dialog, host, tmp_path):
    task_id = add_task(host, tmp_path)
    scheduler = host.task_scheduler
    original = dict(scheduler.task_by_id(task_id))
    scheduler.queue.append(dict(original))
    with pytest.raises(ValueError):
        scheduler.update_task(task_id, dict(path=str(tmp_path / 'missing.xlsx')))
    assert scheduler.task_by_id(task_id) == original
    assert scheduler.queue == [original]


def test_filter_and_scheduler_refresh_keep_unsaved_editor_fields(dialog, host, tmp_path):
    first = add_task(host, tmp_path, '甲任务')
    second = add_task(host, tmp_path, '乙任务')
    dialog.load_task(second, editable=True)
    dialog.description.setPlainText('还没有保存的修改')
    dialog.search.setText('甲任务')
    assert dialog.entries.count() == 1
    assert dialog.entries.item(0).data(Qt.UserRole) == first
    host.task_scheduler.save()
    assert dialog._task_id == second
    assert dialog.description.toPlainText() == '还没有保存的修改'


@pytest.mark.parametrize('surface', ['description', 'path', 'time', 'repeat', 'form', 'blank', 'advanced'])
def test_details_single_click_is_read_only_double_click_unlocks(dialog, host, tmp_path, surface):
    task_id = add_task(host, tmp_path)
    dialog.load_task(task_id)
    if surface == 'advanced':
        dialog.advanced_button.click()
        QTest.qWait(20)
    widget = {
        'description': dialog.description.viewport(), 'path': dialog.path,
        'time': dialog.when.sections['年'], 'repeat': dialog.repeat,
        'form': dialog.form_card, 'blank': dialog.editor_panel,
        'advanced': dialog.advanced_details,
    }[surface]
    position = QPoint(2, 2) if surface in ('form', 'blank') else widget.rect().center()
    original = dict(host.task_scheduler.task_by_id(task_id))
    QTest.mouseClick(widget, Qt.LeftButton, pos=position)
    assert not dialog._editing and not dialog.save_button.isEnabled()
    assert dialog.description.isReadOnly() and not dialog.form_card.isEnabled()
    QTest.mouseDClick(widget, Qt.LeftButton, pos=position)
    assert dialog._editing and dialog.save_button.isEnabled()
    assert not dialog.description.isReadOnly() and dialog.form_card.isEnabled()
    assert host.task_scheduler.task_by_id(task_id) == original
    card = dialog.entries.itemWidget(dialog.entries.currentItem())
    assert card.edit_button.property('editing')


def test_edit_pen_changes_color_and_save_restores_read_only(dialog, host, tmp_path):
    task_id = add_task(host, tmp_path)
    dialog.load_task(task_id)
    card = dialog.entries.itemWidget(dialog.entries.currentItem())
    idle_icon = card.edit_button.icon().pixmap(16, 16).toImage()
    assert not card.edit_button.property('editing')
    card.edit_button.click()
    editing_icon = card.edit_button.icon().pixmap(16, 16).toImage()
    assert editing_icon != idle_icon
    dialog.description.setPlainText('已保存的编辑')
    card.edit_button.click()
    assert dialog.description.toPlainText() == '已保存的编辑'
    host.task_scheduler.save()
    card = dialog.entries.itemWidget(dialog.entries.currentItem())
    assert card.edit_button.property('editing')
    dialog.save_button.click()
    assert host.task_scheduler.task_by_id(task_id)['description'] == '已保存的编辑'
    assert not dialog._editing and not dialog.save_button.isEnabled()
    card = dialog.entries.itemWidget(dialog.entries.currentItem())
    assert not card.edit_button.property('editing')
    assert card.edit_button.icon().pixmap(16, 16).toImage() == idle_icon


def test_invalid_save_keeps_edit_mode_and_draft(dialog, host, tmp_path, monkeypatch):
    import scheduled_tasks_ui as module
    task_id = add_task(host, tmp_path)
    original = dict(host.task_scheduler.task_by_id(task_id))
    dialog.load_task(task_id, editable=True)
    dialog.path.setText(str(tmp_path / '不存在.xlsx'))
    dialog.disable_button.click()
    warning = Mock()
    monkeypatch.setattr(module.QMessageBox, 'warning', warning)
    dialog.save_button.click()
    warning.assert_called_once()
    assert dialog._editing and dialog.disable_button.isChecked()
    assert dialog.path.text().endswith('不存在.xlsx')
    assert host.task_scheduler.task_by_id(task_id) == original


def test_running_details_cannot_unlock_by_double_click(dialog, host, tmp_path, monkeypatch):
    import scheduled_tasks_ui as module
    task_id = add_task(host, tmp_path)
    dialog.load_task(task_id)
    host.task_scheduler.active = dict(host.task_scheduler.task_by_id(task_id))
    info = Mock()
    monkeypatch.setattr(module.QMessageBox, 'information', info)
    try:
        QTest.mouseDClick(dialog.description.viewport(), Qt.LeftButton)
        info.assert_called_once()
        assert not dialog._editing and not dialog.save_button.isEnabled()
    finally:
        host.task_scheduler.active = None


def test_switching_tasks_returns_details_to_read_only(dialog, host, tmp_path):
    first = add_task(host, tmp_path, '甲任务')
    second = add_task(host, tmp_path, '乙任务')
    dialog.load_task(first, editable=True)
    dialog.load_task(second)
    assert not dialog._editing
    for index in range(dialog.entries.count()):
        assert not dialog.entries.itemWidget(dialog.entries.item(index)).edit_button.property('editing')


@pytest.mark.parametrize('section', ['年', '月', '日', '时', '分', '秒'])
def test_time_single_click_selects_whole_section_then_click_allows_typing(dialog, section):
    edit = dialog.when
    edit.setDateTime(QDateTime.fromString('2028-10-13T12:34:56', Qt.ISODate))
    dialog.description.setFocus()
    field = edit.sections[section]
    QTest.mouseClick(field, Qt.LeftButton)
    assert field.selectedText() == field.text()
    QTest.mouseClick(field, Qt.LeftButton)
    assert not field.hasSelectedText()
    field.selectAll()
    QTest.keyClicks(field, '2029' if section == '年' else '11')
    QTest.keyClick(field, Qt.Key_Tab)
    assert field.text() == ('2029' if section == '年' else '11')
    assert edit.dateTime().isValid()


@pytest.mark.parametrize('section,expected', [
    ('年', '2027-10-13T12:30:40'), ('月', '2026-11-13T12:30:40'),
    ('日', '2026-10-14T12:30:40'), ('时', '2026-10-13T13:30:40'),
    ('分', '2026-10-13T12:31:40'), ('秒', '2026-10-13T12:30:41'),
])
def test_time_wheel_down_increases_and_up_decreases(dialog, section, expected):
    start = QDateTime.fromString('2026-10-13T12:30:40', Qt.ISODate)
    dialog.when.setDateTime(start)
    field = dialog.when.sections[section]
    wheel(field, -120)
    assert dialog.when.dateTime().toString(Qt.ISODate) == expected
    wheel(field, 120)
    assert dialog.when.dateTime() == start


def test_time_handles_leap_days_rollover_and_high_resolution_wheel(dialog):
    edit = dialog.when
    edit.setDateTime(QDateTime.fromString('2028-02-29T23:59:59', Qt.ISODate))
    wheel(edit.sections['年'], -120)
    assert edit.dateTime().toString(Qt.ISODate) == '2029-02-28T23:59:59'
    wheel(edit.sections['秒'], -60)
    assert edit.dateTime().time().second() == 59
    wheel(edit.sections['秒'], -60)
    assert edit.dateTime().toString(Qt.ISODate) == '2029-03-01T00:00:00'
    edit.sections['月'].setText('00')
    edit.commit(edit.sections['月'])
    assert edit.sections['月'].text() == '03'
    edit.setDateTime(QDateTime.fromString('2026-01-31T12:00:00', Qt.ISODate))
    edit.sections['月'].setText('2')
    edit.commit(edit.sections['月'])
    assert edit.dateTime().date().day() == 28


@pytest.mark.parametrize('section,typed,index,replacement,expected', [
    ('年', '2032', 2, '4', '2042'), ('秒', '12', 1, '9', '19'),
])
def test_first_click_types_from_left_second_click_overwrites_at_clicked_digit(
        dialog, section, typed, index, replacement, expected):
    dialog.description.setFocus()
    field = dialog.when.sections[section]
    QTest.mouseClick(field, Qt.LeftButton)
    assert field.selectedText() == field.text()
    QTest.keyClicks(field, typed)
    assert field.text() == typed and field.cursorPosition() == len(typed)
    point = next(QPoint(x, field.height() // 2) for x in range(field.width())
                 if field.cursorPositionAt(QPoint(x, field.height() // 2)) == index)
    QTest.mouseClick(field, Qt.LeftButton, pos=point)
    assert field.cursorPosition() == index and not field.hasSelectedText()
    QTest.keyClicks(field, replacement)
    assert field.text() == expected


def test_time_refresh_symbol_fills_current_time_without_saving_task(dialog, host):
    edit = dialog.when
    edit.setDateTime(QDateTime.fromString('2040-01-01T00:00:00', Qt.ISODate))
    assert edit.refresh_button.text() == '↻'
    assert edit.refresh_button.toolTip() == '刷新为当前时间'
    before = QDateTime.currentDateTime()
    edit.refresh_button.click()
    after = QDateTime.currentDateTime()
    assert before <= edit.dateTime() <= after
    assert not host.task_scheduler.tasks
    assert edit.rect().contains(edit.refresh_button.geometry())


def test_calendar_dropdown_selects_date_and_preserves_time(dialog):
    edit = dialog.when
    edit.setDateTime(QDateTime.fromString('2028-10-13T12:34:56', Qt.ISODate))
    edit.calendar_button.click()
    QTest.qWait(20)
    assert edit.calendar_popup.isVisible()
    assert edit.calendar.selectedDate() == QDate(2028, 10, 13)
    assert edit.calendar.firstDayOfWeek() == Qt.Monday
    edit.calendar.clicked.emit(QDate(2028, 11, 25))
    assert not edit.calendar_popup.isVisible()
    assert edit.dateTime().toString(Qt.ISODate) == '2028-11-25T12:34:56'
    edit.calendar_button.click()
    assert edit.calendar.selectedDate() == QDate(2028, 11, 25)
    QTest.keyClick(edit.calendar_popup, Qt.Key_Escape)
    assert not edit.calendar_popup.isVisible()
    assert edit.dateTime().toString(Qt.ISODate) == '2028-11-25T12:34:56'


def test_calendar_closes_with_parent_and_stays_inside_screen(dialog):
    edit = dialog.when
    available = dialog.screen().availableGeometry()
    dialog.move(available.right() - dialog.width(), available.bottom() - dialog.height())
    edit.calendar_button.click()
    QTest.qWait(20)
    assert available.contains(edit.calendar_popup.frameGeometry())
    dialog.reject()
    assert not edit.calendar_popup.isVisible()


@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_schedule_two_pane_theme_layout(host, tmp_path, theme):
    host.task_scheduler.timer.stop()
    task_id = add_task(host, tmp_path, '网页和表格自动运行')
    host.view_workspace.theme_mode = theme
    host.view_workspace._apply_theme()
    host.task_scheduler.show_settings()
    panel = host.task_scheduler.dialog
    panel.load_task(task_id, editable=True)
    panel.resize(960, 500)
    QTest.qWait(30)
    panel.description.setFocus()
    QTest.mouseClick(panel.when.sections['年'], Qt.LeftButton)
    for field in panel.when.sections.values():
        assert field.isVisible() and panel.when.rect().contains(field.geometry())
    assert panel.description.height() >= panel.description.two_line_height()
    root = Path('validation/schedule-workspace-ui')
    root.mkdir(parents=True, exist_ok=True)
    panel.grab().save(str(root / (theme + '.png')))
    editing_color = panel.editor_panel.grab().toImage().pixelColor(panel.editor_panel.width() // 2, panel.editor_panel.height() - 25)
    sidebar_color = panel.sidebar.grab().toImage().pixelColor(panel.sidebar.width() // 2, panel.sidebar.height() - 25)
    assert editing_color == sidebar_color
    assert abs(panel.advanced_button.mapTo(panel.editor_panel, panel.advanced_button.rect().center()).y() -
               panel.save_button.mapTo(panel.editor_panel, panel.save_button.rect().center()).y()) <= 1
    assert panel.save_button.mapTo(panel.editor_panel, panel.save_button.rect().topRight()).x() == panel.editor_panel.width() - 9
    panel.save_button.click()
    assert not panel._editing
    QTest.qWait(10)
    panel.grab().save(str(root / (theme + '-readonly.png')))
    readonly_color = panel.editor_panel.grab().toImage().pixelColor(panel.editor_panel.width() // 2, panel.editor_panel.height() - 25)
    assert readonly_color != editing_color
    panel.load_task(task_id, editable=True)
    panel.when.calendar_button.click()
    QTest.qWait(30)
    panel.when.calendar_popup.grab().save(str(root / (theme + '-calendar.png')))
    panel.when.calendar_popup.hide()
    panel.resize(760, panel.height())
    QTest.qWait(20)
    assert panel.enable_button.isVisible() and panel.disable_button.isVisible()
    for field in panel.when.sections.values():
        assert panel.when.rect().contains(field.geometry())
    panel.reject()
