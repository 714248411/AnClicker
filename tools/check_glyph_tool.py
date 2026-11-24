import os,sys,tempfile,sqlite3,contextlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import cv2,numpy as np
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import Qt
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.registry import INSTRUCTION_SPECS,get_instruction_spec
from anclicker.storage.database import DatabaseOperation
from anclicker.ui.instruction_editors.vision_tools import GlyphLibraryTool
from anclicker.ui.node_editor.palette import InstructionPalette,TYPE_ID_ROLE
from anclicker.platform.vision_tools.runtime import execute
app=QApplication([])
assert all(s.type_id!='制作字库' for s in INSTRUCTION_SPECS)
palette=InstructionPalette(INSTRUCTION_SPECS)
item=palette._glyph_tool_item
assert item and item.data(0,TYPE_ID_ROLE) is None
assert not item.flags() & Qt.ItemIsDragEnabled
opened=[];created=[]
palette.glyphToolRequested.connect(lambda:opened.append(True))
palette.instructionActivated.connect(created.append)
palette.tree.itemDoubleClicked.emit(item,0)
assert opened and not created
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp);db=DatabaseOperation(str(root/'命令集.db'))
    image=np.zeros((50,100,3),np.uint8);cv2.putText(image,'AB',(5,30),cv2.FONT_HERSHEY_SIMPLEX,.8,(0,0,255),2)
    clicks=[]
    context=ExecutionContext(metadata={'database':db},services={'离线视觉截图':lambda p:(image,(0,0),None),'离线视觉输入':lambda *args:clicks.append(args)})
    def snapshot():
        with contextlib.closing(sqlite3.connect(db.db_path)) as conn:
            return [conn.execute('SELECT * FROM '+name).fetchall() for name in ('命令','节点','节点连接')]
    before=snapshot()
    tool=GlyphLibraryTool(context=context,parameters={'区域':'0,0,100,50','目标文字':'AB'})
    assert not hasattr(tool.ui,'repeatSpinBox') and not hasattr(tool,'test_requested')
    assert str(root/'glyphs') in tool._controls['字库目录'].placeholderText()
    tool.save_glyphs()
    assert (root/'glyphs'/'index.json').is_file() and snapshot()==before
    execute('字库点击',{'区域':'0,0,100,50','目标文字':'AB'},context)
    assert clicks and snapshot()==before
    editor=get_instruction_spec('字库点击').create_editor(context=context)
    assert editor._controls['字库目录'].text()=='' and str(root/'glyphs') in editor._controls['字库目录'].placeholderText()
    editor.close();tool.close()
print('PASS standalone glyph tool has no flow controls or draggable instruction; saves default library without changing graph; click automatically finds default library')
