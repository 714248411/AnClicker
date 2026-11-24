"""Run isolated functional regressions and retain individual evidence."""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.7.3'
CASES=["check_step_folding","check_fold_lock","check_fold_borders","check_dynamic_folding","check_nested_collapse","check_stack_group","check_locked_delete","check_locked_copy","check_loop_group_move","check_table_instruction_drop","check_table_flow_164","check_typed_conditions","check_condition_point_select","check_print_log","check_table_columns","check_flow_long_parameters","check_dual_pipeline","check_role_compiler","check_conversational_contracts","check_chinese_steps","check_model_library","check_recommended_dual","check_draft_verification","check_workflow_patch","check_workflow_mermaid","check_stop2_shortcut","check_window_arrangement_165","check_cmd_paths","check_cmd_batch_templates","check_agent_context_menus","check_agent_capabilities","check_recent_compact_settings"]
OUT.mkdir(parents=True,exist_ok=True)
CASES += ['check_image_regions_173','check_window_input','check_window_keyboard','check_window_multi_click','check_window_text_position','check_window_trigger','check_window_geometry','check_window_image','check_all_instruction_combos','check_settings_combo_rows','check_table_header_layout','check_timing_layout','check_window_settings_footer','check_background_window_crash']
results=[]
for name in CASES:
 start=time.perf_counter()
 env=dict(os.environ,QT_QPA_PLATFORM='windows',PYTHONPATH=str(ROOT),PYTHONIOENCODING='utf-8')
 try:
  result=subprocess.run([sys.executable,str(ROOT/'tools'/f'{name}.py')],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
  code,output=result.returncode,result.stdout+result.stderr
 except subprocess.TimeoutExpired:
  code,output=-1,'Timed out after 180 seconds'
 (OUT/f'{name}.log').write_text(output,encoding='utf8')
 results.append(dict(case=name,returncode=code,seconds=round(time.perf_counter()-start,3)))
 print(('PASS ' if code==0 else 'FAIL ')+name,flush=True)
 (OUT/'regressions.json').write_text(json.dumps(results,indent=2),encoding='utf8')
raise SystemExit(any(r['returncode']!=0 for r in results))
