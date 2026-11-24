"""Frozen startup with Data produced by historical 1.7.8 source."""
import json,os,shutil,sqlite3,subprocess,tempfile,uuid,contextlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.9.0'
lines=(OUT/'check_two_version_data.log').read_text(encoding='utf8').splitlines()
proof=json.loads(next(line for line in reversed(lines) if line.startswith('{')))
source=Path(proof['directory'])/'old-offline/Data'
exe=ROOT/'artifacts/dist/v1.9.0/AnClicker/AnClicker.exe'
with tempfile.TemporaryDirectory(prefix='ac-frozen-legacy-') as td:
 data=Path(td)/'Data';shutil.copytree(source,data)
 expected=json.loads((data/'expected.json').read_text(encoding='utf8'))
 for run in range(2):
  env=dict(os.environ,ANCLICKER_DATA_DIR=str(data),ANCLICKER_SINGLETON_KEY=uuid.uuid4().hex,ANCLICKER_SMOKE_LIGHTWEIGHT='1',PYTHONDONTWRITEBYTECODE='1')
  subprocess.run([str(exe),'--release-smoke'],cwd=td,env=env,check=True,timeout=90,capture_output=True)
  with contextlib.closing(sqlite3.connect(data/'命令集.db')) as conn:
   rows=conn.execute('SELECT ID,类型标识,参数JSON,备注 FROM 命令 ORDER BY 排序').fetchall()
   assert len(rows)==142
   for row,saved in zip(rows,expected):
    assert row[0]==saved['id'] and row[1]==saved['type'] and (row[3] or '')==(saved['note'] or '')
   for _,kind,raw,_ in rows[-3:]:
    key={'图像点击':'图像路径','获取Excel':'工作簿','运行外部文件':'文件路径'}[kind]
    path=Path(json.loads(raw)[key]);path=path if path.is_absolute() else data/path
    # Startup must preserve imported command paths until adaptation is accepted.
    saved=next(item for item in expected if item['type']==kind)
    assert json.loads(raw)[key]==saved['parameters'][key]
   current=Path(conn.execute("SELECT 值 FROM 设置 WHERE 设置项='当前文件路径'").fetchone()[0])
   assert current.is_file() and current.is_relative_to(data)
  print('PASS frozen historical Data: 142 commands and unchanged input paths before consent, launch '+str(run+1),flush=True)
(OUT/'frozen-legacy-data.json').write_text(json.dumps({'passed':True,'commands':142,'old_source':'1.7.8','launches':2}))
