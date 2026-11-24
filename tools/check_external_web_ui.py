import runpy
scope=runpy.run_path('tools/check_background_web_ui.py')
ui,app,bridge,pump,patch=[scope[k] for k in ('ui','app','bridge','pump','patch')]
pages=scope['pages']
pages[:]=[{'id':'remote1','remote':True,'endpoint':'http://127.0.0.1:12345','session':'http://127.0.0.1:12345','engine':'外部 CDP','url':'https://example.test','title':'external'}]
with patch.object(ui,'get_bridge',return_value=bridge),patch.object(ui,'discover_endpoints',return_value=[]):
 for spec in scope['iter_instruction_specs']('网页后台操作'):
  params={'browserWindow':dict(pages[0])}
  if '点击' in spec.type_id: params['points']='40,50'
  e=spec.create_editor(draft=scope['InstructionDraft'](spec.type_id,params))
  before=len(bridge.calls);pump(lambda:len(bridge.calls)>before and not e._refreshing)
  assert e.get_draft().parameters['browserWindow']==pages[0]
  before=len(bridge.calls)
  with patch.object(ui.QInputDialog,'getText',return_value=('https://example.test',True)):e.open_web()
  pump(lambda:len(bridge.calls)>before and not e._refreshing)
  assert bridge.calls[-1]['id']=='acOpenRemotePage'
  assert e.get_draft().parameters['browserWindow']==pages[0]
  e.close();e.deleteLater();app.processEvents()
print('PASS external selection persistence and open-web routing for all three editors')
