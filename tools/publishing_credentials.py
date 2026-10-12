"""Read whitelisted literal assignments as data; never execute the supplied script."""
from pathlib import Path
import re

def publishing_environment(path, base, config):
    raw = Path(path).read_bytes()
    text = raw.decode('utf-16') if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else raw.decode('utf-8-sig')
    values = {}
    pattern = r"^\s*'(QINIU_[A-Z_]+)'\s*=\s*'([^'\r\n]*)'\s*$"
    for key, value in re.findall(pattern, text, re.MULTILINE):
        if key in values:
            raise ValueError('Duplicate publishing variable')
        values[key] = value.strip()
    for name in ('bucket', 'region', 'key_prefix'):
        if values.get(config[name + '_env']) != config[name]:
            raise ValueError('Publishing destination does not match project configuration')
    env = dict(base)
    for name in ('access_key', 'secret_key'):
        key = config[name + '_env']
        if not values.get(key):
            raise ValueError('Required publishing credential missing')
        env[key] = values[key]
    # The supplied legacy test URL is not a verified client update endpoint.
    for name in ('bucket', 'region', 'key_prefix', 'public_base_url'):
        env[config[name + '_env']] = config[name]
    return env
