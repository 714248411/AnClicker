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
    from info import CURRENT_VERSION, WINDOW_TITLE
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, default=root / "dist")
    dist = parser.parse_args().dist.resolve()
    if sys.platform == "darwin":
        executable = dist / "AnClicker.app/Contents/MacOS/AnClicker"
    else:
        executable = dist / "AnClicker" / ("AnClicker.exe" if sys.platform == "win32" else "AnClicker")
    with tempfile.TemporaryDirectory(prefix="anclicker-startup-") as folder:
        env = dict(os.environ, ANCLICKER_DATA_DIR=folder,
                   ANCLICKER_SINGLETON_KEY=f"AnClickerSmoke_{uuid.uuid4().hex}",
                   QT_QPA_PLATFORM="offscreen")
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
            if not ready["ready"] or ready["views"] != 6:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
