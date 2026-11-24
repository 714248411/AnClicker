import json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/validation/v1.8.8'
CASES=["check_default_layout","check_instruction_thumbnails","check_flow_thumbnails","check_table_move_selection","check_crawl_image_save","check_web_table_layout","check_window_corner_resize","check_window_edges","check_background_presets_offline","check_background_preload_native","check_scroll_element","check_scroll_element_ui"]
results=[]
for name in CASES:
 start=time.monotonic()
 try:
  result=subprocess.run([sys.executable,'-B','-X','utf8','tools/'+name+'.py'],cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=180)
  code,output=result.returncode,result.stdout+result.stderr
 except subprocess.TimeoutExpired:code,output=-1,'Timed out after 180 seconds'
 (OUT/(name+'.log')).write_text(output,encoding='utf8')
 results.append({'case':name,'returncode':code,'seconds':round(time.monotonic()-start,3)})
 print(('PASS ' if code==0 else 'FAIL ')+name,flush=True)
 (OUT/'extras.json').write_text(json.dumps(results,indent=2))
raise SystemExit(any(r['returncode']!=0 for r in results))
