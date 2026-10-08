"""Compatibility facade for application configuration centralized in info.py."""
from urllib.parse import urlsplit
from info import UPDATE_CONFIG


def update_url():
    parsed = urlsplit(UPDATE_CONFIG['url'])
    if (parsed.scheme != "https" or not parsed.netloc or parsed.username is not None
            or parsed.password is not None or parsed.query or parsed.fragment):
        raise ValueError("更新源必须是公开 HTTPS 地址")
    return UPDATE_CONFIG['url'].rstrip("/")
