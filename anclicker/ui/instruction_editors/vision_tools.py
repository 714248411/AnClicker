"""Theme-aware editors for standalone offline vision instructions."""
from pathlib import Path
from anclicker.ui.instruction_editors.editor import SchemaInstructionEditor
from anclicker.platform.qt_compat.QtWidgets import (QVBoxLayout,QHBoxLayout,QFormLayout,QLabel,QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QPushButton,QDialogButtonBox,QFileDialog,QMessageBox,QDialog,QInputDialog,QApplication)
from anclicker.platform.qt_compat.QtCore import Qt,QTimer
from anclicker.platform.qt_compat.QtGui import QPixmap

def order_secondary_tools(ui):
    widgets=[]
    while ui.secondaryTools.count():
        item=ui.secondaryTools.takeAt(0)
        if item.widget():widgets.append(item.widget())
    order={'识图预览（不点击）':0,'字库查看':1,'选择字库目录':2}
    for widget in sorted(widgets,key=lambda w:order.get(w.text(),3)):ui.secondaryTools.addWidget(widget)

class VisionUi:
    def setupUi(self,dialog):
        self.rootLayout=QVBoxLayout(dialog)
        form=QFormLayout();self.visionForm=form;self.rootLayout.addLayout(form)
        self.rows={}
        for index,field in enumerate(dialog.FIELDS):
            if field.kind=='choice':
                control=QComboBox();control.addItems(field.choices);control.setCurrentText(field.default)
            elif field.kind in ('int','float'):
                control=QSpinBox() if field.kind=='int' else QDoubleSpinBox()
                control.setRange(field.minimum,field.maximum);control.setValue(field.default)
            else:
                control=QLineEdit(str(field.default))
            control.setObjectName('parameter_'+str(index));setattr(self,'parameter_'+str(index),control)
            label=QLabel(field.label);form.addRow(label,control);self.rows[field.key]=(label,control)
        if getattr(dialog,'tool_mode',False):
            self.status=QLabel('框选文字、填写对应文字后保存到字库，供找字使用。');self.status.setWordWrap(True)
            self.rootLayout.addWidget(self.status)
            self.tools=QHBoxLayout();self.rootLayout.addLayout(self.tools)
            self.secondaryTools=QHBoxLayout();self.rootLayout.addLayout(self.secondaryTools)
            self.footerLayout=QHBoxLayout();self.rootLayout.addLayout(self.footerLayout)
            self.saveGlyphButton=QPushButton('保存到字库');self.closeToolButton=QPushButton('关闭')
            self.footerLayout.addStretch();self.footerLayout.addWidget(self.saveGlyphButton);self.footerLayout.addWidget(self.closeToolButton)
            return
        self.repeatSpinBox=QSpinBox();self.repeatSpinBox.setRange(1,999999);self.repeatSpinBox.setValue(1)
        self.errorPolicyComboBox=QComboBox();self.errorPolicyComboBox.addItems(['提示异常并暂停','自动跳过','终止任务'])
        self.noteEdit=QLineEdit();form.addRow('重复次数',self.repeatSpinBox);form.addRow('异常处理',self.errorPolicyComboBox);form.addRow('备注',self.noteEdit)
        if dialog.TYPE_ID=='多线程血量判断':
            hint=QLabel('启动监控后继续后续指令；任务结束自动停止。持续监控请后接等待或循环。血条选区应只包含完整血条。');self.healthHint=hint
            hint.setWordWrap(True);self.rootLayout.addWidget(hint)
        elif dialog.TYPE_ID=='A星寻路':
            hint=QLabel('按亮度识别可通行区域：白色可走、黑色障碍。先确认地图与阈值，再生成路线；结果保存为坐标变量和预览图片。')
            hint.setWordWrap(True);self.rootLayout.addWidget(hint)
        self.tools=QHBoxLayout();self.rootLayout.addLayout(self.tools)
        self.secondaryTools=QHBoxLayout();self.rootLayout.addLayout(self.secondaryTools)
        self.footerLayout=QHBoxLayout();self.rootLayout.addLayout(self.footerLayout)
        self.testButton=QPushButton('测试指令');self.footerLayout.addWidget(self.testButton);self.footerLayout.addStretch()
        self.buttonBox=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);self.footerLayout.addWidget(self.buttonBox)

