import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.colloquial_expanded_judge import judge
path=Path(sys.argv[1]);data=json.loads(path.read_text(encoding='utf8'))
for row in data['cases']:
 errors=[row['error']] if 'error' in row else judge(row,row['response'])
 if 'distance' in row and not any(x['parameters'].get('距离')==row['distance'] for x in row.get('response',{}).get('arguments',{}).get('instructions',[])):errors.append('滚动格数不符')
 row.update(errors=errors,passed=not errors)
print(json.dumps({'passed':sum(r['passed'] for r in data['cases']),'total':len(data['cases']),'failures':[r for r in data['cases'] if not r['passed']]},ensure_ascii=False,indent=2))
if len(data['cases'])==48:path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
