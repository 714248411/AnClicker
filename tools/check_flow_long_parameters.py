"""Long code must not make fit-to-view shrink the entire workflow."""
from pathlib import Path
import sys
from copy import deepcopy
if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.qt_compat import configure_application
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtGui import QColor
from anclicker.ui.node_editor.scene import NodeScene
from anclicker.ui.node_editor.view import NodeView
from anclicker.ui.node_editor.items import NodeItem
from anclicker.ui.node_editor import style


def main():
    configure_application();app=QApplication.instance() or QApplication([])
    code='payload = '+repr('x'*100000)+'\nprint(payload)\n'
    records=[{'node_id':'python','command_id':1,'type_id':'运行Python','parameters':{'代码':code},'repeat_count':2},
             {'node_id':'wait','command_id':2,'type_id':'时间等待','parameters':{'时长':1},'y':120}]
    original=deepcopy(records)
    scene=NodeScene();scene.load_graph(records,[],{})
    node=scene.nodes_by_command_id[1]
    assert node.width<=360 and '2 行' in node.subtitle and '重复 ×2' in node.subtitle
    assert records==original and records[0]['parameters']['代码']==code
    assert '双击编辑完整参数' in node.toolTip()
    clicked=[];scene.commandActivated.connect(clicked.append);scene.activate_node(node);assert clicked==[1]
    view=NodeView(scene);view.resize(760,600);view.show();app.processEvents();view.fit_graph()
    assert view.transform().m11()>0.5,view.transform().m11()
    for mode in ('light','dark'):
        style.apply_theme(mode);scene.update();app.processEvents()
        view.grab().save(str(Path('artifacts/validation')/('flow-long-python-'+mode+'.png')))
    normal=NodeItem('long',3,'网页操作','网页操作',QColor('red'),subtitle_='参数: '+('a'*100000))
    assert normal.width<=360
    manual=NodeItem('manual',4,'运行Python','运行Python',QColor('red'),subtitle_='代码',width_=700)
    assert manual.width==700
    assert NodeScene._node_subtitle('运行Python',{'代码':''},1).endswith('未填写代码')
    view.close();scene.clear()
    print('PASS long Python/generic nodes bounded, fit readable, full code unchanged, edit activation and manual sizes preserved')


if __name__=='__main__':main()