class VisionEditor(SchemaInstructionEditor):
    UI_CLASS=VisionUi
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        def button(text,callback):
            widget=QPushButton(text);widget.clicked.connect(lambda: self.guarded(callback));(self.ui.secondaryTools if text in ('选择字库目录','字库查看','识图预览（不点击）') else self.ui.tools).addWidget(widget)
        if '区域' in self._controls:
            button('截图框选',self.select_region)
            button('选择窗口',self.select_window)
        if self.TYPE_ID=='多线程血量判断':button('截图取色/坐标',self.pick_color)
        if self.TYPE_ID in ('制作字库','字库点击'):button('选择字库目录',self.select_library)
        if self.TYPE_ID=='字库点击':
            button('制作字库',lambda: open_glyph_tool(self,self.context,self.parameters()))
            button('字库查看',self.manage_library)
            button('识图预览（不点击）',self.preview_glyphs)
            button('吸取优先色',self.pick_glyph_color)
            button('选择优先色',self.choose_glyph_color)
        if self.TYPE_ID=='A星寻路':
            button('选择地图',self.select_map);button('小地图预览/设置起终点',self.preview_map);button('预览路线',self.preview_saved)
        if self.TYPE_ID=='小地图拼接制作大地图':button('预览已保存地图',self.preview_saved)
        for name in ('截图来源','响应','操作'):
            if name in self._controls:self._controls[name].currentTextChanged.connect(self.update_fields)
        order_secondary_tools(self.ui)
        self.update_fields()
        if '字库目录' in self._controls:self.set_library_hint()
        if '优先颜色' in self._controls:
            self._controls['优先颜色'].textChanged.connect(lambda:self.normalize_priority_field(False))
            self._controls['优先颜色'].editingFinished.connect(lambda:self.normalize_priority_field(True))
            self.normalize_priority_field(True)
    def normalize_priority_field(self,complete=False):
        control=self._controls['优先颜色'];text=control.text();value=text.replace('；',';').replace('，',',')
        if complete:
            from anclicker.platform.vision_tools.glyph_colors import normalize_priorities
            try:value=normalize_priorities(value)
            except ValueError:return
        if value!=text:
            cursor=control.cursorPosition();control.setText(value);control.setCursorPosition(min(cursor,len(value)))
    def set_library_hint(self):
        from anclicker.platform.vision_tools.runtime import data_path
        from anclicker.domain.instructions import ExecutionContext
        path=str(data_path('',self.context or ExecutionContext(),'glyphs'))
        self._controls['字库目录'].setPlaceholderText('自动使用：'+path)
        self._controls['字库目录'].setToolTip('留空自动使用默认字库目录：'+path)
    def guarded(self,callback):
        try:callback()
        except Exception as error:QMessageBox.warning(self,'操作未完成',str(error))
    def update_fields(self,*args):
        def show(key,visible):
            for widget in self.ui.rows.get(key,()):widget.setVisible(visible)
        show('优先色配置',False)
        window=self._controls.get('截图来源')
        for key in ('窗口标题','窗口句柄'):show(key,window is not None and window.currentText()=='窗口')
        if self.TYPE_ID=='多线程血量判断':
            stop=self._controls['操作'].currentText()=='停止监控'
            for key in self._controls:
                if key not in ('操作','监控名'):show(key,not stop)
            for index in range(self.ui.tools.count()):
                widget=self.ui.tools.itemAt(index).widget()
                if widget: widget.setVisible(not stop)
            if not stop:
                single=self._controls['操作'].currentText()=='单次判断'
                for key in ('连续次数','间隔','冷却'):show(key,not single)
                for key in ('窗口标题','窗口句柄'):show(key,window.currentText()=='窗口')
                mouse=self._controls['响应'].currentText()=='鼠标点击'
                show('按键',not mouse);show('点击位置',mouse)
    def _validate_parameters(self,p):
        from anclicker.platform.vision_tools.runtime import validate
        validated=validate(self.TYPE_ID,p)
        if '优先颜色' in validated:p['优先颜色']=validated['优先颜色']
    def parameters(self):return {key:self._control_value(control) for key,control in self._controls.items()}
    def source_image(self):
        from PIL import Image
        import numpy as np
        from anclicker.execution import actions
        p=self.parameters()
        if p.get('截图来源')=='窗口':
            from anclicker.platform.vision_tools.runtime import window_handle,capture
            from anclicker.domain.instructions import ExecutionContext
            import win32gui
            hwnd=window_handle(p);w,h=win32gui.GetClientRect(hwnd)[2:];p['区域']=f'0,0,{w},{h}'
            image,_,_=capture(p,ExecutionContext());return Image.fromarray(image[:,:,::-1])
        visible=self.isVisible()
        try:
            if visible:self.hide();QApplication.processEvents()
            return actions.pyautogui_module().screenshot()
        finally:
            if visible:self.show()
    def selection(self,mode):
        from anclicker.platform.background_capture import BackgroundCaptureDialog
        from anclicker.ui.settings_theme import apply_settings_theme
        image=self.source_image();dialog=BackgroundCaptureDialog(image,mode,self)
        apply_settings_theme(dialog,self)
        return dialog.canvas.result() if dialog.exec()==QDialog.Accepted else None
    def select_window(self):
        from anclicker.platform.background_runtime import Windows
        windows=Windows().enumerate()
        if not windows:raise ValueError('没有可用窗口')
        labels=[f"{item['窗口标题']} · {item['窗口句柄']}" for item in windows]
        selected,ok=QInputDialog.getItem(self,'选择截图窗口','窗口',labels,0,False)
        if ok:
            item=windows[labels.index(selected)]
            self._controls['窗口标题'].setText(item['窗口标题'])
            self._controls['窗口句柄'].setText(item['窗口句柄'])
            self._controls['截图来源'].setCurrentText('窗口')
    def select_region(self):
        result=self.selection('region')
        if result:self._controls['区域'].setText(','.join(map(str,result.region)))
    def pick_color(self):
        result=self.selection('point')
        if result:
            self._controls['血量颜色'].setText(','.join(map(str,result.color)))
            self._controls['点击位置'].setText(','.join(map(str,result.point)))
    def select_library(self):
        from anclicker.platform.vision_tools.runtime import data_path
        from anclicker.domain.instructions import ExecutionContext
        folder=QFileDialog.getExistingDirectory(self,'选择字库目录',str(data_path('',self.context or ExecutionContext(),'glyphs')))
        if folder:self._controls['字库目录'].setText(folder)
    def pick_glyph_color(self):
        from PIL import Image
        from .glyph_color_picker import GlyphColorPicker
        from anclicker.ui.settings_theme import apply_settings_theme
        from anclicker.platform.vision_tools.glyph_colors import load_variants
        from anclicker.platform.vision_tools.runtime import data_path
        from anclicker.domain.instructions import ExecutionContext
        frozen=getattr(self,'_captured',None)
        image=Image.fromarray(frozen[:,:,::-1]) if frozen is not None else self.source_image()
        records=load_variants(data_path(self._controls['字库目录'].text(),self.context or ExecutionContext(),'glyphs'))
        multiple='录入颜色' not in self._controls
        dialog=GlyphColorPicker(image,self,multiple=multiple,records=records);apply_settings_theme(dialog,self)
        try:
            if dialog.exec()!=QDialog.Accepted or not dialog.samples:return
            self._controls['颜色模式'].setCurrentText('任意颜色')
            if multiple:
                self._controls['优先颜色'].setText(';'.join(item.get('token',item['name']) for item in dialog.samples));self._controls['颜色优先'].setCurrentText('优先颜色')
            else:
                item=dialog.samples[-1];rgb=','.join(map(str,item['rgb']));name=item['name']
                self._controls['录入颜色'].setText(rgb);self._controls['颜色名称'].setText(name)
                self.ui.status.setText(f'已吸取 {name}（{rgb}）；红色保存本名，其他颜色自动追加尾号。')
        finally:dialog.deleteLater()
    def choose_glyph_color(self):
        from anclicker.platform.vision_tools.glyph_colors import load_variants
        from anclicker.platform.vision_tools.runtime import data_path
        from anclicker.domain.instructions import ExecutionContext
        from .glyph_priority_table import GlyphPriorityTable
        from anclicker.ui.settings_theme import apply_settings_theme
        records=load_variants(data_path(self._controls['字库目录'].text(),self.context or ExecutionContext(),'glyphs'))
        dialog=GlyphPriorityTable(self._controls['优先颜色'].text(),records,self._controls['优先色配置'].text(),self._controls['颜色容差'].value(),self)
        apply_settings_theme(dialog,self)
        try:
            if dialog.exec()!=QDialog.Accepted:return
            self._controls['优先颜色'].setText(dialog.value);self._controls['优先色配置'].setText(dialog.config)
            self._controls['颜色优先'].setCurrentText('优先颜色');self._controls['颜色模式'].setCurrentText('任意颜色')
        finally:dialog.deleteLater()
    def manage_library(self):
        from anclicker.platform.vision_tools.runtime import data_path
        from anclicker.domain.instructions import ExecutionContext
        from .glyph_library_manager import GlyphLibraryManager
        GlyphLibraryManager(data_path(self._controls['字库目录'].text(),self.context or ExecutionContext(),'glyphs'),self).exec()
    def preview_glyphs(self):
        from anclicker.platform.vision_tools.runtime import validate,capture,find_glyphs
        from anclicker.domain.instructions import ExecutionContext
        from anclicker.platform.background_capture import BackgroundCaptureDialog
        from anclicker.ui.settings_theme import apply_settings_theme
        from PIL import Image
        import cv2
        context=self.context or ExecutionContext();p=validate('字库点击',self.parameters())
        visible=self.isVisible()
        try:
            if visible:self.hide();QApplication.processEvents()
            frame,offset,hwnd=capture(p,context)
        finally:
            if visible:self.show()
        matches=find_glyphs(frame,p,context);image=frame.copy()
        from anclicker.instructions.common import actions
        dx,dy=actions.point(p['偏移'])
        for text,score,box in matches:
            x0,y0,x1,y1=map(int,box);cv2.rectangle(image,(x0,y0),(x1,y1),(0,200,0),2)
            cv2.drawMarker(image,(int((x0+x1)/2+dx),int((y0+y1)/2+dy)),(0,160,255),cv2.MARKER_CROSS,12,2)
            cv2.putText(image,f'{score:.2f}',(x0,max(12,y0-4)),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,180,0),1)
        dialog=BackgroundCaptureDialog(Image.fromarray(image[:,:,::-1]),'point',self)
        dialog.setWindowTitle(f'识别预览：匹配 {len(matches)} 处（不执行点击）')
        labels=dialog.findChildren(QLabel)
        if labels:labels[0].setText('绿色框为识别文字，橙色十字为偏移后的点击落点；执行时选择第一个匹配。')
        dialog.status.setText('；'.join(f'{text}：{score:.1%}' for text,score,box in matches[:10]) or '未匹配到文字，请检查字库样本、字色和相似度。')
        apply_settings_theme(dialog,self);dialog.exec()
    def select_map(self):
        path,_=QFileDialog.getOpenFileName(self,'选择地图','','图片 (*.png *.jpg *.bmp)')
        if path:self._controls['地图路径'].setText(path)
    def preview_map(self):
        from PIL import Image
        from anclicker.platform.vision_tools.runtime import data_path
        from anclicker.domain.instructions import ExecutionContext
        from anclicker.platform.background_capture import BackgroundCaptureDialog
        from anclicker.ui.settings_theme import apply_settings_theme
        image=Image.open(data_path(self._controls['地图路径'].text(),self.context or ExecutionContext())).convert('RGB')
        for field in ('起始坐标','终点坐标'):
            dialog=BackgroundCaptureDialog(image,'point',self);dialog.setWindowTitle('小地图预览：选择'+field);apply_settings_theme(dialog,self)
            if dialog.exec()!=QDialog.Accepted:return
            self._controls[field].setText(','.join(map(str,dialog.canvas.result().point)))
    def preview_saved(self):
        from PIL import Image
        from anclicker.platform.vision_tools.runtime import data_path
        from anclicker.domain.instructions import ExecutionContext
        from anclicker.platform.background_capture import BackgroundCaptureDialog
        from anclicker.ui.settings_theme import apply_settings_theme
        image=Image.open(data_path(self._controls['保存路径'].text(),self.context or ExecutionContext())).convert('RGB')
        dialog=BackgroundCaptureDialog(image,'point',self);dialog.setWindowTitle('已保存地图预览');apply_settings_theme(dialog,self);dialog.exec()


