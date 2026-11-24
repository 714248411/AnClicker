"""Non-blocking, bounded image previews for instruction table cells."""
from collections import OrderedDict
import json
import re
from time import monotonic
from anclicker.platform.qt_compat.QtCore import QObject,Signal,QRunnable,QThreadPool,Qt,QRect,QSize
from anclicker.platform.qt_compat.QtGui import QImageReader,QImage
from anclicker.platform.image_paths import IMAGE_KEYS,map_background_images,resolve_image_reference

THUMBNAIL_ROLE=int(Qt.UserRole)+18
VARIABLE=re.compile(r'\$\{|\{\{|☾')

def image_references(type_id,parameters):
    """Read image inputs only; never interpret screenshot output paths as inputs."""
    found=[]
    def add(value):
        if isinstance(value,(list,tuple)):
            for item in value:add(item)
        elif isinstance(value,str):
            parts=re.split(r'[\n;；、]',value) if type_id=='多图点击' else value.splitlines()
            found.extend(part.strip() for part in parts if part.strip())
        return value
    for key in IMAGE_KEYS:add(parameters.get(key))
    if type_id.startswith('后台'):
        try:
            values=parameters.get('参数',{})
            if isinstance(values,str):values=json.loads(values)
            if isinstance(values,dict):
                method=str(parameters.get('接口','')).rsplit(' · ',1)[-1]
                map_background_images(method,values,add)
        except (ValueError,TypeError):pass
    return tuple(dict.fromkeys(found))

class _Result(QObject):
    ready=Signal(object,object)

class _Load(QRunnable):
    def __init__(self,key,signal):
        super().__init__();self.key=key;self.signal=signal
    def run(self):
        refs,project,folders=self.key
        result=QImage()
        for ref in refs:
            if VARIABLE.search(ref):continue
            try:
                path=resolve_image_reference(ref,project_path=project or None,resource_folders=folders)
                reader=QImageReader(path);reader.setAutoTransform(True)
                size=reader.size()
                if not size.isValid() or size.width()*size.height()>80_000_000:continue
                reader.setScaledSize(size.scaled(QSize(512,128),Qt.KeepAspectRatio))
                result=reader.read()
                if not result.isNull():break
            except (ValueError,OSError,RuntimeError):continue
        try:self.signal.ready.emit(self.key,result)
        except RuntimeError:pass  # table was closed while decoding

class ThumbnailCache(QObject):
    def __init__(self,table, repaint=None):
        super().__init__(table);self.table=table;self.repaint=repaint;self.entries=OrderedDict();self.pending=set()
        self.signal=_Result(self);self.signal.ready.connect(self._ready)
        self.pool=QThreadPool.globalInstance()
    def image(self,key):
        if not key:return None
        key=(tuple(key[0]),key[1],tuple(key[2]))
        entry=self.entries.get(key)
        if entry:self.entries.move_to_end(key)
        if (not entry or monotonic()>entry[1]) and key not in self.pending and len(self.pending)<64:
            self.pending.add(key);self.pool.start(_Load(key,self.signal))
        return entry[0] if entry else None
    def _ready(self,key,image):
        self.pending.discard(key)
        self.entries[key]=(image,monotonic()+(10 if image.isNull() else 3))
        self.entries.move_to_end(key)
        while len(self.entries)>256:self.entries.popitem(last=False)
        if self.repaint is not None:self.repaint()
        else:self.table.viewport().update()

def thumbnail_layout(rect,font_metrics,text,image,count=1):
    """Use only space left after the label; never enlarge the row or crop."""
    h=max(0,rect.height()-2)
    label=font_metrics.elidedText(text,Qt.ElideRight,max(0,rect.width()-10))
    x=rect.left()+5+font_metrics.horizontalAdvance(label)+5
    available=max(0,rect.right()-x-4)
    badge=font_metrics.horizontalAdvance('+'+str(count-1))+5 if count>1 else 0
    if available < badge+8:badge=0
    available=max(0,available-badge)
    if image is not None and not image.isNull():
        fitted=image.size().scaled(QSize(available,h),Qt.KeepAspectRatio)
        w,h=fitted.width(),fitted.height()
    else:
        w=h=min(available,h)
    return label,QRect(x,rect.top()+(rect.height()-h)//2,w,h),badge
