# coding: utf-8
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'run_agent_model_validation': ('from', 'anclicker.execution.agent_model_validation', ('run',), 0),
    'background_dm_main': ('from', 'anclicker.platform.background_dm_worker', ('main',), 0),
    'ocr_worker_main': ('from', 'anclicker.platform.local_ocr_worker', ('main',), 0),
    'update_worker_main': ('from', 'anclicker.app.updates.process_worker', ('main',), 0),
    'run_animation': ('from', 'anclicker.app.startup_splash', ('run_animation',), 0),
    'velopack': ('import', 'velopack', (), False),
    'prepare_environment_record_startup_error': ('from', 'anclicker.app.startup_environment', ('prepare_environment', 'record_startup_error'), 0),
    'faulthandler': ('import', 'faulthandler', (), False),
    'configure_dpi': ('from', 'anclicker.platform.windows_runtime', ('configure_dpi',), 0),
    'RESOURCE_FOLDER_ensure_data_directories': ('from', 'anclicker.app.paths', ('RESOURCE_FOLDER', 'ensure_data_directories'), 0),
    'BINDING_apply_application_style_configure_application': ('from', 'anclicker.platform.qt_compat', ('BINDING', 'apply_application_style', 'configure_application'), 0),
    'QtCore_QLibraryInfo_etc': ('from', 'anclicker.platform.qt_compat.QtCore', ('QLibraryInfo', 'QLocale', 'QLockFile', 'Qt', 'QTimer', 'QTranslator', 'qVersion'), 0),
    'QtGui_QColor_etc': ('from', 'anclicker.platform.qt_compat.QtGui', ('QColor', 'QFont', 'QGuiApplication', 'QPainter', 'QPainterPath', 'QPixmap'), 0),
    'QApplication_QSplashScreen': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QApplication', 'QSplashScreen'), 0),
    'show_window': ('from', 'anclicker.platform.services', ('show_window',), 0),
    'info_APP_NAME_etc': ('from', 'info', ('APP_NAME', 'CURRENT_VERSION', 'SINGLETON_ENV', 'SINGLETON_KEY_DEFAULT', 'WINDOW_TITLE', 'update_source_config'), 0),
    'LoadingSplashScreen_show_splash_screen': ('from', 'anclicker.app.startup_splash', ('LoadingSplashScreen', 'show_splash_screen'), 0),
    'MigrationWindow': ('from', 'anclicker.ui.migration_gui', ('MigrationWindow',), 0),
    'Workbook': ('from', 'openpyxl', ('Workbook',), 0),
    'LEGACY_HEADERS': ('from', 'anclicker.storage.legacy_workbook', ('LEGACY_HEADERS',), 0),
    'Main_window': ('from', 'anclicker.app.Start_Win', ('Main_window',), 0),
    'run': ('from', 'anclicker.app.updates.local_smoke', ('run',), 0),
    'validate_instruction_editors_validate_legacy_migration': ('from', 'anclicker.app.ui_validation', ('validate_instruction_editors', 'validate_legacy_migration'), 0),
    'validate_image_execution': ('from', 'anclicker.ui.image_validation', ('validate_image_execution',), 0),
    'validate_offline_ocr': ('from', 'anclicker.app.ocr_validation', ('validate_offline_ocr',), 0),
    'validate_rpa': ('from', 'anclicker.app.rpa_validation', ('validate_rpa',), 0),
    'validate_window_chrome': ('from', 'anclicker.ui.window_chrome', ('validate_window_chrome',), 0),
    'QMessageBox': ('from', 'qt_compat.QtWidgets', ('QMessageBox',), 0),
})


if __name__ == "__main__" and "--agent-model-smoke" in sys.argv:
    run_agent_model_validation = _module_imports.load('run_agent_model_validation')

    raise SystemExit(run_agent_model_validation())

# Workers must not enter Velopack lifecycle hooks, Qt or the app singleton.
if __name__ == "__main__" and "--background-dm-worker" in sys.argv:
    background_dm_main = _module_imports.load('background_dm_main')

    raise SystemExit(background_dm_main())

if __name__ == "__main__" and "--local-ocr-worker" in sys.argv:
    ocr_worker_main = _module_imports.load('ocr_worker_main')

    ocr_worker_main()
    raise SystemExit(0)

if __name__ == "__main__" and "--update-worker" in sys.argv:
    update_worker_main = _module_imports.load('update_worker_main')

    update_worker_main()
    raise SystemExit(0)

