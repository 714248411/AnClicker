"""Regenerate independent editors from the versioned reference command catalog."""
import json
from pathlib import Path
import subprocess
import sys
from xml.sax.saxutils import escape
root=Path(__file__).resolve().parents[1]
catalog=json.loads((root/'integrations/yingdao/commands.json').read_text(encoding='utf-8'))
template=(root/'instructions/Excel/写入单元格/写入单元格.ui').read_text(encoding='utf-8')
common=template[template.index('<item><spacer name="verticalSpacer"'):]
for c in catalog:
    folder=root/'instructions'/c['category']/c['type_id']
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'__init__.py').touch()
    fields=[]; rows=[]
    for i,p in enumerate(c['params']):
        key=p['key']; default=p.get('default',''); options=p.get('options',[])
        kind='choice' if p['type'] in ('select','order') else ('int' if key in ('row','col','count','times','startIndex') else 'float') if p['type']=='number' else 'text'
        label=escape(p['label']); value=escape(str(default))
        minimum=1 if key in ('row','col','count','times','startIndex') else 0
        fields.append(f'        FieldSpec({key!r}, {p["label"]!r}, {kind!r}, {default!r}, choices={tuple(options) if kind=="choice" else ()!r}, minimum={minimum}),')
        if kind=='choice':
            inner=''.join('<item><property name="text"><string>'+escape(str(o))+'</string></property></item>' for o in options)
            widget=f'<widget class="QComboBox" name="parameter_{i}">{inner}<property name="currentIndex"><number>{options.index(default) if default in options else 0}</number></property></widget>'
        elif kind=='int':
            widget=f'<widget class="QSpinBox" name="parameter_{i}"><property name="minimum"><number>{minimum}</number></property><property name="maximum"><number>1000000</number></property><property name="value"><number>{default}</number></property></widget>'
        elif kind=='float':
            widget=f'<widget class="QDoubleSpinBox" name="parameter_{i}"><property name="minimum"><double>{minimum}</double></property><property name="maximum"><double>1000000</double></property><property name="value"><double>{default}</double></property></widget>'
        else:
            widget=f'<widget class="QLineEdit" name="parameter_{i}"><property name="text"><string>{value}</string></property></widget>'
        if key in ('path','fromPath','toPath','folder','dst','fromBook','toBook','varName','data','selector','anchor'):
            button='设置变量' if key in ('varName','data') else '拾取元素' if key in ('selector','anchor') else '浏览…'
            widget=f'<widget class="QWidget" name="container_{i}"><layout class="QHBoxLayout" name="fieldLayout_{i}"><item>{widget}</item><item><widget class="QPushButton" name="auxiliary_{i}"><property name="text"><string>{button}</string></property></widget></item></layout></widget>'
        rows.append(f'<item row="{i}" column="0"><widget class="QLabel" name="label_{i}"><property name="text"><string>{label}</string></property></widget></item><item row="{i}" column="1">{widget}</item>')
    xml='<?xml version="1.0" encoding="UTF-8"?><ui version="4.0"><class>InstructionEditor</class><widget class="QDialog" name="InstructionEditor"><property name="geometry"><rect><x>0</x><y>0</y><width>720</width><height>680</height></rect></property><layout class="QVBoxLayout" name="rootLayout"><item><widget class="QLabel" name="titleLabel"><property name="text"><string>'+escape(c['name'])+'</string></property></widget></item><item><widget class="QGroupBox" name="parameterGroupBox"><property name="title"><string>指令参数</string></property><layout class="QFormLayout" name="parameterFormLayout">'+''.join(rows)+'</layout></widget></item>'+common
    ui=folder/(c['type_id']+'.ui');ui.write_text(xml,encoding='utf-8')
    generated=folder/(c['type_id']+'_ui.py')
    subprocess.run([str(Path(sys.executable).parent/'pyside2-uic.exe'),str(ui),'-o',str(generated)],check=True)
    generated.write_text(generated.read_text(encoding='utf-8').replace('from PySide2.', 'from qt_compat.'),encoding='utf-8')
    source='from instructions.common import FieldSpec\nfrom instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor\nfrom importlib import import_module\nUi_InstructionEditor = import_module('+repr('.'+c['type_id']+'_ui')+', __package__).Ui_InstructionEditor\n\nclass InstructionEditor(RpaInstructionEditor):\n    TYPE_ID = '+repr(c['type_id'])+'\n    DISPLAY_NAME = '+repr(c['name'])+'\n    COMMAND_ID = '+repr(c['id'])+'\n    UI_CLASS = Ui_InstructionEditor\n    FIELDS = (\n'+'\n'.join(fields)+'\n    )\n\nclass InstructionExecutor(RpaInstructionExecutor):\n    TYPE_ID = '+repr(c['type_id'])+'\n    COMMAND_ID = '+repr(c['id'])+'\n'
    (folder/(c['type_id']+'.py')).write_text(source,encoding='utf-8')
print('Generated',len(catalog),'instruction editors')
