"""Source-grounded bare domains and website search context."""
import re
from urllib.parse import urlsplit
DOMAIN=re.compile(r'(?<![A-Za-z0-9_@/.:\\-])(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+(?:com|cn|org|net|edu|gov|io|dev|co|info|me|app)(?::[0-9]{1,5})?(?:/[^\s，,；;。！？“”"<>]*)?(?![A-Za-z0-9_.-])',re.I)
URL=re.compile(r'https?://[^\s，,；;。！？“”"<>]+',re.I)

def normalize_web_request(text):
    from models.conversational_contracts import QUOTED,intent_text
    # Resolve navigation names only outside quoted data.
    def aliases(segment):
        def navigation_only(pattern,replacement):
            def replace(match):
                actions=list(re.finditer(r'输入|写上|搜索|搜一下|查找|打开|访问|进入',segment[:match.start()]))
                if actions and actions[-1][0] in ('输入','写上','搜索','搜一下','查找'):return match[0]
                return replacement
            return re.sub(pattern,replace,segment)
        segment=navigation_only(r'(?:打开|访问|进入)(?:一下)?(?:网页)?\s*百度(?:首页|网站)?(?=$|[，,；;。\s]|然后|接着|搜索|搜)', '打开网页 https://www.baidu.com')
        segment=navigation_only(r'(?:去|在)?百度(?:上)?(?:搜一下|搜索|搜)\s*', '打开网页 https://www.baidu.com，搜索')
        return segment
    chunks=[];pos=0
    for quote in QUOTED.finditer(text):
        chunks.extend([aliases(text[pos:quote.start()]),quote[0]]);pos=quote.end()
    chunks.append(aliases(text[pos:]));text=''.join(chunks)
    text=re.sub(r'(https://www\.baidu\.com)(?=搜索|搜)',r'\1，',text)
    quotes=list(QUOTED.finditer(text))
    def replace(m):
        prefix=text[:m.start()]
        # Text/search payloads are data, not a navigation request.
        last=list(re.finditer(r'打开|访问|进入|输入|写上|搜索|查找',intent_text(prefix)))
        if last and last[-1][0] in ('输入','写上','搜索','查找'):return m[0]
        if last and re.search(r'文件|目录|文件夹',prefix[last[-1].start():]):return m[0]
        quoted=next((q for q in quotes if q.start()<=m.start()<q.end()),None)
        if quoted and quoted[0][1:-1]!=m[0]:return m[0]
        return 'https://'+m[0]
    normalized=DOMAIN.sub(replace,text)
    # Spoken navigation may give the action first and its URL in the next clause.
    # Fold only an empty web-open clause followed immediately by an explicit URL;
    # quoted text and input/search payloads must not become navigation.
    def attach_navigation(segment):
        pattern=r'(^|[，,；;。\n])\s*((?:(?:请|帮我|麻烦)\s*)*打开(?:一下)?网页)\s*[，,；;。\n]+\s*(?:(?:进入|访问|打开)(?:网页)?\s*|(?:网址|地址)(?:是|为|[:：])?\s*)?('+URL.pattern+r')'
        def attach(match):
            prefix=segment[:match.start()]
            actions=list(re.finditer(r'输入|写上|搜索|搜一下|查找|打开|访问|进入',prefix))
            if actions and actions[-1][0] in ('输入','写上','搜索','搜一下','查找'):return match[0]
            return match[1]+match[2]+' '+match[3]
        return re.sub(pattern,attach,segment,flags=re.I)
    chunks=[];pos=0
    for quote in QUOTED.finditer(normalized):
        chunks.extend([attach_navigation(normalized[pos:quote.start()]),quote[0]]);pos=quote.end()
    chunks.append(attach_navigation(normalized[pos:]));normalized=''.join(chunks)
    # A URL supplied by itself is a navigation shorthand, including before a search.
    head=re.split(r'[，,；;\n]|然后|接着',normalized,maxsplit=1)[0].strip().strip('“”\"')
    navigation=re.fullmatch(r'(?:(?:请|麻烦|帮我|给我)\s*)*(?:去|进|到|上)\s*(https?://[A-Za-z0-9.-]+(?::[0-9]{1,5})?/?)(?:看看|看一下|瞧瞧|逛逛)?[吧呀啊]?',head,re.I)
    if navigation:
        # Only a complete navigation clause is rewritten; typed/search payloads stay data.
        offset=normalized.find(head)
        normalized=normalized[:offset]+'打开网页 '+navigation[1]+normalized[offset+len(head):]
    elif URL.fullmatch(head):
        normalized='打开网页 '+normalized
    return normalized

def url_argument(text):return bool(URL.fullmatch(re.sub(r'^(?:地址|网址)(?:是|为|[:：])?\s*','',text.strip()).strip('“”\"')))

# Selector observed in https://www.hao123.com HTML on 2026-10-26.
SEARCH_FIELDS={'baidu.com':'textarea#chat-textarea, input[name="wd"]','www.baidu.com':'textarea#chat-textarea, input[name="wd"]','hao123.com':"input[data-hook='searchInput']",'www.hao123.com':"input[data-hook='searchInput']"}
def search_request(step):
    from models.sentence_contracts import clean_action
    t=clean_action(step)
    m=re.fullmatch(r'(?:其中|在其中|在里面|在网页中|在网页里|在页面中|在页面里)?\s*(?:搜索|搜一下|搜)\s*(.*)',t)
    if m:return m[1].lstrip(' ，,：:'),True
    m=re.fullmatch(r'(?:在)?搜索框(?:里|中)?(?:帮我)?(?:输入|填入|写上)\s*(.*)',t)
    if m:return m[1].lstrip(' ，,：:'),False
    return None

def search_parameters(step,drafts):
    request=search_request(step)
    if request is None:return None
    query,submit=request
    from models.conversational_contracts import no_enter
    from models.sentence_contracts import payload_value
    submit=submit and not no_enter(step)
    query=payload_value(query)
    if not query:return None
    for draft in reversed(drafts):
        if draft.type_id=='打开网页':
            selector=SEARCH_FIELDS.get(urlsplit(draft.parameters.get('url','')).hostname)
            if selector:return {'selector':selector,'by':'CSS选择器','text':query,'pressEnter':'是' if submit else '否','clear':'是'}
            return None
    return None


def page_scroll_parameters(step):
    """An absolute page destination is distinct from relative mouse wheel ticks."""
    from models.sentence_contracts import clean_action
    t=clean_action(step).strip(' ，,。；;')
    t=re.sub(r'^回到(?=(?:网页|页面)(?:的)?(?:顶部|顶端))','滚到',t)
    t=re.sub(r'^翻回(?=最上面)','滚到',t)
    match=re.fullmatch(r'(?:(?:请|帮我|麻烦)\s*)*(?:把)?(?:(?:当前|这个|这张)?(?:网页|页面)(?:往下|向下|往上|向上)?)?(?:(?:往|向|朝)[上下])?(?:滚动|滚|滑动|滑|翻)(?:一下)?(?:到|至)(?:(?:当前|这个)?(?:网页|页面)(?:的)?)?(中间|中部|一半|中央|顶部|顶端|最上面|底部|底端|最下面)(?:部位|位置|处)?',t)
    if not match:return None
    word=match[1]
    return {'position':'中间' if word in ('中间','中部','一半','中央') else '顶部' if word in ('顶部','顶端','最上面') else '底部'}
