"""Searchable window selection and a two-column arrangement settings editor."""
import json
import math
from pathlib import Path
from anclicker.domain.instructions import InstructionDraft,CommandRecord,ExecutionContext
from anclicker.domain.window_arrangement import layout_rectangles,MODE_ROWS,MODE_HINTS
from anclicker.instructions.其他.窗口排布.schema import FIELDS
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.window_arrangement import list_windows,list_screens,parse_targets,get_manager,stop_auto_fill
from anclicker.platform.qt_compat.QtCore import Qt,QTimer,QSignalBlocker,QRectF
from anclicker.platform.qt_compat.QtGui import QPainter,QColor,QPen
from anclicker.platform.qt_compat.QtWidgets import QWidget,QTreeWidgetItem,QHeaderView,QMessageBox,QAbstractSpinBox,QPushButton
from anclicker.ui.generated.instructions.其他.窗口排布.窗口排布_ui import Ui_InstructionEditor
from anclicker.ui.instruction_editors.editor import SchemaInstructionEditor
from anclicker.ui.information_dialogs import InformationDialog
from anclicker.ui.instruction_editors.test_runner import run_cancellable_test
from anclicker.app.state import application_state


class LayoutPreview(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.setMinimumHeight(130);self.setMaximumHeight(170);self.area=(0,0,1920,1080);self.rectangles=[]
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.Antialiasing)
        area=self.area
        bounds=[min([area[0],*(r[0] for r in self.rectangles)]),min([area[1],*(r[1] for r in self.rectangles)]),max([area[2],*(r[0]+r[2] for r in self.rectangles)]),max([area[3],*(r[1]+r[3] for r in self.rectangles)])]
        scale=min((self.width()-16)/max(1,bounds[2]-bounds[0]),(self.height()-16)/max(1,bounds[3]-bounds[1]))
        ox=(self.width()-(bounds[2]-bounds[0])*scale)/2;oy=(self.height()-(bounds[3]-bounds[1])*scale)/2
        painter.setPen(QPen(QColor('#64748b'),1));painter.setBrush(QColor('#e2e8f0'));painter.drawRoundedRect(QRectF(ox+(area[0]-bounds[0])*scale,oy+(area[1]-bounds[1])*scale,(area[2]-area[0])*scale,(area[3]-area[1])*scale),4,4)
        for index,(x,y,w,h) in enumerate(self.rectangles):
            rect=QRectF(ox+(x-bounds[0])*scale,oy+(y-bounds[1])*scale,w*scale,h*scale)
            painter.setPen(QPen(QColor('#2563eb'),1));painter.setBrush(QColor(147,197,253,180));painter.drawRoundedRect(rect,2,2)
            painter.setPen(QColor('#102a56'));painter.drawText(rect,Qt.AlignCenter,str(index+1))
        painter.end()


