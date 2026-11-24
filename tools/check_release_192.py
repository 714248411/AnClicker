"""Run isolated functional regressions and retain individual evidence."""
import json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/validation/v1.9.2'
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
CASES += ['check_palette_quick_commands','check_table_edge_resize','check_browser_caption_theme']

CASES = list(dict.fromkeys(CASES + ["check_default_layout","check_instruction_thumbnails","check_flow_thumbnails","check_table_move_selection","check_crawl_image_save","check_web_table_layout","check_window_corner_resize","check_window_edges","check_background_presets_offline","check_background_preload_native","check_scroll_element","check_scroll_element_ui","check_requested_interactions","check_schedule_parallel_modes","check_parallel_start_fanout","check_thread_groups","check_thread_group_ui","check_thread_dissolve","check_thread_relative_move","check_drag_auto_unlock","check_drag_feedback","check_drop_marker_membership","check_floating_panel_controls","check_table_context_insert","check_graph_context_columns","check_two_column_menu","check_mouse_failsafe","check_toolbar_sync","check_workspace_bundle","check_workspace_transfer_ui","check_whole_data_transfer","check_whole_data_transfer_ui","check_project_path_portability","check_save_isolation","check_main_window_state","check_locked_panel","check_resource_bundle","check_xlsm_drop"]))
CASES += ['check_menu_hover_position_run', 'check_standalone_application', 'check_single_exe', 'check_standalone_dependencies']
CASES += ['check_table_delete_menu']
import tempfile
results=[]
selected=set(sys.argv[1:])
if selected: CASES=[case for case in CASES if case in selected]
for name in CASES:
 start=time.perf_counter()
 print('START '+name,flush=True)
 sandbox=tempfile.mkdtemp(prefix='anclicker-release-191-')
 env=dict(os.environ,QT_QPA_PLATFORM='windows',ANCLICKER_DATA_DIR=sandbox,PYTHONPATH=str(ROOT),PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
 try:
  result=subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'tools'/f'{name}.py')],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240)
  code,output=result.returncode,result.stdout+result.stderr
 except subprocess.TimeoutExpired as error:
  code,output=-1,'Timed out after 240 seconds\n'+str(error.stdout or '')+str(error.stderr or '')
 (OUT/f'{name}.log').write_text(output,encoding='utf8')
 warning='Traceback (most recent call last)' in output
 results.append(dict(case=name,returncode=code,traceback=warning,seconds=round(time.perf_counter()-start,3),sandbox=sandbox))
 print(('PASS ' if code==0 and not warning else 'FAIL ')+name,flush=True)
 (OUT/('rechecks.json' if selected else 'regressions.json')).write_text(json.dumps(results,indent=2),encoding='utf8')
raise SystemExit(any(r['returncode']!=0 or r['traceback'] for r in results))
