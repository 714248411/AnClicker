"""Local verification receipts; these are caches, not signatures or upload assets."""
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from info import UPDATE_CONFIG, update_source_config


def fingerprint(context, stage):
    files = {}
    def record(path, key):
        if path.is_symlink():
            raise ValueError(f'Validation does not accept symlinks: {path}')
        if path.is_file():
            checksum = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    checksum.update(chunk)
            files[key] = [path.stat().st_size, checksum.hexdigest()]

    for path in context.app_dir.rglob('*'):
        record(path, 'app/' + path.relative_to(context.app_dir).as_posix())
    for path in context.release_dir.rglob('*'):
        relative = path.relative_to(context.release_dir)
        if relative.as_posix() in ('validation-startup.json', 'validation-publish.json'):
            continue
        # The build exports delivery and normalizes the feed after the startup gate.
        if stage == 'startup' and (relative.parts[0] == 'delivery' or relative.as_posix() == UPDATE_CONFIG['feed_name']):
            continue
        record(path, 'release/' + relative.as_posix())
    for path in (context.project_root / 'packaging').iterdir():
        if path.suffix in ('.py', '.spec', '.manifest'):
            record(path, 'code/' + path.name)
    record(context.project_root / 'info.py', 'code/info.py')
    return {'schema': 1, 'stage': stage, 'context': {k: str(v) for k, v in asdict(context).items()},
            'source': update_source_config(), 'files': files}


def verify_once(context, stage, verify):
    """Reuse only exact content matches; otherwise perform the full verification."""
    if stage not in ('startup', 'publish'):
        raise ValueError('Unknown validation stage')
    receipt = context.release_dir / f'validation-{stage}.json'
    before = fingerprint(context, stage)
    try:
        saved = json.loads(receipt.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        saved = None
    if saved == before:
        print(f'[{stage}] 产物哈希未变，复用验收记录，不重复启动窗口。', flush=True)
        return
    print(f'[{stage}] 执行完整验收；通过后保存记录。', flush=True)
    verify()
    if fingerprint(context, stage) != before:
        raise RuntimeError('验收期间产物发生变化，不能保存验收结果')
    receipt.write_text(json.dumps(before, ensure_ascii=False, sort_keys=True, indent=2), encoding='utf-8')
