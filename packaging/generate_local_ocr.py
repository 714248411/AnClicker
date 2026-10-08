"""Mechanically generate independent OCR UI/modules from their shared schemas."""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from instructions.common.local_ocr_instruction import OCR_TYPES, fields_for


def prop(element, name, tag, value):
    child = ET.SubElement(element, 'property', name=name)
    ET.SubElement(child, tag).text = str(value)


def generate():
    template = ROOT / 'instructions/获取变量/OCR识别/OCR识别.ui'
    uic = Path(sys.executable).parent / ('pyside6-uic.exe' if sys.platform == 'win32' else 'pyside6-uic')
    for name in OCR_TYPES:
        folder = ROOT / 'instructions/本地OCR' / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder.parent / '__init__.py').touch(exist_ok=True)
        (folder / '__init__.py').touch(exist_ok=True)
        tree = ET.parse(template)
        root = tree.getroot()
        root.find("widget/property[@name='windowTitle']/string").text = name
        root.find(".//widget[@name='titleLabel']/property[@name='text']/string").text = name
        root.find(".//widget[@name='parameterGroupBox']/property[@name='title']/string").text = name + '参数（离线）'
        form = root.find(".//layout[@name='parameterFormLayout']")
        form.clear()
        form.set('class', 'QFormLayout')
        form.set('name', 'parameterFormLayout')
        for i, field in enumerate(fields_for(name)):
            label_item = ET.SubElement(form, 'item', row=str(i), column='0')
            label = ET.SubElement(label_item, 'widget', {'class': 'QLabel', 'name': f'parameterLabel_{i}'})
            prop(label, 'text', 'string', field.label + (' *' if field.required else ''))
            item = ET.SubElement(form, 'item', row=str(i), column='1')
            container = ET.SubElement(item, 'widget', {'class': 'QWidget', 'name': f'parameterContainer_{i}'})
            layout = ET.SubElement(container, 'layout', {'class': 'QHBoxLayout', 'name': f'parameterLayout_{i}'})
            for edge in ('leftMargin', 'topMargin', 'rightMargin', 'bottomMargin'):
                prop(layout, edge, 'number', 0)
            control_item = ET.SubElement(layout, 'item')
            cls = {'choice': 'QComboBox', 'int': 'QSpinBox', 'float': 'QDoubleSpinBox',
                   'bool': 'QCheckBox'}.get(field.kind, 'QComboBox' if field.key == '变量' else 'QLineEdit')
            widget = ET.SubElement(control_item, 'widget', {'class': cls, 'name': f'parameter_{i}'})
            if cls == 'QComboBox':
                if field.key == '变量':
                    prop(widget, 'editable', 'bool', 'true')
                choices = field.choices or (str(field.default),)
                for choice in choices:
                    prop(ET.SubElement(widget, 'item'), 'text', 'string', choice)
                prop(widget, 'currentIndex', 'number', choices.index(field.default))
            elif cls in ('QSpinBox', 'QDoubleSpinBox'):
                tag = 'double' if field.kind == 'float' else 'number'
                for key, value in [('minimum', field.minimum), ('maximum', field.maximum), ('value', field.default)]:
                    prop(widget, key, tag, value)
                if field.kind == 'float':
                    prop(widget, 'decimals', 'number', 2)
            elif cls == 'QCheckBox':
                prop(widget, 'checked', 'bool', str(field.default).lower())
                prop(widget, 'text', 'string', '启用')
            else:
                prop(widget, 'text', 'string', field.default)
            auxiliary = {'区域': '框选区域', '变量': '设置变量', '图像路径': '选择图片',
                         '点击位置': '获取坐标'}
            if field.key in auxiliary:
                button = ET.SubElement(ET.SubElement(layout, 'item'), 'widget',
                                       {'class': 'QPushButton', 'name': f'auxiliary_{i}'})
                prop(button, 'text', 'string', auxiliary[field.key])
        path = folder / f'{name}.ui'
        ET.indent(tree)
        tree.write(path, encoding='utf-8', xml_declaration=True)
        subprocess.run([str(uic), str(path), '-o', str(folder/f'{name}_ui.py')], check=True)
        source = f'''"""{name}：独立拖拽指令，共享离线 OCR 引擎。"""
from instructions.common.local_ocr_instruction import LocalOcrEditor, LocalOcrExecutor, fields_for
from .{name}_ui import Ui_InstructionEditor


class InstructionEditor(LocalOcrEditor):
    TYPE_ID = {name!r}
    DISPLAY_NAME = TYPE_ID
    UI_CLASS = Ui_InstructionEditor
    FIELDS = fields_for(TYPE_ID)


class InstructionExecutor(LocalOcrExecutor):
    TYPE_ID = {name!r}
'''
        (folder / f'{name}.py').write_text(source, encoding='utf-8')


if __name__ == '__main__':
    generate()
