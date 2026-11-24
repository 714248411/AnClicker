import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from models.web_contracts import normalize_web_request as normalize
positive={'去hao123.com':'打开网页 https://hao123.com','帮我去hao123.com看看':'打开网页 https://hao123.com','进example.com吧':'打开网页 https://example.com','去hao123.com，然后搜索123123':'打开网页 https://hao123.com，然后搜索123123'}
for source,expected in positive.items():assert normalize(source)==expected,(source,normalize(source))
negative=['输入hao123.com','搜索hao123.com','输入“去hao123.com”','别去hao123.com','不要去hao123.com','打开桌面的hao123.com文件夹']
for source in negative:assert not normalize(source).startswith('打开网页'),(source,normalize(source))
print('PASS',len(positive),'navigation',len(negative),'non-navigation boundaries')
