from copy import deepcopy
from models.workflow_ast import from_drafts
from models.workflow_mermaid import to_mermaid,from_mermaid
from anclicker.domain.agent_protocol import make_draft

def main():
    ast=from_drafts([make_draft('文本输入',{'内容':'中文 "引号"\n第二行; --> & <tag>'}),make_draft('时间等待',{'时长':3,'单位':'秒'}),make_draft('时间等待',{'时长':4,'单位':'秒'})],7)
    source=to_mermaid(ast);assert from_mermaid(source)==ast
    changed=source.replace('n1 --> n2','n1 --> n3').replace('n2 --> n3','n3 --> n2')
    assert [n['id'] for n in from_mermaid(changed)['nodes']]==['n1','n3','n2']
    for bad in [source+'n1 --> n3\n',source+'n3 --> n1\n',source.replace('n2 --> n3',''),source.replace('n1["文本输入"]','n1["运行cmd"]'),source+'click n1 "https://example.org"\n']:
        try:from_mermaid(bad)
        except ValueError:pass
        else:raise AssertionError('Unsupported/lossy diagram accepted')
    empty=from_drafts([]);assert from_mermaid(to_mermaid(empty))==empty
    print('PASS Mermaid lossless roundtrip, link reordering, unicode, parameters, cycle/branch/missing metadata rejection')
if __name__=='__main__':main()
