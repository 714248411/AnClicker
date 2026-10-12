import os, sys, tempfile, json
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='windows'
from qt_compat.QtWidgets import QApplication
from 数据库操作 import DatabaseOperation
from instructions.registry import get_instruction_spec
from instructions.models import ExecutionContext
from ui_validation import validate_instruction_editors
app=QApplication([])
out=Path('validation');out.mkdir(exist_ok=True)
class Hotkeys:
    def register(self,*args,**kwargs): pass
    def unregister(self,*args,**kwargs): pass
with tempfile.TemporaryDirectory() as temp:
    db=DatabaseOperation(str(Path(temp)/'preview.db'))
    with patch('Start_Win.DatabaseOperation',return_value=db), patch('main_work.DatabaseOperation',return_value=db), patch('Start_Win.SystemHotkey',Hotkeys), patch('Start_Win.is_hotkey_valid',return_value=True):
        from Start_Win import Main_window
        window=Main_window()
    window.resize(1450,900);window.show();app.processEvents()
    report=validate_instruction_editors(window)
    from instructions.models import InstructionDraft
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
