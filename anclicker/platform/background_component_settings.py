from anclicker.app.paths import get_install_folder
"""Local component configuration; registration code is protected with Windows DPAPI."""
import base64
import json
import os
from pathlib import Path
import sys

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'win32crypt': ('import', 'win32crypt', (), False),
    'QThread_Signal_Slot_QTimer': ('from', 'anclicker.platform.qt_compat.QtCore', ('QThread', 'Signal', 'Slot', 'QTimer'), 0),
    'QDialog_QVBoxLayout_QLabel_QPushButton': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QDialog', 'QVBoxLayout', 'QLabel', 'QPushButton'), 0),
    'ensure_component': ('from', 'anclicker.platform.background_component_auto', ('ensure_component',), 0),
    'QtWidgets_QDialog_etc': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QDialog', 'QVBoxLayout', 'QFormLayout', 'QHBoxLayout', 'QLineEdit', 'QComboBox', 'QPushButton', 'QLabel', 'QDialogButtonBox', 'QFileDialog', 'QMessageBox', 'QCheckBox', 'QWidget'), 0),
    'ConfigurationCancelled': ('from', 'anclicker.platform.background_component_auto', ('ConfigurationCancelled',), 0),
    'apply_settings_theme': ('from', 'anclicker.ui.settings_theme', ('apply_settings_theme',), 0),
})



def config_path():
    base = (Path(sys.executable).parent if getattr(sys, 'frozen', False)
            else Path(get_install_folder()) / 'current')
    return Path(os.environ.get('ANCLICKER_DM_CONFIG', base / 'damo' / 'config.json'))


def read_config(path=None):
    path = Path(path) if path else config_path()
    if not path.is_file():
        return {}
    result = json.loads(path.read_text(encoding='utf-8-sig'))
    if result.get('reg_code_dpapi'):
        win32crypt = _module_imports.load('win32crypt')
        result['reg_code'] = win32crypt.CryptUnprotectData(base64.b64decode(result['reg_code_dpapi']),None,None,None,0)[1].decode('utf-8')
    return result


def write_config(values, path=None):
    path = Path(path) if path else config_path()
    result = dict(values)
    code = result.pop('reg_code', '').strip()
    result.pop('reg_code_dpapi', None)
    if code:
        win32crypt = _module_imports.load('win32crypt')
        result['reg_code_dpapi'] = base64.b64encode(win32crypt.CryptProtectData(code.encode('utf8'),'AnClicker DM',None,None,None,0)).decode('ascii')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    os.replace(temporary,path)


def configure_automatically(parent=None):
    """A cancellable modal progress window; downloading never blocks the Qt thread."""
    QThread, Signal, Slot, QTimer = _module_imports.load('QThread_Signal_Slot_QTimer')
    QDialog, QVBoxLayout, QLabel, QPushButton = _module_imports.load('QDialog_QVBoxLayout_QLabel_QPushButton')
    ensure_component = _module_imports.load('ensure_component')

    class Worker(QThread):
        progress = Signal(str)

        def __init__(self, parent):
            super().__init__(parent)
            self.result, self.error = None, None
            self.cancelled = False

        def run(self):
            try:
                self.result = ensure_component(emit=self.progress.emit,
                    cancelled=lambda: self.cancelled or self.isInterruptionRequested())
            except Exception as error:
                self.error = error

    class Progress(QDialog):
        def __init__(self, owner):
            super().__init__(owner)
            self.setWindowTitle('自动配置后台组件')
            self.setMinimumWidth(400)
            layout = QVBoxLayout(self)
            self.message = QLabel('正在检查本地后台组件…', self)
            self.message.setWordWrap(True)
            layout.addWidget(self.message)
            self.cancel = QPushButton('取消', self)
            layout.addWidget(self.cancel)
            self.cancel.clicked.connect(self.reject)
            self.worker = Worker(self)
            self.worker.progress.connect(self.message.setText)
            self.worker.finished.connect(self.finished_safely)
            self.ready_to_close = False
            QTimer.singleShot(0, self.worker.start)

        def done(self, result):
            if not self.ready_to_close:
                self.worker.cancelled = True
                self.worker.requestInterruption()
                self.message.setText('正在取消，请稍候…')
                self.cancel.setEnabled(False)
                return
            super().done(result)

        def reject(self):
            self.done(QDialog.Rejected)

        def closeEvent(self, event):
            if not self.ready_to_close:
                self.reject()
                event.ignore()
            else:
                super().closeEvent(event)

        @Slot()
        def finished_safely(self):
            self.worker.wait()
            self.ready_to_close = True
            self.done(QDialog.Rejected if self.worker.error else QDialog.Accepted)

    dialog = Progress(parent)
    try:
        dialog.exec()
        if dialog.worker.error:
            raise dialog.worker.error
        return dialog.worker.result
    finally:
        dialog.deleteLater()


