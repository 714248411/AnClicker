"""Export the actual tool/palette contract for model integrations and training."""
import json,sys
from pathlib import Path

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[1]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'anclicker': ('import', 'anclicker', (), False),
    'VERSION_TOOLS_catalog_instruction_schema': ('from', 'anclicker.domain.agent_protocol', ('VERSION', 'TOOLS', 'catalog', 'instruction_schema'), 0),
})

root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
anclicker = _module_imports.load('anclicker')  # Enable source-tree legacy entry points.
VERSION, TOOLS, catalog, instruction_schema = _module_imports.load('VERSION_TOOLS_catalog_instruction_schema')
if __name__=='__main__':
    target=root/'docs/agent-protocol-v1.json'
    target.write_text(json.dumps({'protocol':VERSION,'tools':TOOLS,'catalog':catalog(),
      'instructions':[instruction_schema(item['type_id']) for item in catalog()],
      'response_examples':[{'type':'tool_call','name':'instructions_search','arguments':{'query':'等待'}},
        {'type':'message','content':'请补充需要点击的图片路径。'}],
      'draft_format':{'protocol':VERSION,'kind':'instruction_drafts','instructions':[
        {'type_id':'时间等待','parameters':{'时长':2},'repeat_count':1,'error_policy':'提示异常并暂停','note':''}]}},ensure_ascii=False,indent=2),encoding='utf-8')
    print(str(target))
