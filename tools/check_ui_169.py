"""1.6.9 negative layout gaps, clear checks, recording ordering and web arrows."""
import json
from pathlib import Path
import sys
from unittest.mock import patch,Mock
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtCore import Qt,QPoint
from anclicker.platform.qt_compat.QtWidgets import QApplication,QWidget,QTableWidget,QLabel,QComboBox
from anclicker.domain.window_arrangement import layout_rectangles
from anclicker.domain.instructions import InstructionDraft
from anclicker.ui.instruction_editors.其他.窗口排布 import InstructionEditor as ArrangementEditor
from anclicker.ui.instruction_editors.网页自动化.点击元素 import InstructionEditor as ClickEditor
from anclicker.ui.recording_view import RecordingView
from anclicker.ui.recording_preview_menu import RecordingPreviewMenu
from anclicker.ui.flow_tips import TIPS


class Preview(QWidget):
    render_preview=RecordingView.render_preview
    def __init__(self):
        super().__init__();self.preview=QTableWidget(0,3,self);self.status=QLabel(self)
        self.drafts=[InstructionDraft('时间等待',{'时长':i}) for i in range(5)]
        self.busy=False;self.written=False;self.update_buttons=Mock();self.render_preview()


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    windows=[{'窗口标题':str(i),'窗口句柄':str(i+1),'进程ID':77,'rect':[0,0,400,300]} for i in range(2)]
    parameters={'排布版本':2,'排布方式':'平铺','行数':1,'列数':2,'边距':-20,'间距':-10}
    for mode in ('平铺','网格'):
        result=layout_rectangles(windows,(0,0,1000,800),dict(parameters,排布方式=mode))
        assert result==[(-20,-20,525,840),(495,-20,525,840)],result
        assert result[0][0]+result[0][2]>result[1][0] and result[-1][0]+result[-1][2]>1000
    with patch('anclicker.ui.instruction_editors.其他.窗口排布.list_windows',return_value=windows),patch('anclicker.ui.instruction_editors.其他.窗口排布.list_screens',return_value=[{'id':'test','rect':[0,0,1000,800],'work':[0,0,1000,800],'primary':True,'scale':100}]):
        editor=ArrangementEditor();editor.show();app.processEvents()
        for key,value in parameters.items():editor._set_control_value(editor._controls[key],value)
        editor.ui.selectAll.click();assert len(editor._checked())==2
        editor.ui.searchEdit.setText('0');assert editor.ui.windowTree.topLevelItem(1).isHidden()
        editor.ui.clearChecksButton.click();assert not editor._checked() and not editor.ui.selectAll.isChecked()
        assert json.loads(editor._controls['窗口列表'].text())==[]
        editor.ui.searchEdit.clear();editor.ui.selectAll.click()
        assert editor.get_draft().parameters['边距']==-20
        proof=Path('artifacts/validation');proof.mkdir(parents=True,exist_ok=True)
        editor.grab().save(str(proof/'arrangement-169.png'));editor.close();editor.status_timer.stop()
    print('PASS negative gaps overlap windows; negative margins allow off-screen placement; clear checks includes filtered-out windows',flush=True)
    view=Preview();menu=RecordingPreviewMenu(view)
    ids=lambda:[d.parameters['时长'] for d in view.drafts]
    menu.move_rows([1,2],-1);assert ids()==[1,2,0,3,4]
    assert sorted({i.row() for i in view.preview.selectedIndexes()})==[0,1]
    menu.move_rows([0,1],1);assert ids()==[0,1,2,3,4]
    menu.move_rows([0,2],-1);assert ids()==[0,2,1,3,4]
    menu.move_rows([3,4],1);assert ids()==[0,2,1,3,4]
    before=list(view.drafts);view.busy=True;menu.move_rows([1],1);assert view.drafts==before
    view.busy=False;view.written=True;menu.move_rows([1],1);assert view.drafts==before
    view.written=False;view.preview.selectRow(1)
    def choose(popup,point):
        assert [a.text() for a in popup.actions()][:2]==['上移','下移']
        return popup.actions()[1]
    with patch('anclicker.ui.recording_preview_menu.QMenu.exec',choose):menu.show_menu(view.preview.visualItemRect(view.preview.item(1,0)).center())
    assert ids()==[0,1,2,3,4]
    view.close();print('PASS recording multi-row order/selection, boundaries, read-only guards and context-menu action',flush=True)
    click=ClickEditor();click.show();app.processEvents()
    combos=click.findChildren(QComboBox);assert combos and all(c.property('compactWebArrow') for c in combos)
    for combo in combos:
        assert combo.width()>24 and combo.height()>=combo.fontMetrics().height()+2
        combo.showPopup();app.processEvents();combo.hidePopup()
    click.grab().save(str(proof/'web-dropdown-169.png'));click.close()
    assert any('水果忍者' in tip for tip in TIPS) and any('空白区域' in tip and '确认' in tip for tip in TIPS)
    print('PASS web arrow area is compact while fields remain readable; tips describe implemented cut and error-node gestures',flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
