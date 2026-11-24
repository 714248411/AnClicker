"""Real Qt drops: composer cursor insertion, CMD paths, file settings and routing."""
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import QMimeData,QUrl,Qt,QPoint,QPointF
from anclicker.platform.qt_compat.QtGui import QDragEnterEvent,QDragMoveEvent,QDropEvent
from anclicker.platform.qt_compat.QtWidgets import QApplication,QMainWindow,QStatusBar
from anclicker.ui.agent_view import Composer
from anclicker.ui.recent_projects import ProjectDropFilter
from anclicker.ui.instruction_editors.其他.运行cmd import InstructionEditor as CmdEditor
from anclicker.ui.instruction_editors.其他.快速文件操作 import InstructionEditor as FileEditor
from anclicker.ui.instruction_editors.其他.运行外部文件 import InstructionEditor as LaunchEditor
from anclicker.ui.instruction_editors.网页自动化.网页截图 import InstructionEditor as ScreenshotEditor
from anclicker.domain.cmd_templates import TEMPLATES


def drop(control,paths,remote=False):
    mime=QMimeData();mime.setUrls([QUrl(path) if remote else QUrl.fromLocalFile(str(path)) for path in paths])
    surface=control.viewport() if hasattr(control,'viewport') else control
    enter=QDragEnterEvent(QPoint(5,5),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
    QApplication.sendEvent(surface,enter)
    if not enter.isAccepted():return False
    move=QDragMoveEvent(QPoint(5,5),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
    QApplication.sendEvent(surface,move)
    event=QDropEvent(QPointF(5,5),Qt.CopyAction,mime,Qt.LeftButton,Qt.NoModifier)
    QApplication.sendEvent(surface,event)
    return event.isAccepted()


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix='anclicker-drop-') as folder:
        folder=Path(folder);file=folder/'中文 文件.xlsx';file.write_bytes(b'fixture');other=folder/'另一个.py';other.write_text('pass');sub=folder/'中文 文件夹';sub.mkdir()
        main=QMainWindow();main.statusBar=QStatusBar(main);composer=Composer(main);main.setCentralWidget(composer);main.show();app.processEvents()
        opened=Mock();filter=ProjectDropFilter(main,opened)
        composer.setPlainText('前半后半');cursor=composer.textCursor();cursor.setPosition(2);composer.setTextCursor(cursor)
        submitted=Mock();composer.submitted.connect(submitted)
        assert drop(composer,[file]);assert composer.toPlainText()=='前半'+os.path.normpath(str(file))+'后半',composer.toPlainText()
        assert not opened.called and not submitted.called
        composer.undo();assert composer.toPlainText()=='前半后半'
        assert drop(composer,[file,other,sub]);assert '\n'.join(map(lambda p:os.path.normpath(str(p)),[file,other,sub])) in composer.toPlainText()
        before=composer.toPlainText();assert not drop(composer,['https://example.com/test'],remote=True);assert composer.toPlainText()==before
        print('PASS composer inserts local paths at existing cursor, preserves text/undo, supports multiple Chinese/spaced paths, never opens Excel as project or submits',flush=True)
        cmd=CmdEditor();cmd.show();app.processEvents();checked=0
        for index,template in enumerate(TEMPLATES):
            fields=[field for field in template[4] if field[3] in ('folder','file','save')]
            if not fields:continue
            combo_index=cmd.template_combo.findData(index)
            cmd._choose_template(combo_index)
            for key,label,default,kind in fields:
                target=sub if kind=='folder' else file
                assert drop(cmd._parameters[key],[target]),(template[0],key)
                assert cmd._parameters[key].text()==os.path.normpath(str(target))
                checked+=1
        assert checked>10,checked
        print('PASS all '+str(checked)+' CMD template path fields accept drops and update their parameter signals',flush=True)
        for cls,keys in ((FileEditor,('源路径','目标路径')),(LaunchEditor,('文件路径',)),(ScreenshotEditor,('path',))):
            editor=cls();editor.show();app.processEvents()
            for key in keys:
                assert drop(editor._controls[key],[file]),key
                assert editor.get_draft().parameters[key]==os.path.normpath(str(file)),key
                before=editor._controls[key].text();assert not drop(editor._controls[key],[file,other]);assert editor._controls[key].text()==before
            editor.close()
        print('PASS file source/destination, launch-file and web screenshot paths save dropped values; single-path fields reject multiple files',flush=True)
        app.removeEventFilter(filter);cmd.close();main.close()
    return 0


if __name__=='__main__':raise SystemExit(main())