class GlyphLibraryTool(QDialog):
    """A resource authoring tool: no draft, test signal, or graph operation."""
    TYPE_ID='制作字库'
    tool_mode=True
    from anclicker.domain.instruction_fields.vision_tools import fields_for as _fields
    FIELDS=_fields(TYPE_ID)
    parameters=VisionEditor.parameters
    guarded=VisionEditor.guarded
    source_image=VisionEditor.source_image
    selection=VisionEditor.selection
    manage_library=VisionEditor.manage_library
    pick_glyph_color=VisionEditor.pick_glyph_color
    select_window=VisionEditor.select_window
    select_library=VisionEditor.select_library
    update_fields=VisionEditor.update_fields
    set_library_hint=VisionEditor.set_library_hint
    _control_value=staticmethod(SchemaInstructionEditor._control_value)
    def __init__(self,parent=None,context=None,parameters=None):
        super().__init__(parent)
        from anclicker.domain.instructions import ExecutionContext
        self.setWindowTitle('制作字库')
        self.context=ExecutionContext(services=getattr(context,'services',{}),
            variables=dict(getattr(context,'variables',{})),metadata=dict(getattr(context,'metadata',{})),runtime=getattr(context,'runtime',None))
        self.ui=VisionUi();self.ui.setupUi(self)
        self._controls={f.key:getattr(self.ui,'parameter_'+str(i)) for i,f in enumerate(self.FIELDS)}
        for key,value in (parameters or {}).items():
            if key in self._controls:SchemaInstructionEditor._set_control_value(self._controls[key],value)
        for text,callback in [('截图框选',self.select_region),('选择窗口',self.select_window),('选择字库目录',self.select_library),('字库查看',self.manage_library),('从图片取字',self.from_image),('吸取文字颜色',self.pick_glyph_color)]:
            button=QPushButton(text);button.clicked.connect(lambda checked=False,callback=callback:self.guarded(callback));(self.ui.secondaryTools if text in ('选择字库目录','字库查看') else self.ui.tools).addWidget(button)
        order_secondary_tools(self.ui)
        self._controls['截图来源'].currentTextChanged.connect(self.update_fields)
        self.ui.saveGlyphButton.clicked.connect(self.start_save)
        self.ui.closeToolButton.clicked.connect(self.reject)
        self._captured=None;self._capture_key=None;self._save_job=None
        self._save_timer=QTimer(self);self._save_timer.setInterval(40);self._save_timer.timeout.connect(self.poll_save)
        self.preview=QLabel('尚未框选文字');self.preview.setAlignment(Qt.AlignCenter);self.preview.setMinimumHeight(100)
        self.ui.rootLayout.insertWidget(1,self.preview)
        self.update_fields();self.set_library_hint();self.resize(760,460)
        from anclicker.platform.vision_tools.runtime import data_path
        data_path('',self.context,'glyphs').mkdir(parents=True,exist_ok=True)
        from anclicker.ui.settings_theme import apply_settings_theme
        host=getattr(context,'owner',None) or self.context.metadata.get('main_window') or parent
        apply_settings_theme(self,host)
    def capture_key(self):
        p=self.parameters();return tuple(str(p.get(key,'')) for key in ('截图来源','窗口标题','窗口句柄','区域'))
    def from_image(self):
        from PIL import Image
        path,_=QFileDialog.getOpenFileName(self,'选择取字图片','','图片 (*.png *.jpg *.jpeg *.bmp)')
        if path:
            with Image.open(path) as image:self.select_from_image(image.convert('RGB'),True)
    def select_region(self):
        self.select_from_image(self.source_image())
    def select_from_image(self,image,local=False):
        from .glyph_capture import GlyphCaptureDialog
        from anclicker.ui.settings_theme import apply_settings_theme
        dialog=GlyphCaptureDialog(image,self._controls['目标文字'].text(),self);apply_settings_theme(dialog,self)
        try:
            if dialog.exec()!=QDialog.Accepted:return
            result=dialog.canvas.result()
            if not result:return
            self.remember_capture(image,result.region,local)
            self._controls['目标文字'].setText(dialog.textEdit.text().strip())
        finally:dialog.deleteLater()
    def remember_capture(self,image,region,local=False):
        import numpy as np
        from anclicker.platform.qt_compat.QtGui import QImage
        x,y,w,h=map(int,region);crop=image.crop((x,y,x+w,y+h)).convert('RGB')
        if local:self._controls['截图来源'].setCurrentText('屏幕')
        self._controls['区域'].setText(','.join(map(str,(x,y,w,h))))
        self._captured=np.asarray(crop)[:,:,::-1].copy();self._capture_key=self.capture_key()
        rgb=crop.tobytes();qimage=QImage(rgb,w,h,w*3,QImage.Format_RGB888).copy()
        self.preview.setPixmap(QPixmap.fromImage(qimage).scaled(680,140,Qt.KeepAspectRatio,Qt.FastTransformation))
        self.ui.status.setText('已固定框选画面；保存使用此预览。更换来源或区域后请重新框选。')
    def start_save(self):
        """UI entry: snapshot widgets now, perform image processing and I/O off-thread."""
        if self._save_job is not None:return
        try:
            from anclicker.platform.vision_tools.runtime import validate,execute
            from anclicker.domain.instructions import ExecutionContext
            import threading
            if self._captured is None:raise ValueError('请先点击“截图框选”或“从图片取字”，确认预览后再保存。')
            if self._capture_key!=self.capture_key():raise ValueError('截图来源或区域已变化，请重新框选后保存。')
            parameters=validate('制作字库',self.parameters())
            frame=self._captured.copy()
            context=ExecutionContext(services=dict(self.context.services),variables=dict(self.context.variables),metadata=dict(self.context.metadata),runtime=self.context.runtime)
            context.services['离线视觉截图']=lambda p:(frame,(0,0),None)
            job={'done':False,'count':None,'error':None}
            def work():
                try:
                    job['count']=execute('制作字库',parameters,context);job['alias']=context.metadata.get('glyph_saved_alias','')
                except Exception as error:job['error']=str(error)
                finally:job['done']=True
            self._save_job=job;self.set_save_busy(True)
            self.ui.status.setText('正在切字并保存字库，请稍候；界面仍可操作，关闭窗口后保存会在后台完成。')
            threading.Thread(target=work,name='glyph-library-save',daemon=True).start()
            self._save_timer.start()
        except Exception as error:
            self._save_job=None;self.set_save_busy(False);self.ui.status.setText('未保存：'+str(error))
    def set_save_busy(self,busy):
        self.ui.saveGlyphButton.setEnabled(not busy)
        self.ui.saveGlyphButton.setText('正在保存…' if busy else '保存到字库')
        for control in self._controls.values():control.setEnabled(not busy)
        for row in (self.ui.tools,self.ui.secondaryTools):
            for index in range(row.count()):
                widget=row.itemAt(index).widget()
                if widget:widget.setEnabled(not busy)
    def poll_save(self):
        job=self._save_job
        if job is None or not job['done']:return
        self._save_timer.stop();self._save_job=None;self.set_save_busy(False)
        if job['error']:self.ui.status.setText('保存失败：'+job['error'])
        else:self.ui.status.setText(f"已保存 {job['count']} 个字到字库；颜色版本：{job.get('alias','')}。")
    def done(self,result):
        self._save_timer.stop()
        # Close owned modal pickers before releasing the standalone tool.
        for dialog in self.findChildren(QDialog):
            if dialog.isVisible():dialog.reject()
        super().done(result)
    def save_glyphs(self):
        """Synchronous integration helper; UI uses start_save, never this method."""
        from anclicker.platform.vision_tools.runtime import execute
        visible=self.isVisible()
        self.ui.saveGlyphButton.setEnabled(False)
        try:
            if visible:self.hide();QApplication.processEvents()
            context=self.context
            if self._captured is not None:
                if self._capture_key!=self.capture_key():raise ValueError('截图来源或区域已变化，请重新框选后保存')
                from anclicker.domain.instructions import ExecutionContext
                context=ExecutionContext(services=dict(self.context.services),variables=self.context.variables,metadata=self.context.metadata)
                context.services['离线视觉截图']=lambda p:(self._captured.copy(),(0,0),None)
            count=execute('制作字库',self.parameters(),context)
            self.ui.status.setText(f'已保存 {count} 个字到字库；颜色版本：{context.metadata.get("glyph_saved_alias","")}。')
        finally:
            if visible:self.show()
            self.ui.saveGlyphButton.setEnabled(True)

def open_glyph_tool(parent=None,context=None,parameters=None):
    # Never nest exec() inside the palette's mouse double-click handler.
    # Keep one owned modeless resource tool, independent of flow editing.
    owner=parent or QApplication.instance()
    tool=getattr(owner,'_glyph_library_tool',None)
    if tool is not None:
        tool.showNormal();tool.raise_();tool.activateWindow();return tool
    tool=GlyphLibraryTool(parent,context,parameters)
    tool.setWindowModality(Qt.NonModal)
    tool.setAttribute(Qt.WA_DeleteOnClose,True)
    owner._glyph_library_tool=tool
    def release(*args):
        if getattr(owner,'_glyph_library_tool',None) is tool:owner._glyph_library_tool=None
    tool.finished.connect(release)
    tool.destroyed.connect(release)
    tool.show();return tool
