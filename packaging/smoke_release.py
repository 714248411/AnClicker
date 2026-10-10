"""Launch the actual packaged application and require a live main window."""

import json
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from info import CURRENT_VERSION, WINDOW_TITLE, APP_ID, EXECUTABLE_NAME
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=root / "dist")
    dist = parser.parse_args().dist.resolve()
    if sys.platform == "darwin":
        executable = dist / f"{APP_ID}.app/Contents/MacOS/{APP_ID}"
    else:
        executable = dist / APP_ID / (EXECUTABLE_NAME if sys.platform == "win32" else APP_ID)
    with tempfile.TemporaryDirectory(prefix="anclicker-startup-") as folder:
        env = dict(os.environ, ANCLICKER_DATA_DIR=folder,
                   ANCLICKER_SINGLETON_KEY=f"AnClickerSmoke_{uuid.uuid4().hex}",
                   QT_QPA_PLATFORM="cocoa" if sys.platform == "darwin" else "offscreen")
        if (sys.platform.startswith('linux') and os.environ.get('GITHUB_ACTIONS') == 'true'
                and not os.environ.get('XAUTHORITY') and not (Path.home() / '.Xauthority').exists()):
            # The CI Xvfb has no cookie; python-xlib still requires a readable file.
            authority = Path(folder) / 'Xauthority'
            authority.touch()
            env['XAUTHORITY'] = str(authority)
        for attempt in range(2):
            env['QT_SCALE_FACTOR'] = '1' if attempt == 0 else '2'
            report = Path(folder) / "startup-ready.json"
            report.unlink(missing_ok=True)
            process = subprocess.Popen([str(executable), "--startup-smoke-test"], env=env, cwd=folder)
            try:
                result = process.wait(timeout=90)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise RuntimeError("Packaged startup timed out; a process alone does not prove readiness")
            if result != 0 or not report.exists():
                error_log = Path(folder) / "logs/startup-error.log"
                detail = error_log.read_text(encoding="utf-8") if error_log.exists() else "No readiness report"
                raise RuntimeError(f"Packaged startup failed ({result}): {detail}")
            ready = json.loads(report.read_text(encoding="utf-8"))
            if not ready["ready"] or ready["views"] != 6 or not ready.get("window_chrome_valid"):
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
        result = subprocess.run([str(executable), '--migration-tool', '--startup-smoke-test'],
                                env=env, cwd=folder, timeout=90)
        if result.returncode or not (Path(folder) / 'migration-ready.json').is_file():
            raise RuntimeError('Standalone migration entry failed packaged smoke test')
        print('Standalone migration entry: ready; converted fixture and wrote report')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
