"""Read the channel bundled with the Windows build."""
import json
import sys
from pathlib import Path

from info import UPDATE_CONFIG, update_source_config


def installed_update_config():
    if not getattr(sys, "frozen", False) or sys.platform != "win32":
        return update_source_config()
    path = Path(sys.executable).parent / UPDATE_CONFIG["snapshot_name"]
    saved = json.loads(path.read_text(encoding="utf-8"))
    expected = update_source_config(saved["delivery_channel"])
    if saved != expected:
        raise ValueError("安装包中的内部更新配置无效")
    return expected


def update_url():
    return installed_update_config()["url"]


def create_update_manager(source):
    import velopack

    options = velopack.UpdateOptions(
        AllowVersionDowngrade=False,
        MaximumDeltasBeforeFallback=10,
        ExplicitChannel=UPDATE_CONFIG["runtime"],
    )
    return velopack.UpdateManager(source, options)
