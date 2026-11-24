from anclicker.instructions.窗口键鼠.窗口键鼠.executor import InstructionExecutor as BaseExecutor, ScopedContext
from anclicker.platform.background_runtime import input_context, SESSION
from anclicker.domain.instructions import CommandRecord
from anclicker.instructions.本地OCR.OCR点击识别区域.executor import InstructionExecutor as OcrExecutor

class RelativeInput:
    def __init__(self, api, windows, target):
        self.api, self.windows, self.target = api, windows, target
    def __getattr__(self, key):
        return getattr(self.api, key)
    def point(self, x, y):
        self.windows.validate(self.target)
        width, height = self.windows.size(self.target)
        if not 0 <= x < width or not 0 <= y < height:
            raise ValueError('OCR点击位置超出窗口')
        return self.windows.gui.ClientToScreen(int(self.target['窗口句柄']), (int(x),int(y)))
    def screenshot(self, region=None):
        x,y,w,h = region
        x,y = self.point(x,y)
        return self.api.screenshot(region=(x,y,w,h))
    def moveTo(self, x, y, **kwargs):
        return self.api.moveTo(*self.point(x,y), **kwargs)
    def click(self, x=None, y=None, **kwargs):
        if x is not None and y is not None:
            return self.api.click(*self.point(x,y), **kwargs)
        return self.api.click(**kwargs)

class InstructionExecutor(BaseExecutor):
    TYPE_ID = '窗口OCR点击'
    CAPTURE_ENABLED = True

    @staticmethod
    def perform(api, windows, target, parameters, context, screen=False):
        width, height = windows.size(target)
        p = dict(parameters, 区域=str((0,0,width,height)), 点击来源='重新识别',
                 动作=parameters.get('操作','左键单击'))
        scoped = ScopedContext(context)
        scoped.metadata[SESSION] = RelativeInput(api, windows, target) if screen else api
        with input_context(scoped):
            return OcrExecutor().execute_once(scoped, CommandRecord(None, 'OCR点击识别区域', p))
