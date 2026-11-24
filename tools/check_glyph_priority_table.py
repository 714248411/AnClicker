import os,sys,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));os.environ['QT_QPA_PLATFORM']='windows'
from types import SimpleNamespace
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow
from anclicker.platform.qt_compat.QtGui import QFont
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.registry import get_instruction_spec
from anclicker.ui.instruction_editors.vision_tools import GlyphLibraryTool
from anclicker.ui.instruction_editors.glyph_priority_table import GlyphPriorityTable
from anclicker.ui.settings_theme import apply_settings_theme
from anclicker.ui.theme import THEMES
app=QApplication([]);app.setFont(QFont('Microsoft YaHei',10))
records=[{'color':'红色','rgb':[255,0,0]},{'color':'蓝色','rgb':[0,0,255]},{'color':'黄色','rgb':[255,255,0]}]
d=GlyphPriorityTable('红色;蓝色',records)
assert d.table.rowCount()==3
d.table.setCurrentCell(1,1);d.move_row(-1)
d.table.item(0,1).setText('优先蓝');d.table.item(0,2).setText('0，0，240');d.table.item(0,3).setText('30')
value,config=d.collect();assert value=='优先蓝;红色'
rows=json.loads(config);assert rows[0]['rgb']==[0,0,240] and rows[0]['tolerance']==30
reopened=GlyphPriorityTable(value,records,config);assert reopened.table.item(0,1).text()=='优先蓝' and reopened.table.item(0,3).text()=='30'
raw=GlyphPriorityTable('192,40,21',[]);assert raw.collect()[0]=='192,40,21';raw.close()
with tempfile.TemporaryDirectory() as tmp:
 ctx=ExecutionContext(metadata={'database':SimpleNamespace(db_path=str(Path(tmp)/'test.db'))})
 editor=get_instruction_spec('字库点击').create_editor(context=ctx)
 def buttons(row):return [row.itemAt(i).widget().text() for i in range(row.count()) if row.itemAt(i).widget()]
 assert buttons(editor.ui.secondaryTools)==['识图预览（不点击）','字库查看','选择字库目录']
 assert buttons(editor.ui.tools).index('吸取优先色')<buttons(editor.ui.tools).index('选择优先色')
 editor._controls['优先色配置'].setText(config);assert json.loads(editor.parameters()['优先色配置'])[0]['name']=='优先蓝'
 tool=GlyphLibraryTool(context=ctx);assert buttons(tool.ui.secondaryTools)==['字库查看','选择字库目录']
 host=QMainWindow();host.view_workspace=SimpleNamespace(THEMES=THEMES,theme_mode='light')
 out=Path('artifacts/validation/glyph-priority');out.mkdir(parents=True,exist_ok=True)
 for mode in ('light','dark'):
  host.view_workspace.theme_mode=mode
  for name,widget in [('table',d),('editor',editor),('tool',tool)]:
   apply_settings_theme(widget,host);widget.setAttribute(Qt.WA_DontShowOnScreen,True);widget.show();app.processEvents();widget.grab().save(str(out/(name+'-'+mode+'.png')));widget.hide()
 editor.close();tool.close()
d.close();reopened.close()
print('PASS second-row buttons and swapped order; table move/edit/toggle, custom name/RGB/tolerance roundtrip, raw RGB entries, hidden per-instruction config, light/dark render')