def ComponentSettings(parent):
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QLabel, QDialogButtonBox, QFileDialog, QMessageBox, QCheckBox, QWidget = _module_imports.load('QtWidgets_QDialog_etc')
    ConfigurationCancelled = _module_imports.load('ConfigurationCancelled')
    dialog = QDialog(parent)
    dialog.setWindowTitle('大漠组件设置')
    dialog.setMinimumWidth(540)
    layout = QVBoxLayout(dialog)
    try:
        config = read_config()
    except Exception:
        config = {}
    automatic = QCheckBox('自动配置后台组件（推荐）', dialog)
    automatic.setObjectName('automaticBackgroundComponent')
    automatic.setChecked(config.get('mode') == 'auto' or not (
        config.get('backend') or config.get('dll_path') or (config_path().parent/'dm.dll').is_file()))
    layout.addWidget(automatic)
    hint = QLabel(dialog)
    hint.setWordWrap(True)
    layout.addWidget(hint)
    setup = QPushButton('立即配置 / 重新检查', dialog)
    setup.setObjectName('setupBackgroundComponent')
    setup.setAutoDefault(False)
    layout.addWidget(setup)
    manual = QWidget(dialog)
    form = QFormLayout(manual)
    form.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(manual)
    backend = QComboBox(dialog)
    backend.addItems(['7.2424 独立组件', '大漠 COM 组件'])
    backend.setCurrentIndex(0 if config.get('backend', 'native-7.2424') == 'native-7.2424' else 1)
    form.addRow('组件类型', backend)
    fields = {}
    for key, caption in [('dll_path', '组件 DLL'), ('helper_path', '配套辅助 DLL'),
                         ('reg_code', '注册码'), ('reg_extra', '版本附加信息')]:
        control = QLineEdit(str(config.get(key, '')), dialog)
        fields[key] = control
        if key == 'reg_code':
            control.setEchoMode(QLineEdit.Password)
        if key.endswith('_path'):
            row = QHBoxLayout()
            row.addWidget(control)
            button = QPushButton('选择…', dialog)
            button.setAutoDefault(False)
            row.addWidget(button)

            def browse(checked=False, target=control):
                path, _ = QFileDialog.getOpenFileName(dialog, '选择组件', str(config_path().parent), 'DLL (*.dll)')
                if path:
                    target.setText(path)

            button.clicked.connect(browse)
            form.addRow(caption, row)
        else:
            form.addRow(caption, control)

    def mode_changed():
        native = backend.currentIndex() == 0
        fields['helper_path'].setEnabled(native)
        fields['reg_code'].setEnabled(not native)
        fields['reg_extra'].setEnabled(not native)
        manual.setVisible(not automatic.isChecked())
        setup.setVisible(automatic.isChecked())
        hint.setText('首次绑定时自动识别本地组件；缺失时下载并校验，升级后继续使用，无需填写路径。'
                     if automatic.isChecked() else
                     '手动配置于下一次绑定时生效。COM 版本需有效授权；注册码加密保存在本机。')

    def install():
        try:
            result = configure_automatically(dialog)
        except ConfigurationCancelled:
            hint.setText('已取消；下次绑定时可以继续自动配置。')
        except Exception as error:
            hint.setText(str(error))
        else:
            hint.setText('后台组件已就绪，将在下次绑定时自动使用。')
            setup.setToolTip(result['dll_path'])

    setup.clicked.connect(install)
    backend.currentIndexChanged.connect(mode_changed)
    automatic.toggled.connect(mode_changed)
    mode_changed()
    buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, dialog)
    buttons.button(QDialogButtonBox.Save).setText('保存')
    buttons.button(QDialogButtonBox.Cancel).setText('取消')
    layout.addWidget(buttons)
    buttons.rejected.connect(dialog.reject)

    def save():
        values = dict(config)
        if automatic.isChecked():
            # Keep existing manual values, including authorization, when switching modes.
            values['mode'] = 'auto'
        else:
            values.update({key: field.text().strip() for key, field in fields.items()})
            values['mode'] = 'manual'
            values['backend'] = 'native-7.2424' if backend.currentIndex() == 0 else 'com'
            for key in (('dll_path', 'helper_path') if backend.currentIndex() == 0 else ('dll_path',)):
                path = Path(values[key])
                path = path if path.is_absolute() else config_path().parent/path
                if not values[key] or not path.is_file():
                    QMessageBox.warning(dialog, '组件路径无效', '请选择存在的 DLL 文件')
                    return
        try:
            write_config(values)
        except Exception:
            QMessageBox.warning(dialog, '保存失败', '无法保存本机组件配置')
            return
        dialog.accept()

    buttons.accepted.connect(save)
    apply_settings_theme = _module_imports.load('apply_settings_theme')
    owner = getattr(getattr(parent, 'context', None), 'metadata', {}).get('main_window')
    if owner:
        apply_settings_theme(dialog, owner)
    return dialog
