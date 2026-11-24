import sys,tempfile,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import Mock,patch
from types import SimpleNamespace
from anclicker.platform import background_binding as binding, background_preferences as prefs, background_preload as preload, background_runtime as runtime, background_component_auto as auto
from anclicker.domain.instructions import ExecutionContext,InstructionDraft
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.instructions.registry import get_instruction_spec
app=QApplication([])
with tempfile.TemporaryDirectory() as folder, patch.object(prefs,'preference_path',return_value=Path(folder)/'preference.json'), patch.object(preload,'start_preload'):
 assert prefs.preferred_preset()==binding.AUTO
 for old,label in binding.LABELS.items():
  assert binding.binding_attempts({'绑定方案':label,'启用截图':True})[0][0][1:4]==binding.PROFILES[old]
 prefs.remember_success('DX2');assert prefs.preferred_preset()=='DX2'
 assert binding.binding_attempts({})[0][0][0]=='DX2'
 for kind in ('窗口键鼠','窗口鼠标','窗口键盘','窗口多坐标点击','窗口OCR点击','窗口按下键盘','窗口文本输入','绑定选择窗口'):
  editor=get_instruction_spec(kind).create_editor()
  combo=editor._controls['绑定方案'] if kind=='绑定选择窗口' else editor.background_preset
  assert combo.currentText()==binding.display_preset('DX2'),(kind,combo.currentText())
  for old,label in binding.LABELS.items():assert combo.findText(label)>=0
  # Existing saved selection wins over remembered success.
  params={'绑定方案':'DX1','窗口':{'窗口句柄':'12'},'模式':'后台'} if kind!='绑定选择窗口' else {'绑定方案':'DX1','窗口句柄':'12'}
  editor.load_draft(InstructionDraft(kind,params))
  assert combo.currentText()==binding.display_preset('DX1')
  if kind in ('窗口键鼠','绑定选择窗口'):
   from anclicker.platform.qt_compat.QtCore import QEventLoop,QTimer
   editor.show();app.processEvents();loop=QEventLoop();QTimer.singleShot(150,loop.quit);loop.exec_()
   editor.grab().save('artifacts/validation/dm-preset-'+('window' if kind=='窗口键鼠' else 'binding')+'.png')
  editor.close()
 target={'窗口句柄':'12','窗口标题':'test'}
 windows=Mock();windows.resolve.return_value=target
 transports=[]
 def factory(context):
  transport=Mock();transport.context=context
  def call(method,*args,**kwargs):
   if method=='BindWindow':return int(args[2]=='dx2')
   return 1
  transport.call.side_effect=call;transports.append(transport);return transport
 ctx=ExecutionContext(services={'background_windows':lambda:windows,'background_transport':factory})
 # Explicit success remembers the same choice used by window keyboard/mouse.
 runtime.bind_background(ctx,dict(target,绑定方案='后台2（DX2）',启用截图=False));assert prefs.preferred_preset()=='DX2'
 with patch.object(preload,'offer_preloaded') as offer:
  runtime.close_background(ctx,keep_transport=True);offer.assert_called_once_with(transports[-1]);transports[-1].close.assert_not_called()
 try:runtime.bind_background(ctx,dict(target,绑定方案='后台1（DX1）',启用截图=False))
 except RuntimeError:pass
 else:raise AssertionError('failure swallowed')
 assert prefs.preferred_preset()=='DX2'
 # Shared pool hands a clean helper to only one next execution.
 preload.close_preload();transport=Mock();transport.process=None
 preload.offer_preloaded(transport);assert preload.take_preloaded(ctx) is transport
 assert preload.take_preloaded(ctx) is None
 transport=Mock();transport.process=None;preload.offer_preloaded(transport);preload.close_preload()
 # Fresh install copies only the shipped verified DLLs, no network.
 destination=Path(folder)/'installed'
 with patch.object(auto,'managed_directory',return_value=destination):
  config=auto.ensure_component()
  assert Path(config['dll_path']).is_file() and Path(config['helper_path']).is_file()
  assert (destination/'installed.json').is_file()
  assert auto.ensure_component()==config
 with patch.object(auto,'managed_directory',return_value=Path(folder)/'missing'),patch.object(auto,'_valid',return_value=False):
  try:auto.ensure_component()
  except RuntimeError as e:assert '不会联网下载' in str(e)
  else:raise AssertionError('missing bundle accepted')
print('PASS four shared presets, remembered success/defaults, explicit saved precedence, failed binding not remembered, clean process recycling, fresh offline install and corrupt/missing bundle failure')
