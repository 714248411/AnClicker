"""Normalize user-entered navigation addresses without capturing redirects."""
from urllib.parse import urlsplit, urlunsplit


def normalize_web_url(value):
    value = str(value or '').strip()
    if not value:
        raise ValueError('请输入网页地址')
    if '://' not in value:
        value = 'https://' + value
    parsed = urlsplit(value)
    if parsed.scheme.lower() not in ('http', 'https') or not parsed.hostname or any(c.isspace() for c in value):
        raise ValueError('请输入 http 或 https 网页地址')
    # A commonly entered site name has an unambiguous public homepage.
    if parsed.netloc.lower() in ('hao123', 'www.hao123'):
        parsed = parsed._replace(netloc='www.hao123.com')
    return urlunsplit(parsed)