# Animation runs independently so synchronous UI initialization cannot freeze it.
if __name__ == "__main__" and "--startup-animation" in sys.argv:
    run_animation = _module_imports.load('run_animation')

    raise SystemExit(run_animation(sys.argv[sys.argv.index("--startup-animation") + 1]))

# Handle lifecycle hooks before storage, Qt and singleton initialization.
if __name__ == "__main__" and sys.platform == "win32" and getattr(sys, "frozen", False):
    velopack = _module_imports.load('velopack')

    velopack.App().set_auto_apply_on_startup(False).run()

prepare_environment, record_startup_error = _module_imports.load('prepare_environment_record_startup_error')

STARTUP_DATA_FOLDER = prepare_environment()

# Keep a diagnostic trace for isolated release checks, including native crashes.
_SMOKE_TRACE = None
if "--release-smoke" in sys.argv:
    faulthandler = _module_imports.load('faulthandler')

    _SMOKE_TRACE = (Path(STARTUP_DATA_FOLDER) / "startup-trace.log").open(
        "a", encoding="utf-8"
    )
    faulthandler.enable(file=_SMOKE_TRACE)
    faulthandler.dump_traceback_later(35, repeat=True, file=_SMOKE_TRACE)


def smoke_stage(stage):
    if _SMOKE_TRACE is not None:
        _SMOKE_TRACE.write(stage + "\n")
        _SMOKE_TRACE.flush()


if sys.platform == "win32":
    configure_dpi = _module_imports.load('configure_dpi')

    DPI_POLICY = configure_dpi()
    os.environ.setdefault("QT_QPA_PLATFORM", "windows:darkmode=0")
else:
    DPI_POLICY = "platform-default"

RESOURCE_FOLDER, ensure_data_directories = _module_imports.load('RESOURCE_FOLDER_ensure_data_directories')
BINDING, apply_application_style, configure_application = _module_imports.load('BINDING_apply_application_style_configure_application')
QLibraryInfo, QLocale, QLockFile, Qt, QTimer, QTranslator, qVersion = _module_imports.load('QtCore_QLibraryInfo_etc')
QColor, QFont, QGuiApplication, QPainter, QPainterPath, QPixmap = _module_imports.load('QtGui_QColor_etc')
QApplication, QSplashScreen = _module_imports.load('QApplication_QSplashScreen')
show_window = _module_imports.load('show_window')
APP_NAME, CURRENT_VERSION, SINGLETON_ENV, SINGLETON_KEY_DEFAULT, WINDOW_TITLE, update_source_config = _module_imports.load('info_APP_NAME_etc')

SINGLETON_KEY = os.environ.get(SINGLETON_ENV, SINGLETON_KEY_DEFAULT)


LoadingSplashScreen, show_splash_screen = _module_imports.load('LoadingSplashScreen_show_splash_screen')


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


