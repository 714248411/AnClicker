"""Integration checks for CMD batch templates using isolated disposable fixtures."""
import os
from pathlib import Path
import subprocess
import tempfile
import time
from anclicker.domain.cmd_templates import TEMPLATES, render_template

def run(name, **values):
    template = next(t for t in TEMPLATES if t[1] == name)
    command = render_template(template, values)
    result = subprocess.run(command, shell=True, capture_output=True, timeout=30)
    assert result.returncode == 0, (name, command, result.stdout, result.stderr)
    return result.stdout

with tempfile.TemporaryDirectory(prefix='anclicker cmd ') as temporary:
    base = Path(temporary)
    source = base / 'source space'
    source.mkdir()
    sub = source / 'sub'
    sub.mkdir()
    (source / 'a file.txt').write_text('error first\nhello\n', encoding='ascii')
    (source / 'b.txt').write_text('error second\n', encoding='ascii')
    (sub / 'c.txt').write_text('error nested\n', encoding='ascii')
    log = source / 'old.log'
    log.write_text('old', encoding='ascii')
    os.utime(log, (time.time()-86400*40, time.time()-86400*40))
    pattern = str(source / '*.txt')
    values = dict(folder=str(source), pattern=pattern, output=str(base/'result.txt'))
    run('按类型批量复制', pattern=pattern, target=str(base/'copy'))
    assert (base/'copy'/'a file.txt').exists() and not (base/'copy'/'sub').exists()
    run('递归批量复制指定类型', pattern=pattern, target=str(base/'recursive'))
    assert (base/'recursive'/'sub'/'c.txt').exists()
    run('预览增量备份清单', folder=str(source), target=str(base/'preview'))
    assert not (base/'preview').exists()
    run('增量备份文件夹', folder=str(source), target=str(base/'backup'))
    assert (base/'backup'/'sub'/'c.txt').exists()
    run('导出递归文件清单', **values)
    assert b'c.txt' in (base/'result.txt').read_bytes()
    run('导出目录清单', **values)
    assert b'sub' in (base/'result.txt').read_bytes()
    run('导出目录树', **values)
    assert b'a file.txt' in (base/'result.txt').read_bytes()
    assert b'nested' in run('递归搜索文本行', pattern=pattern, text='error')
    assert b'c.txt' in run('列出包含关键词的文件', pattern=pattern, text='error')
    run('递归设置文件只读', pattern=pattern)
    assert (source/'a file.txt').stat().st_file_attributes & 1
    run('递归取消文件只读', pattern=pattern)
    assert not (source/'a file.txt').stat().st_file_attributes & 1
    assert b'old.log' in run('查找多天未修改的文件', folder=str(source), mask='*.log', days='30')
    run('批量创建编号目录', folder=str(base/'numbered'), count='3')
    assert all((base/'numbered'/str(i)).is_dir() for i in range(1,4))
    assert b'SHA256' in run('批量计算 SHA256', pattern=pattern)
    run('排序文本清单', file=str(source/'a file.txt'), output=str(base/'sorted.txt'))
    assert (base/'sorted.txt').exists()
    run('批量修改扩展名', pattern=pattern, extension='*.bak')
    assert (source/'a file.bak').exists() and (sub/'c.txt').exists()
    for kind, invalid in [('查找多天未修改的文件', {'days':'-1'}), ('批量修改扩展名', {'extension':'other.txt'})]:
        try:
            render_template(next(t for t in TEMPLATES if t[1]==kind), invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(kind)
print('PASS: all 16 batch templates executed on isolated fixtures; scope, output and validation verified')
