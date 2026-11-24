"""Build or freeze the selected AnClicker internal update channel."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from info import EXECUTABLE_NAME, UPDATE_CHANNELS, UPDATE_CONFIG, VERSION


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build', 'freeze', 'upgrade'))
    parser.add_argument('--channel', choices=UPDATE_CHANNELS, default='stable')
    parser.add_argument('--runtime-bundle', type=Path)
    args = parser.parse_args()
    channel = args.channel
    path = ROOT / ('publish.json' if channel == 'stable' else 'publish.beta.json')
    config = json.loads(path.read_text(encoding='utf-8'))
    expected = {
        'key': UPDATE_CONFIG['project'], 'project': UPDATE_CONFIG['project'],
        'software_type': 'internal', 'pack_id': UPDATE_CONFIG['pack_id'],
        'api_base_url': UPDATE_CONFIG['internal_api_base_url'],
        'update_provider': 'qiniu', 'delivery_channel': channel,
        'output_dir': f'build/updates/{channel}/{{version}}',
        'package': {'type': 'portable', 'main_executable': EXECUTABLE_NAME},
    }
    if any(config.get(key) != value for key, value in expected.items()):
        parser.error(f'Mismatched publishing configuration: {path.name}')
    output = ROOT / config['output_dir'].format(version=VERSION)
    if args.action == 'build':
        if args.runtime_bundle is None:
            parser.error('build requires --runtime-bundle')
        command = [
            sys.executable, 'tools/packaging/build_velopack.py', '--channel', channel,
            '--output', str(output), '--runtime-bundle', str(args.runtime_bundle.resolve()),
        ]
    elif args.action == 'freeze':
        command = ['yt-software-publish', 'build', '--config', str(path), '--version', VERSION,
                   '--notes', 'tools/packaging/RELEASE_NOTES.md']
    else:
        app = ROOT / 'artifacts/dist/velopack' / channel / UPDATE_CONFIG['pack_id']
        command = [sys.executable, 'tools/packaging/smoke_velopack.py', '--app', str(app)]
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
