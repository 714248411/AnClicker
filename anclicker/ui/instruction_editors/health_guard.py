"""Full multi-row guard health settings, using the native AnClicker theme."""
import json, threading, time
from anclicker.platform.qt_compat.QtWidgets import (QWidget,QVBoxLayout,QHBoxLayout,QTableWidget,QAbstractItemView,QHeaderView,QPushButton,QLabel,QLineEdit,QComboBox,QCheckBox,QSpinBox,QDialog,QDialogButtonBox,QApplication,QFormLayout,QSizePolicy)
from anclicker.platform.qt_compat.QtCore import Qt,QTimer,QEvent
from anclicker.platform.qt_compat.QtGui import QKeySequence
from anclicker.ui.instruction_editors.vision_tools import VisionEditor
from anclicker.platform.vision_tools.guard_health import rules_from, key_code, MAX_ROWS

class RecordGuardKey(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent);self.value='';self.setWindowTitle('记录触发按键')
        layout=QVBoxLayout(self);self.hint=QLabel('请按一个按键或组合键，也可按鼠标侧键。支持小键盘。');self.hint.setWordWrap(True);layout.addWidget(self.hint)
        cancel=QPushButton('取消');cancel.clicked.connect(self.reject);layout.addWidget(cancel);self.resize(420,150)
    def keyPressEvent(self,event):
        if event.isAutoRepeat():return
        if event.key() in (Qt.Key_Control,Qt.Key_Shift,Qt.Key_Alt,Qt.Key_Meta):return
        parts=[];mods=event.modifiers()
        for flag,name in ((Qt.ControlModifier,'ctrl'),(Qt.ShiftModifier,'shift'),(Qt.AltModifier,'alt'),(Qt.MetaModifier,'win')):
            if mods & flag:parts.append(name)
        if mods & Qt.KeypadModifier:
            mapping={Qt.Key_Asterisk:'nummultiply',Qt.Key_Plus:'numadd',Qt.Key_Minus:'numsubtract',Qt.Key_Slash:'numdivide',Qt.Key_Period:'numdecimal',Qt.Key_Enter:'numenter'}
            key=mapping.get(event.key(),'num'+chr(event.key()) if Qt.Key_0<=event.key()<=Qt.Key_9 else '')
        else:
            key=QKeySequence(event.key()).toString().lower().replace(' ','')
            key={'pgup':'pageup','pgdown':'pagedown','ins':'insert','del':'delete'}.get(key,key)
        try:key_code(key)
        except ValueError as error:self.hint.setText(str(error));return
        self.value='+'.join(parts+[key]);self.accept()
    def mousePressEvent(self,event):
        if event.button() in (Qt.XButton1,Qt.XButton2):
            self.value='xbutton1' if event.button()==Qt.XButton1 else 'xbutton2';self.accept()
        else:super().mousePressEvent(event)