def main():
    """初始化并启动 Clicker。"""
    ensure_data_directories()
    configure_application()
    app = QApplication(sys.argv)
    apply_application_style(app)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(CURRENT_VERSION)
    try:
        QGuiApplication.styleHints().setColorScheme(Qt.ColorScheme.Light)
    except AttributeError:
        pass
    install_qt_chinese_translator(app)
    if "--migration-tool" in sys.argv:
        MigrationWindow = _module_imports.load('MigrationWindow')

        migration_window = MigrationWindow()
        migration_window.show()
        if "--startup-smoke-test" in sys.argv:
            Workbook = _module_imports.load('Workbook')

            LEGACY_HEADERS = _module_imports.load('LEGACY_HEADERS')

            source = Path(os.environ["ANCLICKER_DATA_DIR"]) / "migration-fixture.xlsx"
            book = Workbook()
            book.active.title = "主流程"
            book.active.append(LEGACY_HEADERS)
            book.active.append(
                [
                    1,
                    None,
                    "时间等待",
                    "{'类型':'时间等待','时长':0,'单位':'秒'}",
                    None,
                    None,
                    None,
                    1,
                    "自动跳过",
                    "smoke",
                ]
            )
            book.save(source)
            book.close()
            output = migration_window.convert_file(source, source.parent)
            if not output or not (output / "迁移报告.json").is_file():
                raise RuntimeError("独立迁移器转换测试失败")
            (source.parent / "migration-ready.json").write_text(
                json.dumps({"ready": True}), encoding="utf-8"
            )
            QTimer.singleShot(100, app.quit)
        return app.exec()
    lock_name = hashlib.sha256(SINGLETON_KEY.encode("utf-8")).hexdigest()
    instance_lock = QLockFile(
        str(Path(tempfile.gettempdir()) / f"AnClicker-{lock_name}.lock")
    )
    if not instance_lock.tryLock(0):
        if instance_lock.error() == QLockFile.LockFailedError:
            show_window(WINDOW_TITLE)
            return 0
        return 1

    flat_dir = os.path.join(RESOURCE_FOLDER, "resources", "animations")
    splash = show_splash_screen(app, os.path.join(flat_dir, "startup.gif"))

    # Keep the import delayed for the splash, but statically visible to
    # PyInstaller so the main window and its dependency tree are bundled.
    Main_window = _module_imports.load('Main_window')

    smoke_stage("create-main-window")
    main_window = Main_window()
    smoke_stage("main-window-created")
    # Main_window installs the active dark/light theme itself.  Reapplying the
    # legacy Combinear.qss here used to overwrite it after construction and
    # left native-white table viewports and corners in the dark theme.

    main_window.show()
    splash.finish(main_window)
    splash.deleteLater()
    app.processEvents()
    if "--velopack-local-smoke" in sys.argv:
        run = _module_imports.load('run')

        def upgrade_probe():
            try:
                run(app, main_window)
            except Exception as error:
                record_startup_error(STARTUP_DATA_FOLDER, error)
                app.exit(1)

        QTimer.singleShot(500, upgrade_probe)
    if "--startup-smoke-test" in sys.argv or "--release-smoke" in sys.argv:
        full_checks = not (
            "--release-smoke" in sys.argv
            and os.environ.get("ANCLICKER_SMOKE_LIGHTWEIGHT") == "1"
        )
        editor_validation = migration_validation = image_validation = ocr_validation = (
            rpa_validation
        ) = {}
        if full_checks:
            validate_instruction_editors, validate_legacy_migration = _module_imports.load('validate_instruction_editors_validate_legacy_migration')

            smoke_stage("editors")
            editor_validation = validate_instruction_editors(main_window)
            smoke_stage("migration")
            migration_validation = validate_legacy_migration()
            validate_image_execution = _module_imports.load('validate_image_execution')

            smoke_stage("images")
            image_validation = validate_image_execution()
            validate_offline_ocr = _module_imports.load('validate_offline_ocr')

            smoke_stage("ocr")
            ocr_validation = validate_offline_ocr()
            validate_rpa = _module_imports.load('validate_rpa')

            smoke_stage("rpa")
            rpa_validation = validate_rpa()
        smoke_stage("waiting-report-timer")

        def report_ready():
            smoke_stage("report-ready")
            validate_window_chrome = _module_imports.load('validate_window_chrome')

            chrome_valid = validate_window_chrome(main_window)
            report = Path(os.environ["ANCLICKER_DATA_DIR"]) / "startup-ready.json"
            report.write_text(
                json.dumps(
                    {
                        "ok": True,
                        "window_visible": main_window.isVisible(),
                        "window_chrome_valid": chrome_valid,
                        "full_checks": full_checks,
                        "data_root": os.environ["ANCLICKER_DATA_DIR"],
                        "ready": main_window.isVisible(),
                        "version": (
                            app.applicationVersion().removeprefix("v")
                            if "--release-smoke" in sys.argv
                            else app.applicationVersion()
                        ),
                        "title": main_window.windowTitle(),
                        "update_config": update_source_config(),
                        "runtime": {
                            "python": sys.version.split()[0],
                            "qt": qVersion(),
                            "binding": BINDING,
                            "dpi_policy": DPI_POLICY,
                            "qt_platform": app.platformName(),
                            "style": app.style().objectName(),
                            "windows_build": (
                                sys.getwindowsversion().build
                                if sys.platform == "win32"
                                else None
                            ),
                        },
                        "views": main_window.tabWidget.count(),
                        "view_labels": [
                            main_window.tabWidget.tabText(i)
                            for i in range(main_window.tabWidget.count())
                        ],
                        "database": main_window.db.db_path,
                        "editor_validation": editor_validation,
                        "migration_validation": migration_validation,
                        "image_validation": image_validation,
                        "ocr_validation": ocr_validation,
                        "rpa_validation": rpa_validation,
                    }
                ),
                encoding="utf-8",
            )
            app.exit(0)

        QTimer.singleShot(500, report_ready)
    return app.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        log_path = record_startup_error(STARTUP_DATA_FOLDER, error)
        if not any(
            flag in sys.argv for flag in ("--startup-smoke-test", "--release-smoke")
        ):
            QMessageBox = _module_imports.load('QMessageBox')

            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "启动失败",
                f"无法完成启动：{error}\n\n详细日志：{log_path}\n请完整解压安装包后运行 AnClicker.exe。",
            )
        raise
