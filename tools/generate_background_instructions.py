"""Generate standalone forms for the dm 7.2149 instruction catalog."""
from pathlib import Path
from xml.sax.saxutils import escape
import subprocess, sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from background_catalog import GROUPS, group_methods, label
from instructions.common import FieldSpec
from background_binding import AUTO, PRESETS
source=(root/'instructions/Excel/写入单元格/写入单元格.ui').read_text(encoding='utf8')
common=source[source.index('<item><spacer name="verticalSpacer"'):]
fields={group:[FieldSpec('接口','操作','choice',label(next(iter(group_methods(group)))),tuple(label(n) for n in group_methods(group))),FieldSpec('参数','接口参数','multiline','{}'),FieldSpec('变量','结果变量（可选）')] for group in GROUPS if group != '后台答题器'}
fields['绑定选择窗口']=[FieldSpec('窗口句柄','目标窗口句柄'),FieldSpec('窗口标题','窗口标题'),FieldSpec('窗口类名','窗口类名'),FieldSpec('进程路径','进程路径'),FieldSpec('进程ID','进程 ID','int',0,maximum=2147483647),FieldSpec('图像模式','后台图像模式','choice','dx1',('dx1','dx2','dx3','gdi','gdi2','dx')),FieldSpec('鼠标模式','后台鼠标模式','choice','dx',('dx','dx2','windows','windows2','windows3')),FieldSpec('键盘模式','后台键盘模式','choice','dx',('dx','windows')),FieldSpec('绑定模式','绑定方式','choice','0',('0','2')),FieldSpec('绑定等待','绑定后等待（秒）','float',1,minimum=0,maximum=10),FieldSpec('绑定方案','绑定方案','choice',AUTO,PRESETS)]
fields['解除后台绑定']=[]
for name, items in fields.items():
    folder=root/'instructions'/'后台功能'/name
    folder.mkdir(parents=True,exist_ok=True);(folder/'__init__.py').touch()
    rows=[]
    for i,f in enumerate(items):
        value=escape(str(f.default)); prop='text'
        if f.kind=='choice':
            widget=f'<widget class="QComboBox" name="parameter_{i}">'+''.join('<item><property name="text"><string>'+escape(x)+'</string></property></item>' for x in f.choices)+'</widget>'
        elif f.kind in ('int','float'):
            w,t=('QSpinBox','number') if f.kind=='int' else ('QDoubleSpinBox','double')
            widget=f'<widget class="{w}" name="parameter_{i}"><property name="minimum"><{t}>{f.minimum}</{t}></property><property name="maximum"><{t}>{f.maximum}</{t}></property><property name="value"><{t}>{f.default}</{t}></property></widget>'
        elif f.key=='变量':
            widget=f'<widget class="QComboBox" name="parameter_{i}"><property name="editable"><bool>true</bool></property></widget>'
        else:
            w,prop=('QPlainTextEdit','plainText') if f.kind=='multiline' else ('QLineEdit','text')
            widget=f'<widget class="{w}" name="parameter_{i}"><property name="{prop}"><string>{value}</string></property></widget>'
        if f.key in ('变量','窗口句柄'):
            button='设置变量' if f.key=='变量' else '选择窗口…'
            widget=f'<layout class="QHBoxLayout" name="fieldLayout_{i}"><item>{widget}</item><item><widget class="QPushButton" name="auxiliary_{i}"><property name="text"><string>{button}</string></property></widget></item></layout>'
        rows.append(f'<item row="{i}" column="0"><widget class="QLabel" name="label_{i}"><property name="text"><string>{escape(f.label)}</string></property></widget></item><item row="{i}" column="1">{widget}</item>')
    xml='<?xml version="1.0" encoding="UTF-8"?><ui version="4.0"><class>InstructionEditor</class><widget class="QDialog" name="InstructionEditor"><layout class="QVBoxLayout" name="rootLayout"><item><widget class="QLabel" name="titleLabel"><property name="text"><string>'+name+'</string></property></widget></item><item><widget class="QGroupBox" name="parameterGroupBox"><property name="title"><string>后台参数</string></property><layout class="QFormLayout" name="parameterFormLayout">'+''.join(rows)+'</layout></widget></item>'+common
    ui=folder/(name+'.ui');ui.write_text(xml,encoding='utf8')
    generated=folder/(name+'_ui.py')
    subprocess.run([str(Path(sys.executable).parent/'pyside2-uic.exe'),str(ui),'-o',str(generated)],check=True)
    generated.write_text(generated.read_text(encoding='utf8').replace('from PySide2.','from qt_compat.'),encoding='utf8')
    base='BindingEditor' if name=='绑定选择窗口' else 'UnbindingEditor' if name=='解除后台绑定' else 'BackgroundMethodEditor'
    text='from instructions.common import FieldSpec, SchemaInstructionEditor\nfrom instructions.common.background_instruction import BackgroundMethodEditor, BackgroundExecutor, BindingEditor, UnbindingEditor\nfrom importlib import import_module\nUi_InstructionEditor = import_module('+repr('.'+name+'_ui')+', __package__).Ui_InstructionEditor\n\nclass InstructionEditor('+base+'):\n    TYPE_ID = DISPLAY_NAME = '+repr(name)+'\n    UI_CLASS = Ui_InstructionEditor\n    FIELDS = (\n'+''.join('        '+repr(f)+',\n' for f in items)+'    )\n\nclass InstructionExecutor(BackgroundExecutor):\n    TYPE_ID = '+repr(name)+'\n'
    (folder/(name+'.py')).write_text(text,encoding='utf8')
(root/'instructions'/'后台功能'/'__init__.py').touch()
print('Generated',len(fields),'background editors')
