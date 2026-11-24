"""Explicit opt-in to the trained converter; verifies model hash and keeps rollback config."""
import argparse,json,hashlib,datetime
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
root=Path(args.root).resolve();models=root/'models';name='anclicker-v6_5-dpo-converter-q4_0.gguf';model=models/name
report=json.loads((models/'anclicker-v6_5-dpo-converter/deployment-manifest.json').read_text(encoding='utf8'))
if not report.get('runtime_verified') or not report.get('generation_improved'):raise SystemExit('Model runtime verification is not complete')
h=hashlib.sha256()
with model.open('rb') as f:
 if f.read(4)!=b'GGUF':raise SystemExit('Invalid GGUF')
 f.seek(0)
 for part in iter(lambda:f.read(8*1024*1024),b''):h.update(part)
if h.hexdigest()!=report['gguf_sha256']:raise SystemExit('Model hash mismatch')
path=models/'dual_model.json';current=json.loads(path.read_text(encoding='utf8'));new={**current,'enabled':True,'converter':name}
print(json.dumps(new,ensure_ascii=False,indent=2))
if args.apply:
 backup=path.with_name('dual_model.before-dpo-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json')
 backup.write_bytes(path.read_bytes());temporary=path.with_suffix('.dpo.tmp');temporary.write_text(json.dumps(new,ensure_ascii=False,indent=2),encoding='utf8');temporary.replace(path)
 print('Applied. Restart AnClicker. Roll back by restoring:',backup)
else:print('Preview only; pass --apply to activate.')