class InstructionEditor(SchemaInstructionEditor,InformationDialog):
    TYPE_ID='窗口排布';DISPLAY_NAME='窗口排布';FIELDS=FIELDS;UI_CLASS=Ui_InstructionEditor
    def __init__(self,parent=None,draft=None,context=None):
        self._origin_explicit=False;self._preview_preference=None
        super().__init__(parent=parent,draft=draft,context=context)
        self._refreshing=False;self._sort_ascending=True;self.screens=[]
        self.preview=LayoutPreview(self);self.ui.previewHolder.addWidget(self.preview)
        self.ui.previewTitle.clicked.connect(self._toggle_preview)
        self.ui.windowTree.header().setSectionResizeMode(0,QHeaderView.Stretch)
        self.ui.windowTree.header().setSectionResizeMode(1,QHeaderView.ResizeToContents)
        self.ui.searchEdit.textChanged.connect(self._filter)
        self.ui.refreshButton.clicked.connect(self.refresh_windows)
        self.ui.screenRefreshButton.clicked.connect(self.refresh_screens)
        self.ui.selectAll.clicked.connect(self._select_visible)
        self.ui.windowTree.itemChanged.connect(self._selection_changed)
        self.ui.sortButton.clicked.connect(self._sort)
        self.ui.upButton.clicked.connect(lambda:self._move(-1));self.ui.downButton.clicked.connect(lambda:self._move(1))
        self.ui.clearChecksButton.clicked.connect(self._clear_checks)
        self.ui.autoGridButton.clicked.connect(self._auto_grid)
        self.ui.originButton.clicked.connect(self._screen_origin)
        for key in ('起点X','起点Y'):self._controls[key].valueChanged.connect(self._mark_origin_explicit)
        self.ui.applyButton.clicked.connect(self._apply_now)
        self.ui.stopButton.clicked.connect(self._stop_auto_fill)
        for key,control in self._controls.items():
            if key in ('窗口列表','排布版本'):continue
            signal=getattr(control,'currentIndexChanged',None) or getattr(control,'valueChanged',None) or getattr(control,'toggled',None)
            if signal is not None:signal.connect(self._update_preview)
        self.refresh_screens();self.refresh_windows()
        self.status_timer=QTimer(self);self.status_timer.setInterval(1000);self.status_timer.timeout.connect(self._refresh_auto_status);self.status_timer.start()
        screen=self.screen();available=screen.availableGeometry() if screen else None
        self.setMinimumSize(790,500);self.resize(min(1180,available.width()-40) if available else 1180,min(820,available.height()-60) if available else 760)
        self._update_preview_visibility();self._refresh_auto_status()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'preview'):self._update_preview_visibility()
    def _toggle_preview(self):
        self._preview_preference=self.preview.isHidden()
        self._update_preview_visibility()
    def _update_preview_visibility(self):
        expanded=self._preview_preference if self._preview_preference is not None else self.height()>=760
        self.preview.setVisible(expanded)
        self.ui.previewTitle.setText('收起排布预览 ▴' if expanded else '展开排布预览 ▾')
    def _adapt_layout(self):
        # The independent scroll area keeps settings accessible while the left
        # window list and action buttons stay visible on a 768-pixel screen.
        for control in self._controls.values():control.setMinimumHeight(32)
        for spin in self.findChildren(QAbstractSpinBox):
            spin.setMinimumHeight(max(34,spin.fontMetrics().height()+16,spin.sizeHint().height()))
            if hasattr(spin,'minimum'):
                text=max((str(spin.minimum()),str(spin.maximum())),key=len)
                spin.setMinimumWidth(max(80,spin.fontMetrics().horizontalAdvance(text)+36))
        for button in self.findChildren(QPushButton):button.setMinimumHeight(max(32,button.sizeHint().height()))
    def load_draft(self,draft):
        draft=draft if isinstance(draft,InstructionDraft) else InstructionDraft.from_mapping(draft)
        self._origin_explicit=all(key in draft.parameters for key in ('起点X','起点Y'))
        super().load_draft(draft)
        self._controls['排布版本'].setValue(2)
        if hasattr(self,'preview'):self.refresh_screens();self.refresh_windows()
    def _raw_parameters(self):
        parameters={key:self._control_value(control) for key,control in self._controls.items()}
        parameters['屏幕']=self._controls['屏幕'].currentData() or parameters['屏幕']
        parameters['排布版本']=2
        return parameters
    def get_draft(self):
        draft=super().get_draft();draft.parameters['屏幕']=self._controls['屏幕'].currentData() or self._controls['屏幕'].currentText()
        draft.parameters['排布版本']=2
        targets=parse_targets(draft.parameters['窗口列表']);screen=self._screen()
        layout_rectangles(targets,screen['work'],draft.parameters)
        return draft
    def _saved_targets(self):
        try:
            result=json.loads(self._controls['窗口列表'].text());return result if isinstance(result,list) else []
        except (ValueError,TypeError):return []
    def _checked(self):
        return [self.ui.windowTree.topLevelItem(i).data(0,Qt.UserRole) for i in range(self.ui.windowTree.topLevelItemCount()) if self.ui.windowTree.topLevelItem(i).checkState(0)==Qt.Checked]
    def refresh_windows(self):
        previous=self._saved_targets();old={str(item.get('窗口句柄')):item for item in previous};self._refreshing=True
        try:
            current=list_windows();ordered=[];remaining=list(current)
            for saved in previous:
                match=next((item for item in remaining if item['窗口句柄']==saved.get('窗口句柄') and item.get('进程ID')==saved.get('进程ID')),None)
                if match is None:
                    matches=[item for item in remaining if all(not saved.get(key) or item.get(key)==saved.get(key) for key in ('窗口标题','窗口类名','进程路径'))]
                    if len(matches)==1:match=matches[0]
                if match is not None:remaining.remove(match);ordered.append((match,True,True))
                else:ordered.append((saved,True,False))
            ordered.extend((item,False,True) for item in remaining)
            self.ui.windowTree.clear()
            for item,checked,available in ordered:
                rect=item.get('rect',(0,0,0,0));title=item['窗口标题']+('（未运行）' if not available else '')
                row=QTreeWidgetItem([title,str(rect[2]-rect[0])+'×'+str(rect[3]-rect[1])]);row.setData(0,Qt.UserRole,item)
                row.setFlags(row.flags()|Qt.ItemIsUserCheckable);row.setCheckState(0,Qt.Checked if checked else Qt.Unchecked)
                row.setToolTip(0,item.get('进程路径','')+'\n类名：'+item.get('窗口类名','')+'\n句柄：'+str(item.get('窗口句柄','')))
                if not available:row.setForeground(0,QColor('#d97706'))
                self.ui.windowTree.addTopLevelItem(row)
        except Exception as error:self.ui.statusLabel.setText('刷新失败：'+str(error))
        finally:self._refreshing=False
        self._filter();self._selection_changed()
    def refresh_screens(self):
        combo=self._controls['屏幕'];selected=combo.currentData() or combo.currentText();blocker=QSignalBlocker(combo)
        try:
            self.screens=list_screens();combo.clear()
            for index,item in enumerate(self.screens):
                r=item['rect'];label=f"屏幕 {index+1}（{r[2]-r[0]}×{r[3]-r[1]}） {item['scale']}%"+('（主）' if item['primary'] else '')
                combo.addItem(label,item['id'])
            index=combo.findData(selected)
            if selected=='主屏幕':index=next((i for i,item in enumerate(self.screens) if item['primary']),0)
            if index<0 and selected not in ('主屏幕',''):
                combo.addItem('已断开的屏幕：'+str(selected),selected);index=combo.count()-1
            combo.setCurrentIndex(max(0,index))
        except Exception as error:self.ui.statusLabel.setText('读取屏幕失败：'+str(error))
        del blocker
        if not self._origin_explicit:self._screen_origin(explicit=False)
        self._update_preview()
    def _screen(self):
        value=self._controls['屏幕'].currentData() or self._controls['屏幕'].currentText()
        found=next((item for item in self.screens if item['id']==value),None)
        if found is None:raise ValueError('请选择当前可用的屏幕')
        return found
    def _filter(self,*_):
        keyword=self.ui.searchEdit.text().casefold().strip()
        for i in range(self.ui.windowTree.topLevelItemCount()):
            row=self.ui.windowTree.topLevelItem(i);item=row.data(0,Qt.UserRole);text=' '.join(str(item.get(key,'')) for key in ('窗口标题','进程路径','窗口类名')).casefold()
            row.setHidden(bool(keyword) and keyword not in text)
        self._update_count()
    def _select_visible(self,checked):
        self._refreshing=True
        for i in range(self.ui.windowTree.topLevelItemCount()):
            row=self.ui.windowTree.topLevelItem(i)
            if not row.isHidden():row.setCheckState(0,Qt.Checked if checked else Qt.Unchecked)
        self._refreshing=False;self._selection_changed()
    def _clear_checks(self):
        self._refreshing=True
        try:
            for index in range(self.ui.windowTree.topLevelItemCount()):
                self.ui.windowTree.topLevelItem(index).setCheckState(0,Qt.Unchecked)
        finally:self._refreshing=False
        self._selection_changed()

    def _selection_changed(self,*_):
        if self._refreshing:return
        self._controls['窗口列表'].setText(json.dumps(self._checked(),ensure_ascii=False,separators=(',',':')))
        self._update_count();self._update_preview()
    def _update_count(self):
        tree=self.ui.windowTree;visible=[tree.topLevelItem(i) for i in range(tree.topLevelItemCount()) if not tree.topLevelItem(i).isHidden()]
        checked=len(self._checked());self.ui.countLabel.setText(f'已选 {checked} / {tree.topLevelItemCount()}')
        with QSignalBlocker(self.ui.selectAll):self.ui.selectAll.setChecked(bool(visible) and all(item.checkState(0)==Qt.Checked for item in visible))
    def _sort(self):
        self.ui.windowTree.sortItems(0,Qt.AscendingOrder if self._sort_ascending else Qt.DescendingOrder);self._sort_ascending=not self._sort_ascending;self._selection_changed()
    def _move(self,delta):
        tree=self.ui.windowTree;item=tree.currentItem()
        if item is None:return
        index=tree.indexOfTopLevelItem(item);target=index+delta
        if 0<=target<tree.topLevelItemCount():
            tree.takeTopLevelItem(index);tree.insertTopLevelItem(target,item);tree.setCurrentItem(item);self._selection_changed()
    def _auto_grid(self):
        count=max(1,len(self._checked()))
        try:area=self._screen()['work'];ratio=(area[2]-area[0])/max(1,area[3]-area[1])
        except ValueError:ratio=1.5
        cols=min(count,max(1,math.ceil(math.sqrt(count*ratio))));self._controls['列数'].setValue(cols);self._controls['行数'].setValue(math.ceil(count/cols))
    def _mark_origin_explicit(self,*_):
        self._origin_explicit=True
    def _screen_origin(self,*_,explicit=True):
        try:area=self._screen()['work']
        except ValueError:return
        self._origin_explicit=explicit
        for key,value in (('起点X',area[0]),('起点Y',area[1])):
            with QSignalBlocker(self._controls[key]):self._controls[key].setValue(value)
        self._update_preview()
    def _update_mode_rows(self,parameters):
        mode=parameters['排布方式'];visible=set(MODE_ROWS[mode])
        if parameters['窗口大小']!='自定义':visible.discard('custom_size')
        if mode in ('对角线','水平层叠','垂直层叠') and parameters['窗口大小']=='自动':visible.discard('aspect')
        visible.update(('screen','mode','hint','auto_fill'))
        keys=tuple(key for key in self.ui.modeRows if key in visible)
        self.ui.modeHint.setText(MODE_HINTS[mode])
        if keys!=getattr(self,'_visible_mode_rows',None):
            # Hide the complete row widget: Qt 5 form layouts otherwise keep
            # empty-row spacing even when both label and field are hidden.
            for key,(label,field) in self.ui.modeRows.items():
                active=key in visible;self.ui.modeRowWidgets[key].setVisible(active)
                label.setVisible(active);field.setVisible(active)
            self.ui.parameterFormLayout.invalidate();self._visible_mode_rows=keys
    def _update_preview(self,*_):
        if not hasattr(self,'preview'):return
        parameters=self._raw_parameters();self._update_mode_rows(parameters)
        try:
            screen=self._screen();self.preview.area=screen['work'];targets=self._saved_targets()
            self.preview.rectangles=layout_rectangles(targets,screen['work'],parameters) if targets else []
            if targets:
                area=screen['work'];outside=sum(x<area[0] or y<area[1] or x+w>area[2] or y+h>area[3] for x,y,w,h in self.preview.rectangles)
                message='预览 '+str(len(targets))+' 个窗口'
                if outside:message+='；'+str(outside)+' 个超出所选屏幕，按填写的绝对坐标排布'
                self.ui.statusLabel.setText(message+'。实际尺寸可能受目标程序限制。')
            else:self.ui.statusLabel.setText('先勾选窗口，再预览或立即排布。')
        except Exception as error:self.preview.rectangles=[];self.ui.statusLabel.setText(str(error))
        self.preview.update()
    def _apply_now(self):
        parent=self.parentWidget()
        if parent is not None and hasattr(parent,'workspace') and not application_state(parent).can_edit_project():
            self.ui.statusLabel.setText('请先停止任务或录制，再立即排布。');return
        try:
            draft=self.get_draft();context=ExecutionContext()
            run_cancellable_test(get_instruction_spec(self.TYPE_ID),CommandRecord(None,self.TYPE_ID,draft.parameters,1),context,self)
            self.refresh_windows()
            result=context.variables.get('窗口排布结果',[]);limited=sum(bool(item.get('系统限制')) for item in result)
            self.ui.statusLabel.setText('已排布 '+str(len(result))+' 个窗口'+('；'+str(limited)+' 个受程序最小尺寸限制' if limited else ''))
            self._refresh_auto_status()
        except Exception as error:QMessageBox.warning(self,'窗口排布未完成',str(error))
    def _stop_auto_fill(self):
        try:stop_auto_fill();self._refresh_auto_status()
        except Exception as error:QMessageBox.warning(self,'自动补位未停止',str(error))
    def _refresh_auto_status(self):
        manager=get_manager();self.ui.autoStatus.setText(manager.status())
        self.ui.autoStatus.setVisible(manager.is_running());self.ui.stopButton.setEnabled(manager.is_running())
