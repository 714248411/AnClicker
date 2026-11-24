"""Ground explicit desktop parameters in the request; the converter still emits the instruction."""
import re
from models.sentence_contracts import clean_action
from models.conversational_contracts import intent_text,quoted_values,no_enter
from models.chinese_planner import chinese_number

def grounded_instruction(step,drafts=()):
    text=clean_action(step);t=intent_text(text)
    if re.match(r'^(?:不要|别|不必|不用)',t):return None
    aliases={'敲个回车':'按回车','敲一下回车键':'按回车','全选一下':'全选','撤销一下':'撤销','粘贴一下':'粘贴','切到下一个窗口':'按Alt+Tab','切换到下一个窗口':'按Alt+Tab'}
    text=aliases.get(text,text);t=intent_text(text)
    text=re.sub(r'(按(?:一下|下)?)(空格|删除|退格)(?:键)?$',lambda m:m[1]+{'空格':'space','删除':'delete','退格':'backspace'}[m[2]],text)
    keys=re.fullmatch(r'(?:用键盘)?(?:按|按下|按一下|敲|敲一下)(?:键盘)?\s*((?:(?:ctrl|alt|shift|win)\s*\+\s*)*(?:[a-z0-9]|tab|enter|esc|escape|space|backspace|delete|f[1-9][0-2]?|回车|回车键))\s*(?:键|一下|就好|就行|吧)?(?:[，,]\s*(?:麻烦照这个做|就按这里给的内容来))?',text,re.I)
    if keys:
        key=re.sub(r'\s+','',keys[1]).lower();key={'回车':'enter','回车键':'enter','escape':'esc'}.get(key,key)
        return '按下键盘',{'按键':key}
    shortcuts={'全选':'ctrl+a','粘贴':'ctrl+v','撤销':'ctrl+z'}
    if t in shortcuts:return '按下键盘',{'按键':shortcuts[t]}
    if t=='复制' and drafts and drafts[-1].type_id=='按下键盘':return '按下键盘',{'按键':'ctrl+c'}
    click_allowed=not re.search(r'(?:不要|不用|别|无需)\s*(?:再|去)?(?:点击|单击|双击|点(?:一下|进去|开)?)',t)
    selector=re.search(r'CSS\s*(#[A-Za-z_][\w:-]*)',t,re.I)
    if selector:
        if re.search(r'输入|填(?:入|写|上)?|写(?:入|上)?|打上',t) and not re.search(r'提取|读取|表格|Excel|单元格|(?:不要|不用|别|无需)\s*(?:输入|填|写)',t,re.I) and len(quoted_values(text))==1:
            return '输入文本',{'selector':selector[1],'by':'CSS选择器','text':quoted_values(text)[0],'pressEnter':'是' if re.search(r'回车|提交',t) and not no_enter(text) else '否'}
        if click_allowed and re.search(r'点击|单击|点一下|点进去|点开',t):return '点击元素',{'selector':selector[1],'by':'CSS选择器'}
    paths=[v for v in quoted_values(text) if re.match(r'^[A-Za-z]:[/\\]',v) and re.search(r'\.(?:png|jpg|jpeg|bmp)$',v,re.I)]
    if click_allowed and len(paths)==1 and re.search(r'图片|图像|屏幕',t) and re.search(r'点击|单击|双击',t):
        action=('右键' if '右键' in t else '左键')+('双击' if '双击' in t else '单击')
        return '图像点击',{'图像路径':paths[0],'动作':action}
    coord=re.search(r'坐标\s*[（(]?\s*([0-9]+)\s*[,，-]\s*([0-9]+)\s*[）)]?',text)
    if click_allowed and coord and re.search(r'点击|单击|双击|点一下',t):
        return '坐标点击',{'坐标':coord[1]+'-'+coord[2],'动作':('右键' if '右键' in t else '左键')+('双击' if '双击' in t else '单击')}
    if click_allowed and (re.search(r'当前位置',t) or ('鼠标' in t and re.search(r'别挪|原地|现在的位置|就这儿',t))) and re.search(r'点|击',t):
        return '鼠标点击',{'鼠标':'右键' if '右键' in t else '中键' if '中键' in t else '左键','次数':2 if '双击' in t else 1}
    scroll=re.search(r'(?:向|往)([上下])(?:滚|滑动|滚动)\s*([零一二三四五六七八九十百两0-9]+)\s*(?:格|次)',t)
    if scroll:return '滚轮滑动',{'方向':'向'+scroll[1],'距离':int(chinese_number(scroll[2]))}
    return None

def grounded_schema(kind,params):
    return {'type':'object','properties':{'type_id':{'const':kind},'parameters':{'type':'object','properties':{k:{'const':v} for k,v in params.items()},'required':list(params),'additionalProperties':False}},'required':['type_id','parameters'],'additionalProperties':False}
