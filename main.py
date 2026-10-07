# coding: utf-8
import json
import os
import sys
from pathlib import Path

from startup_environment import prepare_environment, record_startup_error

STARTUP_DATA_FOLDER = prepare_environment()

if sys.platform == "win32":
    os.environ.setdefault("QT_QPA_PLATFORM", "windows:darkmode=0")

from PySide6.QtCore import QLibraryInfo, QLocale, QSharedMemory, Qt, QTranslator, QTimer
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
from info import APP_NAME, CURRENT_VERSION, WINDOW_TITLE

SINGLETON_KEY = os.environ.get(
    "ANCLICKER_SINGLETON_KEY", f"FasterThanLight_{APP_NAME}_SingletonKey"
)


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
    if '--migration-tool' in sys.argv:
        from migration_gui import MigrationWindow
        migration_window = MigrationWindow()
        migration_window.show()
        if '--startup-smoke-test' in sys.argv:
            from openpyxl import Workbook
            from legacy_workbook import LEGACY_HEADERS
            source = Path(os.environ['ANCLICKER_DATA_DIR']) / 'migration-fixture.xlsx'
            book = Workbook()
            book.active.title = '主流程'
            book.active.append(LEGACY_HEADERS)
            book.active.append([1, None, '时间等待', "{'类型':'时间等待','时长':0,'单位':'秒'}", None, None, None, 1, '自动跳过', 'smoke'])
            book.save(source)
            book.close()
            output = migration_window.convert_file(source, source.parent)
            if not output or not (output / '迁移报告.json').is_file():
                raise RuntimeError('独立迁移器转换测试失败')
            (source.parent / 'migration-ready.json').write_text(json.dumps({'ready':True}), encoding='utf-8')
            QTimer.singleShot(100, app.quit)
        return app.exec()
    shared_memory = QSharedMemory()
    shared_memory.setKey(SINGLETON_KEY)
    if shared_memory.attach():
        show_window(WINDOW_TITLE)
        return 0
    if not shared_memory.create(1):
        return 1

    flat_dir = os.path.join(RESOURCE_FOLDER, "flat")
    splash = show_splash_screen(app, os.path.join(flat_dir, "开屏.png"))

    # Keep the import delayed for the splash, but statically visible to
    # PyInstaller so the main window and its dependency tree are bundled.
    from Start_Win import Main_window

    main_window = Main_window()
    # Main_window installs the active dark/light theme itself.  Reapplying the
    # legacy Combinear.qss here used to overwrite it after construction and
    # left native-white table viewports and corners in the dark theme.

    main_window.show()
    splash.finish(main_window)
    splash.deleteLater()
    app.processEvents()
    if "--startup-smoke-test" in sys.argv:
        from ui_validation import validate_instruction_editors, validate_legacy_migration
        editor_validation = validate_instruction_editors(main_window)
        migration_validation = validate_legacy_migration()
        def report_ready():
            report = Path(os.environ["ANCLICKER_DATA_DIR"]) / "startup-ready.json"
            report.write_text(json.dumps({
                "ready": main_window.isVisible(),
                "version": app.applicationVersion(),
                "title": main_window.windowTitle(),
                "views": main_window.tabWidget.count(),
                "database": main_window.db.db_path,
                "editor_validation": editor_validation,
                "migration_validation": migration_validation,
            }), encoding="utf-8")
            app.exit(0)
        QTimer.singleShot(500, report_ready)
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        log_path = record_startup_error(STARTUP_DATA_FOLDER, error)
        if "--startup-smoke-test" not in sys.argv:
            from PySide6.QtWidgets import QMessageBox
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "启动失败", f"无法完成启动：{error}\n\n详细日志：{log_path}\n请完整解压安装包后运行 AnClicker.exe。")
        raise
