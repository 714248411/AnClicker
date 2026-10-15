"""Launch the actual packaged application and require a live main window."""

import json
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[2]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'CURRENT_VERSION_WINDOW_TITLE_APP_ID_EXECUTABLE_NAME': ('from', 'info', ('CURRENT_VERSION', 'WINDOW_TITLE', 'APP_ID', 'EXECUTABLE_NAME'), 0),
})



def main():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    anclicker = _module_imports.load('anclicker')  # Enable source-tree legacy entry points.
    CURRENT_VERSION, WINDOW_TITLE, APP_ID, EXECUTABLE_NAME = _module_imports.load('CURRENT_VERSION_WINDOW_TITLE_APP_ID_EXECUTABLE_NAME')
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=root / "artifacts/dist")
    dist = parser.parse_args().dist.resolve()
    if sys.platform == "darwin":
        executable = dist / f"{APP_ID}.app/Contents/MacOS/{APP_ID}"
    else:
        executable = dist / APP_ID / (EXECUTABLE_NAME if sys.platform == "win32" else APP_ID)
    with tempfile.TemporaryDirectory(prefix="anclicker-startup-") as folder:
        env = dict(os.environ, ANCLICKER_DATA_DIR=folder,
                   ANCLICKER_SINGLETON_KEY=f"AnClickerSmoke_{uuid.uuid4().hex}",
                   QT_QPA_PLATFORM=("windows" if sys.platform == "win32" else
                                    "cocoa" if sys.platform == "darwin" else "xcb"))
        for attempt in range(2):
            env['QT_SCALE_FACTOR'] = '1' if attempt == 0 else '2'
            report = Path(folder) / "startup-ready.json"
            report.unlink(missing_ok=True)
            process = subprocess.Popen([str(executable), "--startup-smoke-test"], env=env, cwd=folder)
            try:
                result = process.wait(timeout=240)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise RuntimeError("Packaged startup timed out; a process alone does not prove readiness")
            if result != 0 or not report.exists():
                error_log = Path(folder) / "logs/startup-error.log"
                detail = error_log.read_text(encoding="utf-8") if error_log.exists() else "No readiness report"
                for engine_log in Path(folder).glob('*/engine-startup.log'):
                    detail += '\n' + engine_log.read_text(encoding='utf-8', errors='replace')[-6000:]
                raise RuntimeError(f"Packaged startup failed ({result}): {detail}")
            ready = json.loads(report.read_text(encoding="utf-8"))
            expected_views = ["主界面", "表格图", "流程图", "多功能", "录制", "网页录制", "对话 Agent"]
            if (not ready["ready"] or ready["views"] != len(expected_views)
                    or ready.get("view_labels") != expected_views
                    or not ready.get("window_chrome_valid")):
                raise RuntimeError(f"Main window incomplete: {ready}")
            if ready["version"] != CURRENT_VERSION or ready["title"] != WINDOW_TITLE:
                raise RuntimeError(f"Packaged version does not match release: {ready}")
            checks = ready.get('editor_validation', {})
            if not checks.get('image_click_layout') or checks.get('spinboxes_checked', 0) < 70:
                raise RuntimeError(f"Packaged editor checks missing: {ready}")
            migration = ready.get('migration_validation', {})
            if (migration.get('commands_checked') != 2 or not migration.get('round_trip')
                    or not migration.get('rollback')):
                raise RuntimeError(f"Packaged legacy migration checks missing: {ready}")
            print(f"Startup {attempt + 1}: ready; scale={env['QT_SCALE_FACTOR']}; editor checks={checks}")
            print(f"Legacy migration: {migration}")
            image_checks = ready.get('image_validation', {})
            if image_checks.get('count') != 14 or not image_checks.get('synthetic_screen'):
                raise RuntimeError(f"Packaged image execution checks missing: {ready}")
            print(f"Image execution: {image_checks['count']} real OpenCV checks; synthetic screen, no native input")
            ocr_checks = ready.get('ocr_validation', {})
            if not ocr_checks.get('rapidocr') or not ocr_checks.get('isolated_worker'):
                raise RuntimeError(f'Packaged offline OCR checks missing: {ready}')
            print(f'Offline OCR: {ocr_checks}')
            rpa_checks = ready.get('rpa_validation', {})
            if not all(rpa_checks.get(key) for key in ('excel', 'browser', 'screenshot', 'web_recording')):
                raise RuntimeError(f'Packaged RPA checks missing: {ready}')
            print(f'RPA: {rpa_checks}')
        result = subprocess.run([str(executable), '--migration-tool', '--startup-smoke-test'],
                                env=env, cwd=folder, timeout=90)
        if result.returncode or not (Path(folder) / 'migration-ready.json').is_file():
            raise RuntimeError('Standalone migration entry failed packaged smoke test')
        print('Standalone migration entry: ready; converted fixture and wrote report')
        if sys.platform == 'win32':
            code = '''
from pathlib import Path
import sys
bundle = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(bundle))
import anclicker.platform.background_dm_worker as worker
import background_dm_worker as legacy
from anclicker.app.paths import resource_path
assert Path(worker.__file__).resolve().is_relative_to(bundle)
assert worker is legacy
assert resource_path('resources', 'background', 'background_dm_methods.json').is_file()
assert not any(name.startswith(('qt_compat', 'PySide', 'anclicker.ui')) for name in sys.modules)
'''
            probe = subprocess.run([sys.executable, '-I', '-c', code, str(executable.parent)],
                                   cwd=folder, env=env, capture_output=True, timeout=30)
            if probe.returncode:
                raise RuntimeError('Standalone background Python import failed: ' +
                                   probe.stderr.decode('utf-8', errors='replace'))
            print('Standalone background Python import: ready; no Qt or source checkout required')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
