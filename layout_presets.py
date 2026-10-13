"""Named interface layouts, independent of command order and workflow data."""
import base64
import json
import uuid
from qt_compat.QtCore import QByteArray
from qt_compat.QtWidgets import QInputDialog, QMessageBox

SETTING='界面方案'

class LayoutPresets:
    def __init__(self, view, menu):
        self.view,self.window,self.menu=view,view.window,menu
        try:
            data=json.loads(self.window.db.get_setting_value(SETTING) or '{}')
        except (ValueError,TypeError): data={}
        if not isinstance(data,dict): data={}
        self.items=[x for x in data.get('items',[]) if isinstance(x,dict) and isinstance(x.get('name'),str) and isinstance(x.get('layout'),dict) and isinstance(x.get('id'),str)] if isinstance(data.get('items',[]),list) else []
        self.selected=data.get('selected')
        self.next_number=max(1,data.get('next',1)) if isinstance(data.get('next',1),int) else 1
        self.refresh()

    def persist(self):
        self.window.db.set_setting_value(SETTING,json.dumps({'items':self.items,'selected':self.selected,'next':self.next_number},ensure_ascii=False))

    def current(self):
        return next((x for x in self.items if x['id']==self.selected),None)

    def refresh(self):
        self.menu.clear()
        for item in self.items:
            action=self.menu.addAction(item['name']);action.setCheckable(True)
            action.setChecked(item['id']==self.selected)
            action.triggered.connect(lambda checked=False,key=item['id']:self.apply(key))
        if not self.items:self.menu.addAction('暂无保存的界面方案').setEnabled(False)
        self.menu.addSeparator()
        self.menu.addAction('保存方案',self.save)
        self.menu.addAction('删除方案',self.delete).setEnabled(self.current() is not None)
        self.menu.addAction('更名',self.rename).setEnabled(self.current() is not None)
        self.menu.addSeparator()
        self.menu.addAction(self.view.restore_view_action)

    def capture(self):
        v=self.view;d=v.docking
        if v.compact.active:v.compact.set_active(False)
        return {'state':base64.b64encode(bytes(d.host.saveState(1))).decode('ascii'),
                'pages':list(d.placeholders),'toolbar':base64.b64encode(bytes(self.window.saveState(1))).decode('ascii'),
                'palette_collapsed':v.palette_collapsed,'controls_visible':v.controls_action.isChecked(),
                'palette_side':v.palette_side,'tab':v.tabs.currentIndex(),'table_sizes':v.table_splitter.sizes()}

    def save(self):
        names={x['name'] for x in self.items}
        while f'方案{self.next_number}' in names:self.next_number+=1
        item={'id':uuid.uuid4().hex,'name':f'方案{self.next_number}','layout':self.capture()}
        self.next_number+=1;self.items.append(item);self.selected=item['id']
        self.persist();self.refresh()

    def apply(self, key):
        item=next((x for x in self.items if x['id']==key),None)
        if item is None:return
        data=item['layout'];v=self.view;d=v.docking
        try:
            state=QByteArray(base64.b64decode(data['state'],validate=True))
            toolbar=QByteArray(base64.b64decode(data['toolbar'],validate=True))
            pages=data.get('pages',[])
            if not isinstance(pages,list) or not all(isinstance(k,str) for k in pages):raise ValueError('invalid pages')
        except (ValueError,TypeError,KeyError):
            QMessageBox.warning(self.window,'界面方案','方案数据无效，无法应用。');return
        d.reset_layout()
        d.restoring=True
        try:
            for page in pages:d.ensure_dock(page)
            if not d.host.restoreState(state,1):raise ValueError('停靠布局无法恢复')
            self.window.restoreState(toolbar,1)
            v.palette_collapsed=data.get('palette_collapsed') is True
            v.palette_side='right' if data.get('palette_side')=='right' else 'left'
            v.controls_action.setChecked(data.get('controls_visible') is not False)
            sizes=data.get('table_sizes',[])
            if isinstance(sizes,list) and len(sizes)==2 and all(isinstance(x,int) and x>=0 for x in sizes):v.table_splitter.setSizes(sizes)
            tab=data.get('tab',0)
            v.tabs.setCurrentIndex(tab if isinstance(tab,int) and 0<=tab<v.tabs.count() else 0)
            d.update_controls_layout();d.sync_visibility();v._update_view_actions()
        except ValueError as error:
            QMessageBox.warning(self.window,'界面方案',str(error));return
        finally:
            d.restoring=False;d.save()
        self.selected=key;self.persist();self.refresh()
        self.window.statusBar.showMessage('已应用 '+item['name'],3000)

    def delete(self):
        if self.current() is None:return
        self.items=[x for x in self.items if x['id']!=self.selected]
        self.selected=None;self.persist();self.refresh()

    def rename(self):
        item=self.current()
        if item is None:return
        text,ok=QInputDialog.getText(self.window,'更名','方案名称：',text=item['name'])
        if not ok:return
        name=text.strip()
        if not name or any(x['name']==name and x is not item for x in self.items):
            QMessageBox.warning(self.window,'更名','请输入非空且不重复的方案名称。');return
        item['name']=name;self.persist();self.refresh()

    def reset(self):
        self.view.docking.reset_layout()
        self.selected=None;self.persist();self.refresh()
