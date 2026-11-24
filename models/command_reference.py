"""Offline, source-attributed Windows command reference lookup."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'knowledge'
def search_commands(query):
    curated=json.loads((ROOT/'cmd_reference.json').read_text(encoding='utf-8'))['commands']
    index=json.loads((ROOT/'cmd_index.json').read_text(encoding='utf-8'))['commands'] if (ROOT/'cmd_index.json').is_file() else []
    query=query.casefold().strip()
    def match(item):
        return not query or query in (item['name']+' '+item.get('purpose','')).casefold() or bool(re.search(r'(?<![a-z])'+re.escape(item['name'])+r'(?![a-z])',query))
    aliases={'dir':r'列出|目录列表','start':r'打开','copy':r'复制|拷贝','robocopy':r'复制|拷贝','mkdir':r'创建.*目录|新建.*文件夹','ren':r'重命名|改名','findstr':r'搜索|查找.*文本|包含.*行','find':r'查找.*行','where':r'程序路径|可执行.*路径'}
    known=[item for item in curated if match(item) or re.search(aliases.get(item['name'],r'(?!)'),query)]
    links=[item for item in index if match(item) and item['name'] not in {x['name'] for x in known}]
    return {'reviewed':known,'reference_links':links[:30],'reference_total':len(links),'note':'索引条目不等于已训练或已实测；本工具不执行命令。'}
