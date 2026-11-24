import sys, tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image
from anclicker.platform.qt_compat.QtWidgets import QApplication
from anclicker.domain.instructions import ExecutionContext, CommandRecord
from anclicker.instructions.registry import get_instruction_spec
from anclicker.execution import actions
class DB:
    def extract_resource_folder_path(self): return []
    def get_setting_value(self, key): return ''
    def get_variable_info(self, *args): return {}
app = QApplication([])
context = ExecutionContext(metadata={'database': DB()})
spec = get_instruction_spec('窗口图像点击')
assert spec.category == '窗口键鼠'
target = {'窗口句柄':'123','窗口标题':'Test','区域偏移':[1,2,-3,-4]}
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp)/'test.png'
    Image.new('RGB',(10,10)).save(path)
    params = {'图像路径':str(path),'区域':'(10,20,100,200)','区域模式':'跟随窗口','区域窗口':target}
    editor = spec.create_editor(context=context, draft={'type_id':spec.type_id,'parameters':params})
    assert editor.region_group.isHidden()
    assert not editor.follow_region_group.isHidden()
    assert not editor.follow_region_group.isCheckable()
    draft = editor.get_draft()
    assert draft.type_id == '窗口图像点击'
    assert draft.parameters['区域窗口'] == target
    assert draft.parameters['区域模式'] == '跟随窗口'
    editor.load_draft(draft)
    assert editor.get_draft().parameters == draft.parameters
    editor._region_target = None
    try:
        editor.get_draft()
        raise AssertionError('missing target allowed')
    except ValueError: pass
    editor.close()
    normal = get_instruction_spec('图像点击').create_editor(context=context)
    assert normal.follow_region_group.isHidden()
    assert not normal.region_group.isHidden()
    normal.load_draft({'type_id':'图像点击','parameters':params})
    assert not normal.follow_region_group.isHidden()
    assert normal.get_draft().parameters['区域窗口'] == target
    normal.close()
    with patch.object(actions,'click_image',return_value=(20,30)) as click:
        result = spec.create_executor().execute_once(context,CommandRecord(None,spec.type_id,params))
        assert result == (20,30)
        assert click.call_args.args[0]['区域窗口'] == target
    with patch.object(actions,'click_image') as click:
        try:
            spec.create_executor().execute_once(context,CommandRecord(None,spec.type_id,{'图像路径':str(path)}))
            raise AssertionError('unbounded search allowed')
        except ValueError: pass
        click.assert_not_called()
print('PASS: window image registry, dedicated UI, mandatory window, offsets roundtrip, legacy compatibility and executor')
