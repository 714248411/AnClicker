"""Public client configuration. Upload credentials are never imported here."""
import json
import sys
from pathlib import Path

PACK_ID = "AnClicker"
RUNTIME = "win-x64"
FEED_NAME = "releases.win-x64.json"

def update_url():
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    path = root / "update-source.json"
    if not path.is_file():
        return ""
    config = json.loads(path.read_text(encoding="utf-8"))
    from urllib.parse import urlsplit
    url = config.get("url", "")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query or parsed.fragment:
        raise ValueError("更新源必须是公开 HTTPS 地址")
    if config.get("pack_id") != PACK_ID or config.get("runtime") != RUNTIME:
        raise ValueError("更新源项目或平台不匹配")
    return url.rstrip("/")
