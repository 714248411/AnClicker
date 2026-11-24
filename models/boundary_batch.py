import json

def _pair_messages(parts,index):
 system='你是电脑自动化任务的拆分器。判断后一句是否需要执行一个新的操作。不要把先后执行的两个操作合并，即使它们服务同一个目标、使用同一个对象。例如搜索之后复制结果、复制之后粘贴、打开目录之后创建文件，都是两个操作。后一句要求打开、搜索、读取、复制、粘贴、输入、点击、等待、保存、新建、切换、滚动、按键等实际动作，new_action=true。只有后一句是前一个动作的参数、方式或禁止事项，而不要求执行新动作时，new_action=false，例如不要提交、别改编号、原件保留、按顺序。否定和引号内的文字不能被当作要执行的动作。不需要判断操作能否执行或是否缺少信息。只返回JSON，不解释。'
 return [{'role':'system','content':system},{'role':'user','content':json.dumps({'前一句':parts[index],'后一句':parts[index+1]},ensure_ascii=False)}]


def batch_messages(parts):
 system=_pair_messages(['a','b'],0)[0]['content'].replace('new_action=true','对应边界为true').replace('new_action=false','对应边界为false')
 system+='输入pairs中的每项都是相邻片段的一对。逐项判断，输出唯一字段boundaries，布尔值顺序与pairs一致，数量必须等于pairs数量。一个pair只对应一个布尔值。只输出JSON对象。'
 return [{'role':'system','content':system},{'role':'user','content':json.dumps({'pairs':[{'前一句':parts[i],'后一句':parts[i+1]} for i in range(len(parts)-1)],'边界数量':len(parts)-1},ensure_ascii=False)}]
