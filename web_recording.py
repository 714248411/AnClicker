"""Convert timestamped browser events into editable persisted instructions."""
from instructions.models import InstructionDraft

def events_to_web_drafts(url, events, elapsed=0):
    drafts=[InstructionDraft('打开网页', {'url':url,'engine':'Chrome','target':'新窗口',
        'loginMode':'独立登录(每次全新)','waitType':'加载完成'},note='网页录制')]
    merged=[]
    for event in events:
        event=dict(event)
        if event.get('type')=='input' and merged and merged[-1].get('type')=='input' and merged[-1].get('selector')==event.get('selector'):
            merged[-1]=event
        else:
            merged.append(event)
    previous=0
    for event in merged:
        kind=event.get('type');selector=event.get('selector','')
        if kind=='click':
            command=InstructionDraft('点击元素',{'selector':selector,'by':'CSS选择器','clickType':'单击'})
        elif kind=='input':
            command=InstructionDraft('输入文本',{'selector':selector,'by':'CSS选择器','text':event.get('text',''),'clear':'是','pressEnter':'否'})
        elif kind=='key':
            command=InstructionDraft('按键',{'key':'回车(Enter)' if event.get('key')=='Enter' else 'Tab','times':1})
        elif kind=='directNavigation':
            command=InstructionDraft('打开网页',{'url':event['url'],'engine':'Chrome','target':'当前标签页','waitType':'加载完成'})
        elif kind=='navigation':
            # The preceding click/Enter already triggers navigation. Wait rather than navigate twice.
            command=InstructionDraft('等待页面加载完成',{'timeout':30})
        else:
            continue
        at=max(previous,float(event.get('at',previous)))
        if at-previous>=1:
            drafts.append(InstructionDraft('等待（秒）',{'seconds':round((at-previous)/1000,3)},note='网页录制等待'))
        command.note='网页录制'
        drafts.append(command)
        previous=at
    if float(elapsed)-previous>=1:
        drafts.append(InstructionDraft('等待（秒）',{'seconds':round((float(elapsed)-previous)/1000,3)},note='网页录制等待'))
    return drafts
