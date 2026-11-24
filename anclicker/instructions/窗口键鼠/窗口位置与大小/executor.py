from anclicker.instructions.common import InstructionExecutorBase
from anclicker.platform.background_runtime import Windows
from .schema import OPERATIONS

class InstructionExecutor(InstructionExecutorBase):
    TYPE_ID = '窗口位置与大小'

    def execute_once(self, context, command):
        p = command.parameters
        op = p.get('操作',OPERATIONS[0])
        if op not in OPERATIONS: raise ValueError('未知窗口位置操作')
        if context.stop_requested: return None
        windows = (context.service('background_windows') or Windows)()
        if not isinstance(p.get('窗口'),dict) or not p['窗口'].get('窗口句柄'):
            raise ValueError('请先点选目标窗口')
        target = windows.resolve(p['窗口'])
        gui = windows.gui
        hwnd = int(target['窗口句柄'])
        windows.validate(target)
        name = str(p.get('记录名称','窗口位置记录')).strip()
        if op in OPERATIONS[3:] and not name: raise ValueError('请填写记录变量名称')
        if op == '记录位置和大小':
            record = {'窗口':dict(target),'位置状态':gui.GetWindowPlacement(hwnd),
                      '窗口范围':list(gui.GetWindowRect(hwnd)),
                      '置顶':bool(gui.GetWindowLong(hwnd,-20)&8)}
            context.set_variable(name,record)
            context.emit('已记录窗口位置和大小: '+name)
            return record
        if op == '恢复位置和大小':
            record = context.variables.get(name)
            if not isinstance(record,dict) or '位置状态' not in record:
                raise ValueError('没有窗口位置记录，请先执行记录操作: '+name)
            recorded_target = windows.resolve(record.get('窗口') or {})
            if int(recorded_target['窗口句柄']) != hwnd:
                raise ValueError('记录属于其他窗口，请选择记录时的窗口')
            placement = record['位置状态']
            if not isinstance(placement,(list,tuple)) or len(placement)!=5:
                raise ValueError('窗口位置记录格式无效')
            placement = (int(placement[0]),int(placement[1]),tuple(placement[2]),tuple(placement[3]),tuple(placement[4]))
            windows.validate(target)
            gui.SetWindowPlacement(hwnd,placement)
            gui.SetWindowPos(hwnd,-1 if record.get('置顶') else -2,0,0,0,0,19)
            context.emit('已恢复窗口位置和大小: '+name)
            return True
        def number(key,default,low,high):
            value = p.get(key,default)
            if isinstance(value,bool) or int(value)!=float(value) or not low<=int(value)<=high:
                raise ValueError(key+'超出有效范围或不是整数')
            return int(value)
        move = op != '仅调整大小'
        resize = op != '仅移动位置'
        x = number('X',0,-100000,100000) if move else 0
        y = number('Y',0,-100000,100000) if move else 0
        width = number('宽度',800,1,100000) if resize else 0
        height = number('高度',600,1,100000) if resize else 0
        if gui.IsIconic(hwnd) or gui.IsZoomed(hwnd): gui.ShowWindow(hwnd,9)
        flags = 4|16|(0 if move else 2)|(0 if resize else 1)
        gui.SetWindowPos(hwnd,0,x,y,width,height,flags)
        context.emit('窗口位置与大小: '+op+'完成')
        return list(gui.GetWindowRect(hwnd))
