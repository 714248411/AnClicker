import os,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ['QT_QPA_PLATFORM']='windows'
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.instructions.registry import get_instruction_spec
from anclicker.domain.instructions import InstructionDraft
app=QApplication.instance() or QApplication([])
spec=get_instruction_spec('滚动元素到页面中心')
e=spec.create_editor();e.show();app.processEvents()
assert e._controls['behavior'].currentText()=='平滑滚动'
assert not e.ui.container_5.isVisible()
e._controls['by'].setCurrentText('锚点定位');app.processEvents();assert e.ui.container_5.isVisible()
e._controls['selector'].setText('#target');e._controls['anchor'].setText('#anchor')
e._controls['timeout'].setValue(12.5);e._controls['settle'].setValue(.7)
selected={'id':42,'session':'test','title':'测试窗口','url':'https://example.test'}
e.web_window.set_selection(selected)
draft=e.get_draft();other=spec.create_editor(draft=draft)
assert other.get_draft().parameters==draft.parameters
assert other._controls['timeout'].value()==12.5
other._controls['by'].setCurrentText('CSS选择器');other.show();app.processEvents();assert not other.ui.container_5.isVisible()
assert other.open_web_button.text()=='打开网页' and other.test_button.text()=='测试滚动'
from anclicker.platform.qt_compat.QtTest import QTest
other.resize(720,550);QTest.qWait(300);other.grab().save(str(ROOT/'artifacts/validation/scroll-element-ui.png'))
e.close();other.close()
print('PASS defaults, conditional anchors, window/draft persistence, decimal timings, open/test controls',flush=True)
os._exit(0)
