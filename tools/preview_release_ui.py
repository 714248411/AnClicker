import os, sys, tempfile, json
from pathlib import Path
from unittest.mock import patch

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'QApplication': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QApplication',), 0),
    'DatabaseOperation': ('from', 'anclicker.storage.database', ('DatabaseOperation',), 0),
    'get_instruction_spec': ('from', 'anclicker.instructions.registry', ('get_instruction_spec',), 0),
    'ExecutionContext': ('from', 'anclicker.domain.instructions', ('ExecutionContext',), 0),
    'validate_instruction_editors': ('from', 'anclicker.app.ui_validation', ('validate_instruction_editors',), 0),
    'Main_window': ('from', 'anclicker.app.Start_Win', ('Main_window',), 0),
    'InstructionDraft': ('from', 'anclicker.domain.instructions', ('InstructionDraft',), 0),
})

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
anclicker = _module_imports.load('anclicker')  # Enable source-tree legacy entry points.
os.environ['QT_QPA_PLATFORM']='windows'
QApplication = _module_imports.load('QApplication')
DatabaseOperation = _module_imports.load('DatabaseOperation')
get_instruction_spec = _module_imports.load('get_instruction_spec')
ExecutionContext = _module_imports.load('ExecutionContext')
validate_instruction_editors = _module_imports.load('validate_instruction_editors')
app=QApplication([])
out=Path(__file__).resolve().parents[1] / 'artifacts/validation';out.mkdir(parents=True, exist_ok=True)
class Hotkeys:
    def register(self,*args,**kwargs): pass
    def unregister(self,*args,**kwargs): pass
with tempfile.TemporaryDirectory() as temp:
    db=DatabaseOperation(str(Path(temp)/'preview.db'))
    with patch('Start_Win.DatabaseOperation',return_value=db), patch('main_work.DatabaseOperation',return_value=db), patch('Start_Win.SystemHotkey',Hotkeys), patch('Start_Win.is_hotkey_valid',return_value=True):
        Main_window = _module_imports.load('Main_window')
        window=Main_window()
    window.resize(1450,900);window.show();app.processEvents()
    report=validate_instruction_editors(window)
    InstructionDraft = _module_imports.load('InstructionDraft')
    window.workspace.repository.append_recording([InstructionDraft('时间等待',{'时长':0,'单位':'秒'}) for i in range(4)],connect=False)
    window.view_workspace.refresh_table()
    window.view_workspace.show_table()
    for theme in ('light','dark'):
        window.view_workspace.theme_mode=theme;window.view_workspace._apply_theme()
        palette=window.workspace.palette
        for i in range(palette.tree.topLevelItemCount()):
            group=palette.tree.topLevelItem(i)
            group.setExpanded(group.text(0) in ('快捷功能栏','Excel','白话','网页自动化','数据抓取'))
        palette.show_recent_ocr((100,200,300,120))
        window.view_workspace.show_table()
        table=window.view_workspace.command_table;table.selectAll()
        app.processEvents()
        pixels=table.viewport().grab().toImage()
        colors=[]
        for row in range(4):
            rect=table.visualItemRect(table.item(row,2));colors.append(pixels.pixelColor(rect.right()-10,rect.center().y()).name())
        assert len(set(colors))==1,colors
        window.grab().save(str(out/('selected-table-'+theme+'.png')))
        window.view_workspace.show_web_recording()
        app.processEvents();window.grab().save(str(out/('main-'+theme+'.png')))
        for kind,filename in [('OCR点击识别区域','ocr')]:
            try: spec=get_instruction_spec(kind)
            except KeyError: continue
            editor=spec.create_editor(window,context=ExecutionContext(metadata={'database':db}))
            editor._controls['点击来源'].setCurrentText('重新识别')
            editor.ocr_advanced_button.setChecked(True)
            editor.resize(760,1000)
            editor.show();app.processEvents();editor.grab().save(str(out/(filename+'-'+theme+'.png')))
            editor.close();editor.deleteLater()
    window.close();window.deleteLater();app.processEvents()
(out/'ui-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(report)
