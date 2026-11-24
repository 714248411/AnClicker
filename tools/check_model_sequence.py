import sys
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.sequence_text import model_steps
from models.draft_planner import candidate_types,planning_schema
assert model_steps('输入“先复制然后打开”，然后按回车')==['输入“先复制然后打开”','按回车']
assert model_steps('不要再打开文件夹')==['不要再打开文件夹']
assert model_steps('如果存在则打开，否则等待')==['如果存在则打开，否则等待']
assert len(model_steps('第一步：等待一秒\n第二步：按回车'))==2
assert len(model_steps('往当前文本框填入“完成”后，用回车提交'))==2
assert candidate_types('先将“C:/输入/a.txt”复制到“C:/输出/b.txt”')==['快速文件操作']
assert candidate_types('在当前输入框键入“示例”，不用回车')==['文本输入']
assert candidate_types('使用 CMD 在“C:/输出”创建目录')==['运行cmd']
schema=planning_schema(['文本输入'],text='输入“原样内容”')
assert schema['oneOf'][0]['properties']['arguments']['properties']['instructions']['items']['oneOf'][0]['properties']['parameters']['properties']['内容']['enum']==['原样内容']
print('PASS quoted connectors, negation, conditional preservation, file intent, tool preference and literal fidelity')
