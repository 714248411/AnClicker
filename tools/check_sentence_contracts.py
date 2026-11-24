from models.dual_model import clauses
from models.sentence_contracts import grouped_boundaries
from models.conversational_contracts import boundary_contract
assert clauses('打开 https://example.org/a!b?q=然后再继续，等待三秒')[0]==['打开 https://example.org/a!b?q=然后再继续','等待三秒']
assert clauses('输入“甲，乙；然后再说！”，等待2秒')[0]==['输入“甲，乙；然后再说！”','等待2秒']
for parts,cuts in [(['等待','三秒','输入','“你好”'],[False,True,False]),(['打开网页','地址是https://hao123.com','搜索','123123'],[False,True,False]),(['复制','“E:/a.txt”','到','“E:/b.txt”','等待2秒'],[False,False,False,True])]:
 assert boundary_contract(parts,grouped_boundaries(parts,[True]*(len(parts)-1)))==cuts
print('PASS URL/quoted payload preservation and punctuation argument grouping')
