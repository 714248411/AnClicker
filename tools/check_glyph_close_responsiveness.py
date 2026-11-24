import os,sys,tempfile,time,importlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ['QT_QPA_PLATFORM']='windows'
from types import SimpleNamespace
from PIL import Image
from anclicker.platform.qt_compat import BINDING
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow,QWidget,QVBoxLayout,QPushButton,QDialog
from anclicker.platform.qt_compat.QtCore import Qt,QTimer
from anclicker.domain.instructions import ExecutionContext
from anclicker.instructions.registry import INSTRUCTION_SPECS
from anclicker.ui.node_editor.palette import InstructionPalette
from anclicker.ui.instruction_editors.vision_tools import open_glyph_tool
from anclicker.platform.vision_tools import runtime
QTest=importlib.import_module(BINDING+'.QtTest').QTest
app=QApplication([]);app.setQuitOnLastWindowClosed(False)
def pump(seconds=.12):
    end=time.monotonic()+seconds
    while time.monotonic()<end:app.processEvents();time.sleep(.005)
with tempfile.TemporaryDirectory() as tmp:
    host=QMainWindow();central=QWidget();layout=QVBoxLayout(central);host.setCentralWidget(central)
    palette=InstructionPalette(INSTRUCTION_SPECS);layout.addWidget(palette)
    button=QPushButton('主界面可点击');layout.addWidget(button);clicks=[];button.clicked.connect(lambda:clicks.append(1))
    context=ExecutionContext(metadata={'database':SimpleNamespace(db_path=str(Path(tmp)/'test.db'))})
    palette.glyphToolRequested.connect(lambda:open_glyph_tool(host,context),Qt.QueuedConnection)
    host.resize(450,650);host.show();pump()
    for index in range(12):
        item=palette._glyph_tool_item;item.parent().setExpanded(True);palette.tree.scrollToItem(item);pump(.03)
        rect=palette.tree.visualItemRect(item)
        QTest.mouseClick(palette.tree.viewport(),Qt.LeftButton,Qt.NoModifier,rect.center());pump(.03)
        QTest.mouseDClick(palette.tree.viewport(),Qt.LeftButton,Qt.NoModifier,rect.center());pump()
        tool=host._glyph_library_tool
        assert tool and tool.isVisible() and not tool.isModal()
        assert open_glyph_tool(host,context) is tool
        if index%3==0:QTest.mouseClick(tool.ui.closeToolButton,Qt.LeftButton)
        elif index%3==1:tool.close()
        else:QTest.keyClick(tool,Qt.Key_Escape)
        pump();assert host._glyph_library_tool is None
        assert QApplication.activeModalWidget() is None
        QTest.mouseClick(button,Qt.LeftButton);pump(.02)
        assert len(clicks)==index+1
    print('PASS actual palette double-click; close button, window X and Escape; 12 reopen cycles; main controls remain clickable')
    tool=open_glyph_tool(host,context);pump()
    child=QDialog(tool);child.setModal(True);child.show();pump()
    tool.close();pump();assert QApplication.activeModalWidget() is None
    print('PASS closing tool also dismisses child modal windows')
    tool=open_glyph_tool(host,context);tool._controls['目标文字'].setText('A');tool.remember_capture(Image.new('RGB',(30,30),'white'),(0,0,30,30));pump()
    original=runtime.execute;calls=[]
    def slow(*args):calls.append(1);time.sleep(.6);return 1
    runtime.execute=slow
    ticks=[];timer=QTimer();timer.setInterval(10);timer.timeout.connect(lambda:ticks.append(1));timer.start()
    QTest.mouseClick(tool.ui.saveGlyphButton,Qt.LeftButton);tool.start_save();pump(.15)
    assert len(ticks)>5 and len(calls)==1 and not tool.ui.saveGlyphButton.isEnabled()
    tool.close();pump(.7)
    assert host._glyph_library_tool is None and QApplication.activeModalWidget() is None
    assert not any(w.isVisible() and w.windowTitle()=='制作字库' for w in app.topLevelWidgets())
    QTest.mouseClick(button,Qt.LeftButton);assert len(clicks)==13
    runtime.execute=original;timer.stop()
    tool=open_glyph_tool(host,context);tool._controls['目标文字'].setText('A')
    tool.remember_capture(Image.new('RGB',(30,30),'white'),(0,0,30,30))
    QTest.mouseClick(tool.ui.saveGlyphButton,Qt.LeftButton)
    for _ in range(100):
        pump(.03)
        if tool._save_job is None:break
    assert '保存失败' in tool.ui.status.text() and tool.ui.saveGlyphButton.isEnabled()
    import cv2,numpy as np
    frame=np.zeros((40,50,3),np.uint8);cv2.putText(frame,'A',(5,30),cv2.FONT_HERSHEY_SIMPLEX,.8,(255,255,255),2)
    tool.remember_capture(Image.fromarray(frame),(0,0,50,40));QTest.mouseClick(tool.ui.saveGlyphButton,Qt.LeftButton)
    for _ in range(100):
        pump(.03)
        if tool._save_job is None:break
    assert '已保存 1 个字' in tool.ui.status.text() and (Path(tmp)/'glyphs'/'index.json').is_file()
    tool.close();pump();assert QApplication.activeModalWidget() is None
    print('PASS real asynchronous save succeeds; save errors stay inline and re-enable controls')
    host.close();pump()
    print('PASS slow save does not block event loop; duplicate save ignored; close during save does not reopen or lock main window')
