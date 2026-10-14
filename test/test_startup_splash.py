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
