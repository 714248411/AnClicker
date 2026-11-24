"""Remember only successfully bound presets; never store window handles or secrets."""
import json
import os
import threading
from pathlib import Path
from anclicker.platform.background_binding import AUTO, PROFILES, canonical_preset
_lock = threading.RLock()

def preference_path():
    from anclicker.app.startup_environment import prepare_environment
    return prepare_environment() / 'damo' / 'binding-preference.json'

def preferred_preset():
    with _lock:
        try:
            value = canonical_preset(json.loads(preference_path().read_text(encoding='utf8')).get('preset'))
            return value if value in PROFILES else AUTO
        except (OSError, ValueError, TypeError, AttributeError):
            return AUTO

def remember_success(preset):
    preset = canonical_preset(preset)
    if preset not in PROFILES:
        return
    with _lock:
        if preferred_preset() == preset:
            return
        path = preference_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'preset': preset},ensure_ascii=False),encoding='utf8')
        os.replace(temporary,path)
