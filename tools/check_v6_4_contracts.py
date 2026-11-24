from models.dual_model import clauses
from models.sentence_contracts import input_text_value,payload_value
from models.desktop_contracts import grounded_instruction
assert clauses('输入再见，然后等两秒')[0]==['输入再见','等两秒']
assert clauses('输入并列第一，再等两秒')[0]==['输入并列第一','等两秒']
assert clauses('先等两秒然后输入你好再等三秒')[0]==['先等两秒','输入你好','等三秒']
assert clauses('鼠标点击坐标（100，200），然后等两秒')[0]==['鼠标点击坐标（100，200）','等两秒']
assert input_text_value('输入周五，哦不，改成周六')=='周六'
assert payload_value('北京天气，不对，改成上海天气，别提交')=='上海天气'
assert grounded_instruction('按一下Ctrl+A')==('按下键盘',{'按键':'ctrl+a'})
assert grounded_instruction('鼠标点击坐标（100，200）')==('坐标点击',{'坐标':'100-200','动作':'左键单击'})
assert grounded_instruction('不要按Ctrl+A') is None
print('PASS word preservation, compound commands, corrections, coordinates, key grounding and negation')

from models.sentence_contracts import grouped_boundaries
from models.conversational_contracts import clarification
assert input_text_value('输入“周一交稿”，说错了，改成“周三交稿”')=='周三交稿'
assert input_text_value('输入“字面，改成内容”')=='字面，改成内容'
assert input_text_value('输入甲，改成“乙”，改为 “丙”')=='丙'
assert clarification('打开https://example.org，然后点右边那个按钮')
assert clarification('点击 CSS #right') is None
parts=clauses('读取UTF-8文件“E:/test.txt”并计算行数')[0]
assert grouped_boundaries(parts,[True])==[False]
assert grouped_boundaries(['读取文件“E:/test.txt”','计算文件“E:/other.txt”的SHA256'],[True])==[True]
print('PASS quoted corrections, missing click target and dependent file computation')
