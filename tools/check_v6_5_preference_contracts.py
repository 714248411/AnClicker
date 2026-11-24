import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.instruction_compiler import compiler_candidates
from models.desktop_contracts import grounded_instruction
from models.dual_model import validate_conversion
positive=['网页里 CSS #contact700 那个框，帮我填“周五再联系0”，别按回车','往网页 CSS #name 填写“李明”','CSS #note 那儿写入“收到”，别提交','网页 CSS #a 写“输入不是打开网址”']
for s in positive:
 assert compiler_candidates(s)==['输入文本'],(s,compiler_candidates(s))
 g=grounded_instruction(s);assert g and g[0]=='输入文本' and g[1]['pressEnter']=='否',(s,g)
for s in ['按一下 ctrl+a 就行','按 ctrl+c 吧','按ctrl+v就好']:
 assert grounded_instruction(s)[0]=='按下键盘'
for s in ['不要填网页 CSS #a “收到”','网页 CSS #a 别写“收到”','提取网页 CSS #a 到表格','输入“CSS #a 帮我填网址”']:
 assert not (grounded_instruction(s) and grounded_instruction(s)[0]=='输入文本'),s
try:validate_conversion(positive[0],{'type_id':'打开网页','parameters':{'url':'https://invented.invalid'}})
except ValueError:pass
else:raise AssertionError('Invented URL accepted')
print('PASS 12 web/keyboard/negative-boundary and invented URL checks')

for s,kind in [('网页 CSS #details 那里点进去看看','点击元素'),('鼠标别挪，就这儿点一下右键','鼠标点击'),('屏幕上找找“E:/图片/按钮.png”，找到左键单击','图像点击'),('鼠标点一下坐标（321，456）','坐标点击')]:
 assert compiler_candidates(s)==[kind],(s,compiler_candidates(s))
for s in ['不要点网页 CSS #a','不要在坐标（321，456）点一下','查找文件“E:/图片/按钮.png”']:
 assert grounded_instruction(s) is None,s
print('PASS 7 colloquial targeting and negative boundary checks')

for s in ['网页 CSS #a 别点进去','鼠标当前位置不要单击','坐标（321，456）不要点一下']:
 assert grounded_instruction(s) is None,s
print('PASS 3 inline negative-click checks')
