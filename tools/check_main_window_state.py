"""Persist real Qt window geometry through SQLite, including compact/maximized cases."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat.QtCore import Qt, QRect
from anclicker.platform.qt_compat.QtWidgets import QApplication, QWidget
from anclicker.storage.database import DatabaseOperation
from anclicker.storage.settings import SettingsRepository
from anclicker.ui.dialogs.窗口状态 import install_window_state
from tools.packaging.resource_archive import require_expanded_resources


def main():
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        db = DatabaseOperation(str(root / 'state.db'))
        def make():
            window = QWidget(None, Qt.FramelessWindowHint)
            window.resize(360, 240)
            install_window_state(window, db, 'main', remember_position=True, enable_maximize_button=False)
            window.show()
            app.processEvents()
            app.processEvents()
            return window
        first = make()
        bounds = first.screen().availableGeometry()
        geometry = QRect(bounds.x() + 45, bounds.y() + 55, 360, 240)
        first.setGeometry(geometry)
        app.processEvents()
        first.close()
        second = make()
        assert second.geometry() == geometry, (second.geometry(), geometry)
        second._restore_client_geometry = QRect(geometry)
        second.showMaximized()
        app.processEvents()
        second.close()
        third = make()
        assert third.isMaximized()
        assert db.get_window_state('main')['position'] == (geometry.x(), geometry.y())
        third.showNormal()
        app.processEvents()
        assert third.geometry() == geometry, (third.geometry(), geometry)

        # Closing in compact mode keeps the complete main window's normal rectangle.
        third.view_workspace = SimpleNamespace(compact=SimpleNamespace(active=True, was_maximized=True, normal_rect=geometry))
        third.setGeometry(bounds.x() + 10, bounds.y() + 15, 200, 150)
        third._window_state_controller._saved = False
        third._window_state_controller.save_window_state()
        state = db.get_window_state('main')
        assert state == {'size': (360, 240), 'maximized': True, 'position': (geometry.x(), geometry.y())}, state
        third.close()

        # Missing monitors/invalid positions cannot strand the window offscreen.
        db.save_window_size(360, 240, 'main', position=(-100000, -100000))
        fourth = make()
        assert fourth.screen().availableGeometry().contains(fourth.geometry())
        fourth.close()
        assert SettingsRepository._parse_window_state('(640, 480)') == {'size': (640, 480), 'maximized': False}
        for position in ([False, 10], [1], 'bad', [2**40, 1]):
            assert 'position' not in SettingsRepository._parse_window_state({'size': [640, 480], 'position': position})
        valid = {'size': (640, 480), 'maximized': False, 'position': (-900, 60)}
        assert SettingsRepository._parse_window_state(SettingsRepository._serialize_window_state(valid)) == valid

        # Expanded resources are accepted without mutation; nested archives are rejected.
        assets = root / 'app' / 'models'
        assets.mkdir(parents=True)
        model = assets / 'model.gguf'
        model.write_bytes(b'offline model')
        require_expanded_resources(assets.parent)
        assert model.read_bytes() == b'offline model'
        for name in ('AnClicker-resources.zip', 'AnClicker-resources.json'):
            marker = assets.parent / name
            marker.touch()
            try:
                require_expanded_resources(assets.parent)
            except RuntimeError:
                pass
            else:
                raise AssertionError('nested resources accepted')
            marker.unlink()
    print('PASS main geometry reopen, maximized restore, compact isolation, offscreen recovery, legacy settings, expanded packaging guard')


if __name__ == '__main__':
    main()
