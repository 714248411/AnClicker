import requests,json
r=requests.get('https://api.github.com/repos/714248411/AnClicker/releases?per_page=10',timeout=30);r.raise_for_status()
print(json.dumps([{'tag':x['tag_name'],'url':x['html_url']} for x in r.json()],ensure_ascii=False))
