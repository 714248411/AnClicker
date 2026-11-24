"""Exercise the real popup layout, opacity, actions and dismissal."""
import os
import sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import QEvent, QPoint, QPointF, QTimer, Qt
from anclicker.platform.qt_compat.QtGui import QMouseEvent, QFontDatabase, QFont
from anclicker.platform.qt_compat.QtWidgets import QApplication, QMenu, QWidget
from anclicker.ui.context_menu_style import style_context_menu
from anclicker.ui.two_column_menu import MenuColumn, TwoColumnMenu

app = QApplication.instance() or QApplication([])
font_id = QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
families = QFontDatabase.applicationFontFamilies(font_id)
if families: app.setFont(QFont(families[0], 10))
owner = QWidget()
owner.resize(900, 700)
owner.show()
errors = []
def later(callback):
    def checked():
        try:
            callback()
        except BaseException as error:
            errors.append(error)
            popup.close()
    QTimer.singleShot(60, checked)
def build():
    left, right = MenuColumn(owner), MenuColumn(owner)
    for index in range(10):
        left.addAction('操作 %s' % index)
    right._submenus = []
    for index in range(15):
        sub = right.addMenu('指令分类 %s' % index)
        right._submenus.append(sub)
        sub.addAction('插入指令 %s' % index)
    style_context_menu(left, owner)
    style_context_menu(right, owner)
    return TwoColumnMenu(left, right, owner)
popup = build()
def check_right_click():
    left, right = popup.columns
    assert left.isVisible() and right.isVisible()
    assert left.geometry().right() < right.geometry().left()
    assert left.y() == right.y()
    QApplication.sendEvent(right, QEvent(QEvent.Enter))
    assert [m.column_opacity for m in popup.columns] == [.2, 1.0]
    sub = right._submenus[0]
    sub.popup(right.mapToGlobal(QPoint(right.width(), 10)))
    assert not sub.geometry().intersects(popup.geometry()), "Submenu covers another column despite available room"
    QApplication.sendEvent(sub, QEvent(QEvent.Enter))
    assert [m.column_opacity for m in popup.columns] == [.2, 1.0]
    out = Path('artifacts/validation/two-column-menu-v2.png')
    out.parent.mkdir(parents=True, exist_ok=True)
    popup.grab().save(str(out))
    for kind in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
        QApplication.sendEvent(sub, QMouseEvent(kind, QPointF(10, 10), Qt.RightButton, Qt.RightButton if kind == QEvent.MouseButtonPress else Qt.NoButton, Qt.NoModifier))
    assert not popup.isVisible() and not sub.isVisible()
later(check_right_click)
assert popup.exec(QPoint(700, 600)) is None
if errors: raise errors[0]
print('PASS two columns, hover opacity, submenu ownership, right-click closes entire popup')
popup.deleteLater()
popup = build()
action = popup.columns[1]._submenus[1].actions()[0]
def click_instruction():
    sub = popup.columns[1]._submenus[1]
    sub.popup(popup.mapToGlobal(QPoint(popup.width(), 10)))
    location = QPointF(sub.actionGeometry(action).center())
    QApplication.sendEvent(sub, QMouseEvent(QEvent.MouseMove, location, QPointF(sub.mapToGlobal(location.toPoint())), Qt.NoButton, Qt.NoButton, Qt.NoModifier))
    for kind in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
        QApplication.sendEvent(sub, QMouseEvent(kind, location, QPointF(sub.mapToGlobal(location.toPoint())), Qt.LeftButton,
            Qt.LeftButton if kind == QEvent.MouseButtonPress else Qt.NoButton, Qt.NoModifier))
    QTimer.singleShot(100, popup.close)
later(click_instruction)
assert popup.exec(QPoint(100, 100)) == action
if errors: raise errors[0]
print('PASS submenu insertion action returned')
popup.deleteLater()
popup = build()
later(lambda: QApplication.sendEvent(popup.columns[0], QEvent(QEvent.Enter)))
QTimer.singleShot(100, popup.close)
assert popup.exec(QPoint(100, 100)) is None
assert [m.column_opacity for m in popup.columns] == [1.0, .2]
print('PASS switching back to operation column and cancellation')
owner.close()

popup = build()
def hover_category():
    menu = popup.columns[1]
    location = QPointF(menu.actionGeometry(menu.actions()[0]).center())
    QApplication.sendEvent(menu, QMouseEvent(QEvent.MouseMove, location,
        QPointF(menu.mapToGlobal(location.toPoint())), Qt.NoButton, Qt.NoButton, Qt.NoModifier))
    def verify():
        try:
            assert menu._submenus[0].isVisible(), 'Category submenu did not open on hover'
        except BaseException as error:
            errors.append(error)
        popup.close()
    QTimer.singleShot(500, verify)
later(hover_category)
popup.exec(QPoint(100, 100))
if errors: raise errors[0]
print('PASS category submenu opens on pointer hover')

# An outside press received by a native submenu closes the whole popup at once.
for button in (Qt.LeftButton, Qt.RightButton):
    popup = build()
    def dismiss_once():
        sub = popup.columns[1]._submenus[0]
        sub.popup(popup.mapToGlobal(QPoint(popup.width(), 10)))
        global_point = QPoint(10, 10)
        local = QPointF(sub.mapFromGlobal(global_point))
        QApplication.sendEvent(sub, QMouseEvent(QEvent.MouseButtonPress, local,
            QPointF(global_point), button, button, Qt.NoModifier))
        assert not popup.isVisible() and not sub.isVisible(), 'First press must close all menus'
        QApplication.sendEvent(owner, QMouseEvent(QEvent.MouseButtonRelease, QPointF(10, 10),
            QPointF(global_point), button, Qt.NoButton, Qt.NoModifier))
        assert not popup.isVisible()
    later(dismiss_once)
    assert popup.exec(QPoint(100, 100)) is None
    if errors: raise errors[0]
    popup.deleteLater()
print('PASS one outside left/right press closes both columns and native submenus')

# A triggered operation can open a modal before the menu exec call unwinds.
from anclicker.platform.qt_compat.QtWidgets import QMessageBox
from anclicker.platform.qt_compat.QtTest import QTest
popup = build()
confirmed = []
def confirm_operation():
    box = QMessageBox(owner)
    box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    QTimer.singleShot(60, lambda: QTest.mouseClick(box.button(QMessageBox.Ok), Qt.LeftButton))
    guard = QTimer(box)
    guard.setSingleShot(True)
    guard.timeout.connect(box.reject)
    guard.start(2000)
    confirmed.append(box.exec())
    guard.stop()
action = popup.columns[0].actions()[0]
action.triggered.connect(confirm_operation)
def choose_confirmation():
    menu = popup.columns[0]
    QTest.mouseClick(menu, Qt.LeftButton, pos=menu.actionGeometry(action).center())
later(choose_confirmation)
assert popup.exec(QPoint(100, 100)) == action
assert confirmed == [QMessageBox.Ok], confirmed
print('PASS modal confirmation accepts first click after popup dismissal')
