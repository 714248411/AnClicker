import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from openpyxl import Workbook
from anclicker.storage.legacy_workbook import is_graph_workbook,convert_legacy_workbook
from anclicker.storage.migration_tool import needs_batch_migration,inspect_migration
from anclicker.domain.graph_models import COMMAND_SHEET_HEADERS,NODE_SHEET_HEADERS,EDGE_SHEET_HEADERS,SETTINGS_SHEET_HEADERS
b=Workbook();b.remove(b.active)
for name,headers in [('命令',COMMAND_SHEET_HEADERS),('节点',NODE_SHEET_HEADERS),('连线',EDGE_SHEET_HEADERS),('设置',SETTINGS_SHEET_HEADERS)]:b.create_sheet(name).append(headers)
for i in range(1,4):b['命令'].append([i,'时间等待','{}',1,'自动跳过','',i-1])
b.create_sheet('未知附表').append(['保留的数据'])
assert is_graph_workbook(b) and not needs_batch_migration(b)
assert convert_legacy_workbook(b) is b
plan=inspect_migration(b)
assert plan.source_commands==3 and len(plan.errors)==1 and '流程图' in plan.errors[0]['error']
assert '未知附表' in b.sheetnames
plan.close();b.close()
print('PASS graph documents never treated as legacy branches; counts only actual commands; unsupported sheets preserved')
