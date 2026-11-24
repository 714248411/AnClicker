"""Run isolated functional regressions and retain individual evidence."""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.8.7'
CASES=["check_step_folding","check_fold_lock","check_fold_borders","check_dynamic_folding","check_nested_collapse","check_stack_group","check_locked_delete","check_locked_copy","check_loop_group_move","check_table_instruction_drop","check_table_flow_164","check_typed_conditions","check_condition_point_select","check_print_log","check_table_columns","check_flow_long_parameters","check_dual_pipeline","check_role_compiler","check_conversational_contracts","check_chinese_steps","check_model_library","check_recommended_dual","check_draft_verification","check_workflow_patch","check_workflow_mermaid","check_stop2_shortcut","check_window_arrangement_165","check_cmd_paths","check_cmd_batch_templates","check_agent_context_menus","check_agent_capabilities","check_recent_compact_settings"]
OUT.mkdir(parents=True,exist_ok=True)
CASES += ['check_image_regions_173','check_window_input','check_window_keyboard','check_window_multi_click','check_window_text_position','check_window_trigger','check_window_geometry','check_window_image','check_all_instruction_combos','check_settings_combo_rows','check_table_header_layout','check_timing_layout','check_window_settings_footer','check_background_window_crash']
CASES += ['check_canvas_arrangement', 'check_flow_view_preservation']
CASES += ['check_all_editors_172', 'check_schedule_random', 'check_crawl4ai', 'check_extraction_export', 'check_web_video', 'check_web_region_bridge']
CASES += ["check_blank_formal_save","check_new_blank_full_window","check_both_panels_shortcut","check_dock_tab_alignment","check_dynamic_left","check_human_mouse","check_menu_runtime_restore","check_missing_recent_project","check_panel_arrangements","check_project_controls","check_recent_folder","check_replace_pinned_editor","check_schedule_titlebar","check_settings_sections","check_shared_start_stop","check_single_runtime_log","check_table_tips_center","check_tooltip_policy"]
CASES = list(dict.fromkeys(CASES + ["check_fold_insert_boundaries","check_dynamic_folding","check_fold_lock","check_locked_copy","check_locked_delete","check_agent_autoscroll","check_browser_titles","check_browser_network_recovery","check_settings_appearance","check_release_ui_172"]))
CASES += ['check_schedule_theme','check_image_path_relocation','check_project_folder_import','check_update_startup_policy','check_release_data_boundaries','check_portable_data_migration']
CASES += ['check_legacy_data_images','check_automatic_legacy_migration','check_graph_migration_routing','check_two_version_data','check_startup_paths']
CASES += ['check_data_partitions','check_imported_project_recents','check_glyph_capture_interaction','check_glyph_close_responsiveness','check_glyph_colors','check_glyph_color_ui','check_glyph_matching','check_glyph_priority_table','check_glyph_tool','check_glyph_workflow','check_color_picker_order','check_guard_health','check_guard_picker_zoom','check_parallel_runtime','check_parallel_ui']
CASES += ['check_cdp_discovery','check_external_web_ui','check_window_control_geometry','check_background_timeout']
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
