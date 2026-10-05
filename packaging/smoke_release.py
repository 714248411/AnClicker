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
            if not ready["ready"] or ready["views"] != 5:
                raise RuntimeError(f"Main window incomplete: {ready}")
            if ready["version"] != CURRENT_VERSION or ready["title"] != WINDOW_TITLE:
                raise RuntimeError(f"Packaged version does not match release: {ready}")
            print(f"Startup {attempt + 1}: main window ready, five views, database initialized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
