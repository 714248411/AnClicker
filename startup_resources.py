"""Names shared by startup validation and the packaged resource layout."""
from pathlib import Path

REQUIRED_STARTUP_RESOURCES = ('Combinear.qss', 'startup.gif',
                              'chevron-down.svg', 'chevron-up.svg')

def missing_startup_resources(resource_folder):
    folder = Path(resource_folder) / 'flat'
    missing = ['flat/' + name for name in REQUIRED_STARTUP_RESOURCES
               if name != 'startup.gif' and not (folder / name).is_file()]
    if not any((folder / name).is_file() for name in ('startup.gif', 'startup-fallback.png')):
        missing.append('flat/startup.gif 或 flat/startup-fallback.png')
    return missing
