"""Local component configuration; registration code is protected with Windows DPAPI."""
import base64
import json
import os
from pathlib import Path
import sys


def config_path():
    base = (Path(sys.executable).parent if getattr(sys, 'frozen', False)
            else Path(__file__).parent / 'current')
    return Path(os.environ.get('ANCLICKER_DM_CONFIG', base / 'damo' / 'config.json'))


def read_config(path=None):
    path = Path(path) if path else config_path()
    if not path.is_file():
        return {}
    result = json.loads(path.read_text(encoding='utf-8-sig'))
    if result.get('reg_code_dpapi'):
        import win32crypt
        result['reg_code'] = win32crypt.CryptUnprotectData(base64.b64decode(result['reg_code_dpapi']),None,None,None,0)[1].decode('utf-8')
    return result


def write_config(values, path=None):
    path = Path(path) if path else config_path()
    result = dict(values)
    code = result.pop('reg_code', '').strip()
    result.pop('reg_code_dpapi', None)
    if code:
        import win32crypt
        result['reg_code_dpapi'] = base64.b64encode(win32crypt.CryptProtectData(code.encode('utf8'),'AnClicker DM',None,None,None,0)).decode('ascii')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    os.replace(temporary,path)


def ComponentSettings(parent):
    from qt_compat.QtWidgets import (QDialog,QVBoxLayout,QFormLayout,QHBoxLayout,QLineEdit,
        QComboBox,QPushButton,QLabel,QDialogButtonBox,QFileDialog,QMessageBox)
    dialog = QDialog(parent)
    dialog.setWindowTitle('大漠组件设置');dialog.setMinimumWidth(540)
    layout = QVBoxLayout(dialog);form = QFormLayout();layout.addLayout(form)
    try:
        config = read_config()
    except Exception:
        config = {}
    backend = QComboBox(dialog);backend.addItems(['7.2424 独立组件','大漠 COM 组件'])
    backend.setCurrentIndex(0 if config.get('backend') == 'native-7.2424' else 1)
    form.addRow('组件类型',backend)
    fields = {}
    for key,caption in [('dll_path','组件 DLL'),('helper_path','配套辅助 DLL'),('reg_code','注册码'),('reg_extra','版本附加信息')]:
        control = QLineEdit(str(config.get(key,'')),dialog);fields[key]=control
        if key == 'reg_code':
            control.setEchoMode(QLineEdit.Password)
        if key.endswith('_path'):
            row=QHBoxLayout();row.addWidget(control);button=QPushButton('选择…',dialog);row.addWidget(button)
            def browse(checked=False, target=control):
                path,_=QFileDialog.getOpenFileName(dialog,'选择组件',str(config_path().parent),'DLL (*.dll)')
                if path:target.setText(path)
            button.clicked.connect(browse);form.addRow(caption,row)
        else:
            form.addRow(caption,control)
    hint=QLabel('组件在独立进程中运行。配置变更于下一次绑定时生效。\nCOM 版本需填写有效授权；注册码加密保存在本机，不写入项目文件。',dialog)
    hint.setWordWrap(True);layout.addWidget(hint)
    def mode_changed():
        native=backend.currentIndex()==0
        fields['helper_path'].setEnabled(native)
        fields['reg_code'].setEnabled(not native)
        fields['reg_extra'].setEnabled(not native)
    backend.currentIndexChanged.connect(mode_changed);mode_changed()
    buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel,dialog)
    buttons.button(QDialogButtonBox.Save).setText('保存');buttons.button(QDialogButtonBox.Cancel).setText('取消')
    layout.addWidget(buttons);buttons.rejected.connect(dialog.reject)
    def save():
        values={key:field.text().strip() for key,field in fields.items()}
        values['backend']='native-7.2424' if backend.currentIndex()==0 else 'com'
        for key in (('dll_path','helper_path') if backend.currentIndex()==0 else ('dll_path',)):
            path=Path(values[key]);path=path if path.is_absolute() else config_path().parent/path
            if not values[key] or not path.is_file():
                QMessageBox.warning(dialog,'组件路径无效','请选择存在的 DLL 文件');return
        try:
            write_config(values)
        except Exception:
            QMessageBox.warning(dialog,'保存失败','无法保存本机组件配置');return
        dialog.accept()
    buttons.accepted.connect(save)
    from settings_theme import apply_settings_theme
    owner = getattr(getattr(parent,'context',None),'metadata',{}).get('main_window')
    if owner:apply_settings_theme(dialog,owner)
    return dialog
