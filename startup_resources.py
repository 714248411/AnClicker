"""Names shared by startup validation and the packaged resource layout."""
from pathlib import Path

REQUIRED_STARTUP_RESOURCES = ('Combinear.qss', 'startup.gif',
                              'chevron-down.svg', 'chevron-up.svg')

def missing_startup_resources(resource_folder):
    folder = Path(resource_folder) / 'flat'
    return ['flat/' + name for name in REQUIRED_STARTUP_RESOURCES
            if not (folder / name).is_file()]
