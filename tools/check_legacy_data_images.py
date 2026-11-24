"""Legacy imports recover missing absolute image paths from current Data."""
import os,sys,tempfile,json,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory() as td:
 data=Path(td)/'Data';data.mkdir();os.environ['ANCLICKER_DATA_DIR']=str(data)
 from openpyxl import Workbook,load_workbook
 from anclicker.storage.legacy_workbook import LEGACY_HEADERS,convert_legacy_workbook,save_converted_copy
 from anclicker.storage.migration_tool import inspect_migration,write_migration_bundle
 from anclicker.storage.database import DatabaseOperation
 from anclicker.storage.graph_repository import GraphRepository
 from anclicker.platform.image_paths import resolve_image_reference
 name=uuid.uuid4().hex+'.png';image=data/'图片'/'子目录'/name;image.parent.mkdir(parents=True);image.write_bytes(b'image sentinel')
 old='Z:/removed-install/Data/old-images/'+name
 book=Workbook();book.active.title='主流程';book.active.append(LEGACY_HEADERS)
 book.active.append([1,old,'图像点击',"{'灰度': 'False', '精度': '0.8', '区域': '(0,0,0,0)'}",None,None,None,1,'自动跳过',''])
 source=data/'old.xlsx';book.save(source);original=source.read_bytes()
 converted=convert_legacy_workbook(book,data)
 assert Path(json.loads(converted['命令'].cell(2,3).value)['图像路径'])==image
 saved=save_converted_copy(converted,source);converted.close()
 with_image=load_workbook(saved);assert Path(json.loads(with_image['命令'].cell(2,3).value)['图像路径'])==image;with_image.close()
 plan=inspect_migration(book,data)
 assert not plan.errors,plan.errors
 assert not plan.missing_resources,plan.missing_resources
 folder,outputs=write_migration_bundle(plan,source)
 db=DatabaseOperation(str(Path(td)/'check.db'));repository=GraphRepository(db.db_path,data_folder=data)
 migrated=load_workbook(outputs['主流程']);repository.import_from_workbook(migrated,source_path=outputs['主流程']);migrated.close()
 command=repository.list_commands()[0]
 assert Path(resolve_image_reference(command.parameters['图像路径'],data_folder=data)).read_bytes()==b'image sentinel'
 assert source.read_bytes()==original
 plan.close()
 # A real missing image remains reported, never replaced with an arbitrary file.
 book.active.cell(2,2).value='Z:/missing/'+uuid.uuid4().hex+'.png'
 missing=inspect_migration(book,data);assert len(missing.missing_resources)==1;missing.close();book.close()
 print('PASS legacy single/batch migration: recursive Data recovery, persisted path, bundle import, missing reporting, original preserved')
