import json
def judge(case,response):
 items=response.get('arguments',{}).get('instructions',[]);errors=[]
 if 'question' in case:
  if response.get('type')!='message' or not any(s in response.get('content','') for s in case['question']):errors.append('没有针对缺少的信息追问')
  return errors
 if 'types' in case and [('时间等待' if i['type_id']=='等待（秒）' else i['type_id']) for i in items]!=case['types']:errors.append('指令类型或动作数量不符')
 if 'search' in case:
  searches=[i['parameters'] for i in items if i['type_id']=='输入文本']
  if len(searches)!=1 or searches[0].get('text')!=case['search']:errors.append('搜索词改变')
 if 'url' in case and not any(i['parameters'].get('url','').rstrip('/')==case['url'].rstrip('/') for i in items):errors.append('网址不符')
 if 'key' in case and not any(str(i['parameters'].get('按键','')).lower()==case['key'] for i in items):errors.append('按键不符')
 if 'repeat' in case and not any(i.get('repeat_count',1)==case['repeat'] for i in items):errors.append('重复次数不符')
 if 'direction' in case and not any(i['parameters'].get('方向')==case['direction'] for i in items):errors.append('滚动方向不符')
 if 'seconds' in case:
  waits=[({'时长':i['parameters'].get('seconds'),'单位':'秒'} if i['type_id']=='等待（秒）' else i['parameters']) for i in items if i['type_id'] in ('时间等待','等待（秒）')]
  if not waits or not any(str(w.get('时长')) in (str(case['seconds']),str(float(case['seconds']))) and w.get('单位','秒')=='秒' for w in waits):errors.append('等待时间不符')
 if 'literal' in case and not any(i['parameters'].get('内容')==case['literal'] for i in items):errors.append('输入原文改变')
 if case.get('no_enter') and (any(i['type_id'] in ('按下键盘','按键') for i in items) or any(i['parameters'].get('pressEnter')=='是' for i in items)):errors.append('违反不要回车/提交')
 if case.get('not_path'):
  if not items or any('C:/Users' in json.dumps(i) or 'C:\\Users' in json.dumps(i) for i in items):errors.append('回收站缺绑定或伪造路径')
 return errors
