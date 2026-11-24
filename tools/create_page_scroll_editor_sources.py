import json,sys,subprocess,xml.etree.ElementTree as E
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
name='滚动网页到指定位置'
c=next(x for x in json.loads((ROOT/'integrations/yingdao/commands.json').read_text('utf8')) if x['id']=='scrollPageToPosition')
fields=[]
for p in c['params']:
 kind={'select':'choice','number':'float'}.get(p['type'],'text')
 fields.append(f"FieldSpec({p['key']!r}, {p['label']!r}, {kind!r}, {p['default']!r}, choices={tuple(p.get('options',[]))!r}, required={p['key']=='selector'}, minimum=0, maximum={30 if p['key']=='settle' else 60})")
(ROOT/f'anclicker/instructions/网页自动化/{name}/schema.py').write_text('from anclicker.domain.fields import FieldSpec\nTYPE_ID = '+repr(name)+'\nFIELDS = ('+',\n'.join(fields)+',)\n',encoding='utf8')
tree=E.parse(ROOT/'resources/ui/instructions/网页自动化/点击元素/点击元素.ui')
form=tree.find('.//layout[@name="parameterFormLayout"]');form.clear();form.set('class','QFormLayout');form.set('name','parameterFormLayout')
def prop(w,n,t,v): E.SubElement(E.SubElement(w,'property',name=n),t).text=str(v)
for i,p in enumerate(c['params']):
 label=E.SubElement(E.SubElement(form,'item',row=str(i),column='0'),'widget',{'class':'QLabel','name':f'label_{i}'});prop(label,'text','string',p['label'])
 cell=E.SubElement(form,'item',row=str(i),column='1')
 if p['type']=='text':
  container=E.SubElement(cell,'widget',{'class':'QWidget','name':f'container_{i}'})
  layout=E.SubElement(container,'layout',{'class':'QHBoxLayout','name':f'fieldLayout_{i}'})
  w=E.SubElement(E.SubElement(layout,'item'),'widget',{'class':'QLineEdit','name':f'parameter_{i}'})
  button=E.SubElement(E.SubElement(layout,'item'),'widget',{'class':'QPushButton','name':f'auxiliary_{i}'});prop(button,'text','string','拾取元素' if p['key']=='selector' else '拾取锚点')
 elif p['type']=='select':
  w=E.SubElement(cell,'widget',{'class':'QComboBox','name':f'parameter_{i}'})
  for text in p['options']:prop(E.SubElement(w,'item'),'text','string',text)
  prop(w,'currentIndex','number',p['options'].index(p['default']))
 else:
  w=E.SubElement(cell,'widget',{'class':'QDoubleSpinBox','name':f'parameter_{i}'})
  prop(w,'minimum','double',0);prop(w,'maximum','double',30 if p['key']=='settle' else 60);prop(w,'value','double',p['default']);prop(w,'singleStep','double',.1)
tree.find('.//widget[@name="titleLabel"]/property/string').text=name
ui=ROOT/f'resources/ui/instructions/网页自动化/{name}/{name}.ui';ui.parent.mkdir(parents=True,exist_ok=True);tree.write(ui,encoding='utf-8',xml_declaration=True)
binding=ROOT/f'anclicker/ui/generated/instructions/网页自动化/{name}/{name}_ui.py';binding.parent.mkdir(parents=True,exist_ok=True)
subprocess.run([str(ROOT/'.venv-build/Lib/site-packages/PySide2/uic.exe'),'-g','python',str(ui),'-o',str(binding)],check=True)
binding.write_text(binding.read_text('utf8').replace('from PySide2.','from anclicker.platform.qt_compat.'),encoding='utf8')
from tools.generate_instruction_adapters import editor_source
from anclicker.instructions.registry import get_instruction_spec
spec=get_instruction_spec(name)
p=ROOT/(spec.editor_module_path.replace('.','/')+'.py');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(editor_source(spec,c),encoding='utf8')
print('PASS scroll editor sources and Qt binding generated')
