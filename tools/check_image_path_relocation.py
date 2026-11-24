import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from anclicker.platform.image_paths import resolve_image_reference,store_image_reference
with tempfile.TemporaryDirectory() as td:
 root=Path(td)/'data'; image=root/'images'/'nested'/'capture.png';image.parent.mkdir(parents=True);image.write_bytes(b'test')
 for value in ('images/nested/capture.png','data/images/nested/capture.png','../data/images/nested/capture.png','Z:/old/install/data/images/nested/capture.png','capture.png'):
  assert Path(resolve_image_reference(value,data_folder=root))==image,(value,resolve_image_reference(value,data_folder=root))
  assert store_image_reference(value,data_folder=root)=='images/nested/capture.png'
 assert Path(resolve_image_reference('images/other/capture.png',data_folder=root))==image
 assert not Path(resolve_image_reference('data/../../escape.png',data_folder=root)).is_file()
 (root/'images'/'capture.png').write_bytes(b'other')
 try:resolve_image_reference('capture.png',data_folder=root)
 except ValueError:pass
 else:raise AssertionError('Ambiguous image selected')
 print('PASS portable Data paths, moved installs, stable references, missing and duplicate images')

with tempfile.TemporaryDirectory() as td:
 install=Path(td)/'AnClicker'; local=install/'Data/images/capture.png';local.parent.mkdir(parents=True);local.write_bytes(b'local')
 external=Path(td)/'old/data/images/capture.png';external.parent.mkdir(parents=True);external.write_bytes(b'old')
 data=Path(td)/'other-data';data.mkdir()
 assert Path(resolve_image_reference(str(external),data_folder=data,install_folder=install))==external
 external.unlink()
 for value in (str(external),'images/capture.png','Data/images/capture.png','capture.png'):
  assert Path(resolve_image_reference(value,data_folder=data,install_folder=install))==local,value
 local.unlink()
 assert not Path(resolve_image_reference(str(external),data_folder=data,install_folder=install)).is_file()
 assert resolve_image_reference('{{图片}}',install_folder=install)=='{{图片}}'
 print('PASS explicit absolute path first, Data fallback only when missing')

with tempfile.TemporaryDirectory() as td:
 from unittest.mock import patch
 from types import SimpleNamespace
 from anclicker.domain.instructions import CommandRecord,ExecutionContext
 from anclicker.platform.image_paths import repair_command_image_paths
 from anclicker.storage.database import DatabaseOperation
 from anclicker.storage.graph_repository import GraphRepository
 from anclicker.domain.instructions import InstructionDraft
 base=Path(td);data=base/'Data';nested=data/'截图归档'/'第二层';nested.mkdir(parents=True)
 db=DatabaseOperation(str(data/'commands.db'));repo=GraphRepository(db.db_path)
 missing=str(base/'gone'/'unique.png')
 record=repo.add_command(InstructionDraft('图像点击',{'图像路径':missing},2,'自动跳过','保留备注'))
 image=nested/'unique.png';image.write_bytes(b'image')
 context=ExecutionContext();context.metadata['database']=db
 with patch('anclicker.platform.image_paths.DATA_FOLDER',str(data)),patch('anclicker.platform.image_paths.get_install_folder',return_value=str(base)):
  assert repair_command_image_paths(record,context)
  saved=repo.get_command(record.id)
  assert Path(resolve_image_reference(saved.parameters['图像路径']))==image
  assert saved.repeat_count==2 and saved.note=='保留备注'
  assert not repair_command_image_paths(record,context)
  variable=CommandRecord(None,'图像点击',{'图像路径':'{{图片}}'})
  assert not repair_command_image_paths(variable,context)
 print('PASS recursive Data recovery, persisted command, stable second run and variables')

with tempfile.TemporaryDirectory() as td:
 base=Path(td);current=base/'current';current.mkdir()
 (current/'sq.version').write_text('managed');(base/'Update.exe').write_bytes(b'update')
 image=base/'Data'/'nested'/'managed.png';image.parent.mkdir(parents=True);image.write_bytes(b'image')
 assert Path(resolve_image_reference('Z:/gone/managed.png',install_folder=current,data_folder=base/'separate'))==image
 print('PASS managed portable searches root Data outside replaceable current')
