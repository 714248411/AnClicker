"""Split explicit Chinese ordering outside quoted data; never select an operation."""
import re
from models.chinese_planner import split_numbered_steps

def model_steps(text):
    numbered=split_numbered_steps(text)
    if numbered:
        intro,steps=numbered
        return [(intro+'\n'+s).strip() for s in steps]
    if re.search(r'如果|否则|当.+时|直到|循环|重复',text):return [text]
    quote=None;parts=[];start=0;i=0
    while i<len(text):
        char=text[i]
        if quote:
            if char==quote:quote=None
            i+=1;continue
        if char in ('“','"','「','『'):
            quote={'“':'”','"':'"','「':'」','『':'』'}[char];i+=1;continue
        match=re.match(r'(?:然后|接着|随后|之后|后[，,]|再(?!次))',text[i:])
        negative=any(text[:i].endswith(word) for word in ('不','别','勿','不要','不用','无需'))
        if match and not negative:
            part=text[start:i].strip(' ，,；;。\n')
            if part:parts.append(part)
            i+=len(match[0]);start=i;continue
        i+=1
    tail=text[start:].strip(' ，,；;。\n')
    if tail:parts.append(tail)
    return parts if len(parts)>1 else [text]
