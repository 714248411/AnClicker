"""Verify the packaged channel and the exact release inputs before SDK freeze."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from info import APP_ID, EXECUTABLE_NAME, UPDATE_CHANNELS, UPDATE_CONFIG, VERSION, update_source_config


def verify(output, channel, version):
    snapshot = update_source_config(channel)
    feed = json.loads((output / UPDATE_CONFIG['feed_name']).read_text(encoding='utf-8-sig'))
    full_name = f"{APP_ID}-{version}-{snapshot['runtime']}-full.nupkg"
    assets = [asset for asset in feed['Assets'] if asset['Version'] == version]
    if len(assets) != 1:
        raise ValueError('The internal transition must contain one Full update')
    asset = assets[0]
    if (asset['PackageId'], asset['Type'], asset['FileName']) != (APP_ID, 'Full', full_name):
        raise ValueError('Update asset does not match the project identity')
    package = output / full_name
    digest = hashlib.sha256()
    with package.open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(chunk)
    if package.stat().st_size != asset['Size'] or digest.hexdigest() != asset['SHA256'].lower():
        raise ValueError('Full package hash or size differs from the feed')
    with ZipFile(package) as archive:
        if json.loads(archive.read(f"lib/app/{UPDATE_CONFIG['snapshot_name']}")) != snapshot:
            raise ValueError('Full package channel does not match the publishing channel')
        archive.getinfo(f'lib/app/{EXECUTABLE_NAME}')
    with ZipFile(output / UPDATE_CONFIG['portable_name']) as archive:
        if json.loads(archive.read(f"current/{UPDATE_CONFIG['snapshot_name']}")) != snapshot:
            raise ValueError('Portable package channel does not match the publishing channel')
    return asset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel', required=True, choices=UPDATE_CHANNELS)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.version != VERSION:
        parser.error(f'Expected version {VERSION} from info.py')
    asset = verify(args.output, args.channel, args.version)
    print(f"Verified {args.channel}: {asset['FileName']} {asset['SHA256']}")


if __name__ == '__main__':
    main()
