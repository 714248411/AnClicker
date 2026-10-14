import os
import subprocess
import sys
from pathlib import Path
from qt_compat.QtWidgets import QApplication, QWidget
from qt_compat.QtTest import QTest
from startup_splash import show_local_splash, show_splash_screen

ROOT = Path(__file__).resolve().parents[1]

def test_movie_advances_and_readiness_stops_immediately():
    app = QApplication.instance() or QApplication([])
    splash = show_local_splash(app, ROOT / 'flat/startup.gif')
    frames = []
    splash.movie.frameChanged.connect(frames.append)
    try:
        assert splash.movie.isValid()
        QTest.qWait(350)
        assert len(frames) > 1
        main = QWidget()
        splash.finish(main)
        assert not splash.isVisible()
        assert splash.movie.state() == splash.movie.NotRunning
    finally:
        splash.close()
        splash.deleteLater()

def test_animation_process_closes_when_parent_pipe_closes():
    app = QApplication.instance() or QApplication([])
    splash = show_splash_screen(app, ROOT / 'flat/startup.gif')
    try:
        QTest.qWait(700)
        assert splash.process.poll() is None
        splash.finish()
        assert splash.process.wait(timeout=10) == 0
    finally:
        if splash.process.poll() is None:
            splash.process.kill()
            splash.process.wait()

def test_only_new_animation_is_packaged():
    spec = (ROOT / 'packaging/main.spec').read_text(encoding='utf8')
    assert 'startup.gif' in spec
    assert '开屏.png' not in spec
    assert not (ROOT / 'flat/开屏.png').exists()


def test_gif_resources_pass_without_legacy_png(tmp_path):
    from startup_resources import missing_startup_resources, REQUIRED_STARTUP_RESOURCES
    folder = tmp_path / 'flat'
    folder.mkdir()
    for name in REQUIRED_STARTUP_RESOURCES:
        (folder / name).write_bytes(b'resource')
    assert not list(folder.glob('*.png'))
    assert missing_startup_resources(tmp_path) == []
    (folder / 'startup.gif').unlink()
    assert missing_startup_resources(tmp_path) == ['flat/startup.gif 或 flat/startup-fallback.png']
    (folder / 'startup-fallback.png').write_bytes(b'fallback')
    assert missing_startup_resources(tmp_path) == []

def test_missing_resource_folder_reports_exact_filenames(tmp_path):
    from startup_resources import missing_startup_resources, REQUIRED_STARTUP_RESOURCES
    assert set(missing_startup_resources(tmp_path)) == {'flat/Combinear.qss', 'flat/chevron-down.svg', 'flat/chevron-up.svg', 'flat/startup.gif 或 flat/startup-fallback.png'}


def test_unsupported_gif_shows_extracted_static_frame(tmp_path):
    import shutil
    from startup_splash import LoadingSplashScreen
    app = QApplication.instance() or QApplication([])
    shutil.copyfile(ROOT / 'flat/startup-fallback.png', tmp_path / 'startup-fallback.png')
    (tmp_path / 'startup.gif').write_bytes(b'unsupported gif')
    splash = LoadingSplashScreen(tmp_path / 'startup.gif')
    try:
        assert splash._static_mode
        assert not splash._fallback.isNull()
        assert splash.movie.state() == splash.movie.NotRunning
        splash.show()
        app.processEvents()
        assert not splash.grab().isNull()
        splash.finish(None)
        assert not splash.isVisible()
    finally:
        splash.close()

def test_decode_error_switches_to_fallback_and_stops_movie():
    from startup_splash import LoadingSplashScreen
    app = QApplication.instance() or QApplication([])
    splash = LoadingSplashScreen(ROOT / 'flat/startup.gif')
    try:
        splash.movie.error.emit(splash.movie.lastError())
        assert splash._static_mode
        assert not splash._fallback.isNull()
        assert splash.movie.state() == splash.movie.NotRunning
    finally:
        splash.close()
