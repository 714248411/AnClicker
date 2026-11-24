"""Local library lifecycle and asynchronous dialog regression on temporary files."""
import tempfile
from pathlib import Path
from contextlib import nullcontext
from models.model_library import ModelLibrary
from anclicker.ui.local_model_dialog import LocalModelDialog
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.platform.qt_compat.QtCore import QEventLoop,QTimer
class Manager:
    def __init__(self,root):self.root=root;self.stops=0;self.available=True
    def _exclusive(self,blocking=False):return nullcontext(self.available)
    def stop(self):self.stops+=1
app=QApplication([])
with tempfile.TemporaryDirectory() as temp:
    base=Path(temp);root=base/'models';root.mkdir();manager=Manager(root);lib=ModelLibrary(manager)
    a=base/'中文模型.gguf';a.write_bytes(b'GGUF'+(3).to_bytes(4,'little')+b'fixture')
    lib.apply('add',str(a));assert a.exists() and len(lib.list())==1
    lib.apply('select',a.name);assert lib.active()==a.name and manager.stops==1
    for action,value in [('delete',a.name),('add',str(a)),('select','../'+a.name)]:
        try:lib.apply(action,value)
        except ValueError:pass
        else:raise AssertionError('Invalid operation accepted')
    invalid=base/'invalid.gguf';invalid.write_bytes(b'not a model')
    try:lib.apply('add',str(invalid))
    except ValueError:pass
    else:raise AssertionError('Invalid GGUF accepted')
    b=base/'second.gguf';b.write_bytes(a.read_bytes());lib.apply('add',str(b));lib.apply('select',b.name)
    manager.available=False
    try:lib.apply('delete',a.name)
    except RuntimeError:pass
    else:raise AssertionError('Busy request bypassed')
    manager.available=True;lib.apply('delete',a.name)
    assert a.exists() and not (root/a.name).exists() and len(list((root/'.trash').glob('*.gguf')))==1
    dialog=LocalModelDialog(None,lib);assert dialog.items.count()==1 and not dialog.delete.isEnabled()
    c=base/'third.gguf';c.write_bytes(a.read_bytes());dialog.run_action('add',str(c))
    loop=QEventLoop();timer=QTimer();timer.timeout.connect(lambda:loop.quit() if dialog.worker is None else None);timer.start(10);QTimer.singleShot(5000,loop.quit);loop.exec();timer.stop()
    assert dialog.worker is None and dialog.items.count()==2 and (root/c.name).exists()
    dialog.close()
print('PASS library add/select/delete, source preservation, invalid paths, busy guard, current protection and asynchronous dialog')
