from pathlib import Path
p=Path('models/dual_model.py');c=p.read_text(encoding='utf8')
c=c.replace("        match=re.match(r'(?:", "        pair=re.match(r'[（(]\\s*[0-9]+\\s*[,，]\\s*[0-9]+\\s*[）)]',text[i:])\n        if pair:i+=len(pair[0]);continue\n        match=re.match(r'(?:",1)
c=c.replace("        if match and not negative:\n", "        if match and match[0][0] not in '，,；;。！？!\\n':\n            from models.sentence_contracts import starts_action\n            tail=text[i+len(match[0]):]\n            if not starts_action(tail) and not re.match(r'^(?:不要|不用|无需|别|保留|改成|改为)',tail):match=None\n        if match and not negative:\n",1)
p.write_text(c,encoding='utf8')
p=Path('models/sentence_contracts.py');c=p.read_text(encoding='utf8')
c=c.replace('打开|访问|进入|等待|等|暂停|停留|输入','打开|访问|进入|全选|粘贴|撤销|按|敲|单击|双击|右键|左键|鼠标|向上滚|向下滚|等待|等|暂停|停留|输入',1)
c=c.replace('        if attach:result[i]=False',"        if re.search(r'图片|图像',previous) and quoted_values(group) and re.fullmatch(r'(?:左键|右键)?(?:单击|双击)(?:左键|右键)?',current):attach=True\n        if attach:result[i]=False",1)
p.write_text(c,encoding='utf8')