class HealthGuardEditor(VisionEditor):
    def __init__(self,parent=None,draft=None,context=None):
        self.guard_panel=None;self._job=None;self._closing=False
        super().__init__(parent,draft,context)
        panel=QWidget();panel.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed);self.guard_panel=panel;layout=QVBoxLayout(panel);layout.setContentsMargins(0,4,0,4)
        toolbar=QHBoxLayout();layout.addLayout(toolbar)
        self.fold_button=QPushButton('▾ 血条检测');self.fold_button.setCheckable(True);self.fold_button.setChecked(True);self.fold_button.setAutoDefault(False);self.fold_button.clicked.connect(self.toggle_guard);toolbar.addWidget(self.fold_button)
        self._guard_was_disabled=self._controls['守护启用'].currentText()=='关闭'
        self._controls['守护启用'].setCurrentText('启用')
        self.count_label=QLabel();toolbar.addWidget(self.count_label);toolbar.addStretch()
        for text,callback in [('＋',self.add_rule),('－',self.remove_rule),('刷新窗口',self.refresh_windows)]:
            button=QPushButton(text);button.clicked.connect(callback);toolbar.addWidget(button)
        self.advanced_button=QPushButton('高级');self.advanced_button.setCheckable(True);self.advanced_button.setAutoDefault(False);self.advanced_button.toggled.connect(self.toggle_columns);toolbar.addWidget(self.advanced_button)
        self.table=QTableWidget(0,9);self.table.setHorizontalHeaderLabels(['启用','检测坐标 x,y','基准颜色 RGB','取色','触发键','录键','截图来源','目标窗口','容差'])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(38)
        self.table.horizontalHeader().hide();self.table.verticalHeader().hide();self.table.setShowGrid(False)
        self.table.setColumnHidden(6,True);self.table.setColumnHidden(8,True)
        for col,width in enumerate((82,100,108,82,96,62,85,170,60)):self.table.setColumnWidth(col,width)
        self.table.horizontalHeader().setSectionResizeMode(7,QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.guard_hint=QLabel('颜色变化时触发按键。窗口相对坐标、颜色容差可在“高级”中设置。')
        self.guard_hint.setWordWrap(True);layout.addWidget(self.guard_hint)
        self.status=QLabel('');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.ui.visionForm.insertRow(5,panel)
        self.common_rows=[('重复次数',self.repeat_count),('异常处理',self.error_policy),('备注',self.note)]
        self.timing_row=QWidget();timing=QHBoxLayout(self.timing_row);timing.setContentsMargins(0,0,0,0)
        for key in ('连续次数','间隔','冷却'):
            label,control=self.ui.rows[key];self.ui.visionForm.removeWidget(label);self.ui.visionForm.removeWidget(control)
            timing.addWidget(label);timing.addWidget(control,1)
        self.ui.rootLayout.removeItem(self.ui.footerLayout);self.layout().addLayout(self.ui.footerLayout)
        self.windows=[];self.refresh_windows()
        try:rows=rules_from(self._controls['检测规则'].text(),validate=False)
        except (ValueError,TypeError):rows=[]
        for row in rows:
            if self._guard_was_disabled:row=dict(row,enabled=False)
            self.add_rule(row)
        if not rows:self.add_rule()
        if draft is None or not draft.parameters:
            self._controls['检测方式'].setCurrentText('守护取点检测')
            for key in ('间隔','冷却','连续次数'):self._controls[key].setValue(1)
            self._controls['变量'].setText('血条检测结果')
        self._controls['检测方式'].currentTextChanged.connect(self.update_fields)
        self.poll=QTimer(self);self.poll.setInterval(30);self.poll.timeout.connect(self.finish_job)
        self.finished.connect(self._shutdown)
        self.update_fields()
        available=self.screen().availableGeometry() if self.screen() else None
        self.resize(min(1060,available.width()-40) if available else 1060,min(760,available.height()-60) if available else 760)
    def add_rule(self, row=None):
        if isinstance(row,bool) or row is None:row={}
        if self.table.rowCount()>=MAX_ROWS:return
        index=self.table.rowCount();self.table.insertRow(index)
        enabled=QCheckBox('检测'+str(index+1)+':');enabled.setChecked(bool(row.get('enabled',False)));self.table.setCellWidget(index,0,enabled)
        for col,key in ((1,'pos'),(2,'color'),(4,'key')):
            control=QLineEdit(str(row.get(key,'')));control.setPlaceholderText({'pos':'坐标 x,y','color':'颜色 R,G,B','key':'触发键'}[key]);self.table.setCellWidget(index,col,control)
        pick=QPushButton('取色');pick.setMinimumSize(76,34);pick.setToolTip('点击截图上的血条位置，同时记录坐标和 RGB 颜色');pick.clicked.connect(lambda:self.pick_rule(pick));self.table.setCellWidget(index,3,pick)
        record=QPushButton('录键');record.setToolTip('记录触发用的键盘按键或鼠标侧键；颜色请使用左侧取色');record.clicked.connect(lambda:self.record_rule(record));self.table.setCellWidget(index,5,record)
        source=QComboBox();source.addItems(['屏幕','窗口']);source.setCurrentText(row.get('source','屏幕'));self.table.setCellWidget(index,6,source)
        window=QComboBox();window.setEditable(True);window.setMinimumWidth(130);window.setInsertPolicy(QComboBox.NoInsert)
        self.populate_window(window,row.get('window',''),row.get('hwnd',''));self.table.setCellWidget(index,7,window)
        tolerance=QSpinBox();tolerance.setRange(0,255);tolerance.setValue(int(row.get('tolerance',0)));self.table.setCellWidget(index,8,tolerance)
        for column in range(self.table.columnCount()):
            widget=self.table.cellWidget(index,column);widget.installEventFilter(self)
            if isinstance(widget,QComboBox) and widget.isEditable():widget.lineEdit().installEventFilter(self)
        self.update_count();self.table.setCurrentCell(index,1)
    def update_count(self):
        count=self.table.rowCount();self.count_label.setText('共 '+str(count)+' 项')
        self._refresh_adaptive_geometry()
        for index in range(count):self.table.cellWidget(index,0).setText('检测'+str(index+1)+':')
    def _refresh_adaptive_geometry(self):
        if not hasattr(self,'table'):return
        # Recalculate after font/padding scaling, rather than scaling a cached
        # fixed table height while leaving its row heights unchanged.
        for button in self.guard_panel.findChildren(QPushButton):
            button.ensurePolished()
            button.setMinimumHeight(max(30,button.sizeHint().height()))
        height=max(38,self.table.fontMetrics().height()+18)
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                widget=self.table.cellWidget(row,col)
                widget.ensurePolished()
                height=max(height,widget.sizeHint().height(),widget.minimumHeight())
        self.table.verticalHeader().setDefaultSectionSize(height)
        for row in range(self.table.rowCount()):self.table.setRowHeight(row,height)
        header=self.table.horizontalHeader().sizeHint().height() if self.advanced_button.isChecked() else 0
        self.table.setFixedHeight(height*min(max(self.table.rowCount(),1),5)+header+2*self.table.frameWidth()+self.table.horizontalScrollBar().sizeHint().height())
        for label in (self.guard_hint,self.status):
            width=max(1,self.guard_panel.width()-8)
            label.setMinimumHeight(max(label.fontMetrics().height(),label.heightForWidth(width)))
        panel_layout=self.guard_panel.layout();panel_layout.invalidate()
        width=max(1,self.guard_panel.width())
        required=panel_layout.totalHeightForWidth(width) if panel_layout.hasHeightForWidth() else panel_layout.sizeHint().height()
        self.guard_panel.setMinimumHeight(max(required,panel_layout.minimumSize().height()))
        self.guard_panel.updateGeometry()
    def toggle_guard(self,expanded):
        self.fold_button.setText(('▾' if expanded else '▸')+' 血条检测')
        for widget in (self.table,self.guard_hint,self.status):widget.setVisible(expanded)
        self._refresh_adaptive_geometry()
    def toggle_columns(self,expanded):
        for column in (6,8):self.table.setColumnHidden(column,not expanded)
        self.table.horizontalHeader().setVisible(expanded)
        self.update_count()
    def row_for(self,button,column):
        return next((i for i in range(self.table.rowCount()) if self.table.cellWidget(i,column) is button),None)
    def remove_rule(self):
        row=self.table.currentRow()
        if row<0:row=self.table.rowCount()-1
        if row>=0:self.table.removeRow(row)
        self.update_count()
    def populate_window(self,combo,title='',hwnd=''):
        combo.clear();combo.addItem('前台（不指定窗口）',{'title':'','hwnd':''})
        for item in self.windows:
            combo.addItem(item['窗口标题']+' · '+str(item['窗口句柄']),{'title':item['窗口标题'],'hwnd':str(item['窗口句柄'])})
        match=next((i for i in range(1,combo.count()) if (str(hwnd) and combo.itemData(i)['hwnd']==str(hwnd)) or (title and combo.itemData(i)['title']==title)),None)
        if match is not None:combo.setCurrentIndex(match)
        elif title:combo.addItem(title,{'title':title,'hwnd':str(hwnd)});combo.setCurrentIndex(combo.count()-1)
        elif hwnd:combo.addItem('窗口 #'+str(hwnd),{'title':'','hwnd':str(hwnd)});combo.setCurrentIndex(combo.count()-1)
    def refresh_windows(self):
        from anclicker.platform.background_runtime import Windows
        try:self.windows=Windows().enumerate()
        except Exception:self.windows=[]
        if not hasattr(self,'table'):return
        for i in range(self.table.rowCount()):
            row=self.rule(i);self.populate_window(self.table.cellWidget(i,7),row['window'],row['hwnd'])
    def rule(self,index):
        get=lambda col:self.table.cellWidget(index,col)
        combo=get(7);data=combo.currentData() or {};text=combo.currentText().strip()
        if combo.currentIndex()>=0 and text==combo.itemText(combo.currentIndex()):title,hwnd=data.get('title',''),data.get('hwnd','')
        else:title,hwnd=text,''
        return dict(enabled=get(0).isChecked(),pos=get(1).text().strip().replace('，',','),color=get(2).text().strip().replace('，',','),key=get(4).text().strip().lower(),source=get(6).currentText(),window=title,hwnd=hwnd,tolerance=get(8).value())
    def sync_rules(self):
        rows=[self.rule(i) for i in range(self.table.rowCount())]
        self._controls['检测规则'].setText(json.dumps(rows,ensure_ascii=False))
        self._controls['守护启用'].setCurrentText('启用' if any(row['enabled'] for row in rows) else '关闭')
    def get_draft(self):
        if self.guard_panel is not None:self.sync_rules()
        return super().get_draft()
    def update_fields(self,*args):
        super().update_fields(*args)
        point=self._controls['检测方式'].currentText()=='守护取点检测'
        stop=self._controls['操作'].currentText()=='停止监控'
        if hasattr(self.ui,'healthHint'):
            self.ui.healthHint.setText('启动检测后继续后续指令，主流程结束自动停止；持续守护请后接等待或循环。' if point else '血条选区应包含完整血条。启动监控后继续后续指令，主流程结束自动停止。')
        for key in ('检测规则','守护启用'):
            for widget in self.ui.rows.get(key,()):widget.hide()
        if point:
            for key in ('截图来源','窗口标题','窗口句柄','区域','血量颜色','容差','阈值','响应','按键','点击位置'):
                for widget in self.ui.rows[key]:widget.hide()
            for i in range(self.ui.tools.count()):
                widget=self.ui.tools.itemAt(i).widget()
                if widget:widget.hide()
        if self.guard_panel is not None:self.guard_panel.setVisible(point and not stop)
        self.test_button.setText('检测预览（不按键）' if point else '测试指令')
        self.test_button.setEnabled(not stop and not self._job)
        if hasattr(self,'common_rows'):
            self.ui.rows['监控名'][0].setText('监控名称')
            self.ui.rows['操作'][0].setText('操作')
            self.ui.rows['变量'][0].setText('检测结果变量' if point else '血量百分比变量')
            previous=self.ui.visionForm
            for _,control in self.common_rows:
                old_label=previous.labelForField(control)
                if old_label is not None:old_label.hide();old_label.deleteLater()
            while previous.count():previous.takeAt(0)
            self.ui.rootLayout.removeItem(previous);previous.deleteLater()
            form=QFormLayout();form.setFormAlignment(Qt.AlignTop);form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow);form.setRowWrapPolicy(QFormLayout.WrapLongRows)
            self.ui.visionForm=form;self.ui.rootLayout.insertLayout(0,form)
            for key,(label,control) in self.ui.rows.items():
                if key in ('连续次数','间隔','冷却'):continue
                if not control.isHidden():form.addRow(label,control)
                if key=='监控名' and point and not stop:form.addRow(self.guard_panel)
            single=self._controls['操作'].currentText()=='单次判断'
            self.timing_row.setVisible(not stop and not single)
            if not stop and not single:form.addRow(self.timing_row)
            for label,control in self.common_rows:form.addRow(label,control)
            from anclicker.ui.instruction_editors.compact_settings import compact_body
            compact_body(self._parameter_body)
    def record_rule(self,button):
        from anclicker.ui.settings_theme import apply_settings_theme
        index=self.row_for(button,5)
        if index is None:return
        dialog=RecordGuardKey(self);apply_settings_theme(dialog,self)
        if dialog.exec()==QDialog.Accepted:self.table.cellWidget(index,4).setText(dialog.value)
        dialog.deleteLater()
    def start_job(self,work,callback,hide=False):
        if self._job:return
        self.fold_button.setChecked(True);self.toggle_guard(True)
        job={'done':False,'started':time.monotonic()};self._capture_hidden=hide and self.isVisible();self._job=(job,callback);self.test_button.setEnabled(False);self.table.setEnabled(False)
        self.status.setText('正在读取画面，请稍候…')
        def run():
            try:job['result']=work()
            except Exception as error:job['error']=str(error)
            finally:job['done']=True
        worker=threading.Thread(target=run,name='guard-preview',daemon=True)
        if self._capture_hidden:
            self.hide();QTimer.singleShot(120,lambda:worker.start())
        else:worker.start()
        self.poll.start()
    def finish_job(self):
        if not self._job:return
        if not self._job[0]['done']:
            if self._capture_hidden and time.monotonic()-self._job[0]['started']>3 and not self._closing:
                self._capture_hidden=False;self.show();self.status.setText('截图仍在等待，可关闭设置窗口取消预览。')
            return
        job,callback=self._job;self._job=None;self.poll.stop()
        self.table.setEnabled(True);self.update_fields()
        if self._closing:return
        if self._capture_hidden:self._capture_hidden=False;self.show()
        if 'error' in job:self.status.setText('读取失败：'+job['error'])
        else:
            try:callback(job['result'])
            except Exception as error:self.status.setText(str(error))
    def pick_rule(self,button):
        index=self.row_for(button,3)
        if index is None:return
        row=self.rule(index)
        from anclicker.domain.instructions import ExecutionContext
        from anclicker.platform.vision_tools.runtime import window_handle,capture
        from anclicker.execution import actions
        def grab():
            if row['source']=='窗口':
                import win32gui
                p={'窗口标题':row['window'],'窗口句柄':row['hwnd'],'截图来源':'窗口'}
                hwnd=window_handle(p);w,h=win32gui.GetClientRect(hwnd)[2:];p['区域']=f'0,0,{w},{h}'
                frame,_,_=capture(p,ExecutionContext())
                from PIL import Image
                return Image.fromarray(frame[:,:,::-1]),(0,0)
            from PIL import ImageGrab
            import ctypes
            image=ImageGrab.grab(all_screens=True)
            return image,(ctypes.windll.user32.GetSystemMetrics(76),ctypes.windll.user32.GetSystemMetrics(77))
        def picked(packet):
            image,origin=packet
            from anclicker.ui.instruction_editors.guard_color_picker import GuardColorPicker
            from anclicker.ui.settings_theme import apply_settings_theme
            dialog=GuardColorPicker(image,'point',self);dialog.setWindowTitle('血条检测：取点取色');apply_settings_theme(dialog,self)
            accepted=dialog.exec()==QDialog.Accepted
            if self._closing:
                dialog.deleteLater();return
            if accepted:
                result=dialog.canvas.result()
                current=self.row_for(button,3)
                if current is not None:
                    point=(result.point[0]+origin[0],result.point[1]+origin[1])
                    self.table.cellWidget(current,1).setText(','.join(map(str,point)))
                    self.table.cellWidget(current,2).setText(','.join(map(str,result.color)))
            dialog.deleteLater();self.status.setText('取点完成；勾选检测项并设置触发按键后保存。')
        self.start_job(grab,picked,hide=row['source']=='屏幕')
    def _test_if_valid(self):
        if self._controls['检测方式'].currentText()!='守护取点检测':return super()._test_if_valid()
        try:p=self.get_draft().parameters
        except Exception as error:self.status.setText(str(error));return
        from anclicker.domain.instructions import ExecutionContext
        from anclicker.platform.vision_tools.guard_health import preview
        context=ExecutionContext(services=getattr(self.context,'services',{}))
        def done(results):
            self.status.setText('；'.join('检测 '+key+'：RGB '+','.join(map(str,value['颜色']))+('，将触发' if value['触发'] else '，正常') for key,value in results.items()) or '没有启用检测项')
        self.start_job(lambda:preview(p,context,trigger=False),done)
    def eventFilter(self,watched,event):
        if event.type() in (QEvent.FocusIn,QEvent.MouseButtonPress) and hasattr(self,'table'):
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    widget=self.table.cellWidget(row,col)
                    if widget and (widget is watched or widget.isAncestorOf(watched)):
                        if self.table.currentRow()!=row:self.table.setCurrentCell(row,col)
                        return super().eventFilter(watched,event)
        return super().eventFilter(watched,event)
    def _shutdown(self,*args):
        self._closing=True
        if hasattr(self,'poll'):self.poll.stop()
        for dialog in self.findChildren(QDialog):dialog.reject()
    def done(self,result):
        self._shutdown();super().done(result)
    def closeEvent(self,event):
        self._shutdown();super().closeEvent(event)
    def close(self):
        self._shutdown();return super().close()
