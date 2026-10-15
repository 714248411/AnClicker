"""Names shared by startup validation and the packaged resource layout."""
from pathlib import Path

REQUIRED_STARTUP_RESOURCES = (
    'resources/styles/Combinear.qss', 'resources/animations/startup.gif',
    'resources/icons/chevron-down.svg', 'resources/icons/chevron-up.svg',
)


def missing_startup_resources(resource_folder):
    folder = Path(resource_folder)
    missing = [name for name in REQUIRED_STARTUP_RESOURCES
               if not name.endswith('startup.gif') and not (folder / name).is_file()]
    animations = folder / 'resources/animations'
    if not any((animations / name).is_file() for name in ('startup.gif', 'startup-fallback.png')):
        missing.append('resources/animations/startup.gif 或 resources/animations/startup-fallback.png')
    return missing
