import ast
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock
root=Path(__file__).resolve().parents[1]
source=(root/'anclicker/app/Start_Win.py').read_text(encoding='utf8')
tree=ast.parse(source)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Main_window')
names={'register_global_shortcut_keys','unregister_global_shortcut_keys','global_shortcut_key'}
methods=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in names]
env={'normalize_hotkey':lambda keys:tuple(keys),'QKeySequence':lambda x:x,'global_hotkeys_supported':lambda x:True,'is_hotkey_valid':lambda *a:True,'QMessageBox':Mock()}
exec(compile(ast.Module(body=methods,type_ignores=[]),'<methods>','exec'),env)
keys={'开始运行':['f10'],'结束运行':['f10'],'结束运行2':[],'暂停和恢复':['f9']}
w=NS(db=Mock(),escape_stop=Mock(),hk_stop=Mock(),shortcut_requested=Mock(),pushButton_5=Mock(),pushButton_6=Mock(),pushButton_7=Mock(),command_thread=Mock(),task_scheduler=None,view_workspace=NS(agent_page=None),workspace=NS(),start=Mock(return_value=True),send_message=Mock(),_escape_registered=False,_runtime_error_box=None,isMinimized=lambda:False,show=Mock(),raise_=Mock(),activateWindow=Mock())
w.db.get_global_shortcut.return_value=keys
w.command_thread.isRunning.return_value=False
env['register_global_shortcut_keys'](w)
assert w.hk_stop.register.call_count==2
assert w._primary_stop_available
callback=w.hk_stop.register.call_args_list[0].kwargs['callback']
callback(None)
assert w.shortcut_requested.emit.call_args.args==('启停共享按键',)
env['global_shortcut_key'](w,'启停共享按键')
w.start.assert_called_once()
env['global_shortcut_key'](w,'终止线程')
w.command_thread.request_stop.assert_not_called()
w.command_thread.isRunning.return_value=True
env['global_shortcut_key'](w,'开始线程')
w.start.assert_called_once()
env['global_shortcut_key'](w,'启停共享按键')
w.command_thread.request_stop.assert_called_once()
w.command_thread.isRunning.return_value=False
env['global_shortcut_key'](w,'启停共享按键')
assert w.start.call_count==2
env['unregister_global_shortcut_keys'](w)
assert w.hk_stop.unregister.call_count==2
w.hk_stop.register.reset_mock()
keys['结束运行']=['f11']
env['register_global_shortcut_keys'](w)
assert w.hk_stop.register.call_count==3
for p in ('anclicker/app/Start_Win.py','anclicker/ui/dialogs/设置窗口.py'):
    compile((root/p).read_text(encoding='utf8'),p,'exec')
print('PASS shared registration, idle/start/run/stop/restart interlock, separate hotkeys, unique unregister, syntax')
