# coding: utf-8
import importlib
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=0"

from PySide6.QtCore import QLibraryInfo, QLocale, QSharedMemory, Qt, QTranslator
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPixmap,
)
from PySide6.QtWidgets import QApplication, QSplashScreen

from functions import RESOURCE_FOLDER, ensure_data_directories, show_window
from info import APP_NAME, CURRENT_VERSION

WINDOW_TITLE = f"{APP_NAME} {CURRENT_VERSION}"
SINGLETON_KEY = f"FasterThanLight_{APP_NAME}_SingletonKey"


class LoadingSplashScreen(QSplashScreen):
    """使用清晰的自定义文字绘制启动画面。"""

    def drawContents(self, painter):
        message = self.message()
        if not message:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("微软雅黑", 16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#176b2c"))
        painter.drawText(
            self.rect().adjusted(0, 0, 0, -18),
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            message,
        )
        painter.restore()


def read_qss_file(qss_file_name):
    """读取应用样式文件。"""
    with open(qss_file_name, "r", encoding="UTF-8") as file:
        return file.read()


def install_qt_chinese_translator(app):
    """安装 Qt 中文翻译，使标准对话框显示为中文。"""
    translator = QTranslator(app)
    locale = QLocale.system().name()
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load(f"qtbase_{locale}", translations_path):
        app.installTranslator(translator)
    return translator


def show_splash_screen(app, image_path):
    """创建并居中显示圆角启动画面。"""
    splash = LoadingSplashScreen()
    if Path(image_path).is_file():
        pixmap = QPixmap(image_path).scaled(
            600,
            400,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        rounded_pixmap = QPixmap(pixmap.size())
        rounded_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(pixmap.rect(), 24, 24)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        splash.setPixmap(rounded_pixmap)
        splash.setMask(rounded_pixmap.mask())

    screen = app.primaryScreen()
    if screen is not None:
        geometry = screen.availableGeometry()
        splash.move(
            geometry.x() + (geometry.width() - splash.width()) // 2,
            geometry.y() + (geometry.height() - splash.height()) // 2,
        )
    splash.showMessage(
        "正在载入中...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
        QColor("#176b2c"),
    )
    splash.show()
    app.processEvents()
    return splash


def main():
    """初始化并启动 Clicker。"""
    ensure_data_directories()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(CURRENT_VERSION)
    try:
        QGuiApplication.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass
    install_qt_chinese_translator(app)
    shared_memory = QSharedMemory()
    shared_memory.setKey(SINGLETON_KEY)
    if shared_memory.attach():
        show_window(WINDOW_TITLE)
        return 0
    if not shared_memory.create(1):
        return 1

    flat_dir = os.path.join(RESOURCE_FOLDER, "flat")
    splash = show_splash_screen(app, os.path.join(flat_dir, "开屏.png"))

    start_window = importlib.import_module("Start_Win")
    main_window = start_window.Main_window()
    try:
        main_window.setStyleSheet(
            read_qss_file(os.path.join(flat_dir, "Combinear.qss"))
        )
    except FileNotFoundError:
        pass

    main_window.show()
    splash.finish(main_window)
    splash.deleteLater()
    app.processEvents()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
