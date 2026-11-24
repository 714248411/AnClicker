"""Concurrent branch integration, synthetic capture and input only."""
import os,sys,tempfile,time,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import numpy as np
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.domain.graph_models import GraphSnapshot, NodeView, EdgeRecord
from anclicker.execution.engine import ExecutionEngine
from anclicker.execution.services import ExecutionServices
from anclicker.storage.database import DatabaseOperation
from anclicker.platform.vision_tools.runtime import execute as vision, close_monitors
from anclicker.instructions.registry import get_instruction_spec
from anclicker.platform.qt_compat.QtWidgets import QApplication

def until(predicate, seconds=3):
    deadline=time.monotonic()+seconds
    while not predicate() and time.monotonic()<deadline:time.sleep(.01)
    if not predicate():
        print('DIAGNOSTIC', counts, errors, logs, flush=True)
        engine.request_stop()
        raise AssertionError('timeout')

def snapshot(commands, edges):
    nodes=[NodeView('start',None,'start',None,'开始',0,0),NodeView('end',None,'end',None,'结束',0,0)]
    nodes += [NodeView(str(c.id),c.id,'instruction',c.type_id,c.type_id,0,0) for c in commands]
    return GraphSnapshot(tuple(commands),tuple(nodes),tuple(EdgeRecord(str(a),str(b),k) for a,b,k in edges))

original=ExecutionEngine._execute_one
errors=[]
counts={}
main_ready=threading.Event();main_release=threading.Event()
def execute_one(self,command,context):
    if command.type_id=='Probe':
        name=context.metadata.get('parallel_worker',False)
        counts[name]=counts.get(name,0)+1
        self._wait_interruptibly(.03,context)
        return
    if command.type_id=='FailProbe':
        raise ValueError('synthetic worker failure')
    if command.type_id=='MainWait':
        main_ready.set()
        while not main_release.is_set() and self._wait_interruptibly(.02,context):pass
        return
    return original(self,command,context)
ExecutionEngine._execute_one=execute_one
app=QApplication.instance() or QApplication([])
with tempfile.TemporaryDirectory() as folder:
    db=DatabaseOperation(str(Path(folder)/'test.db'))
    logs=[]; events=[]
    image=np.zeros((10,100,3),np.uint8);image[:,:10]=(0,0,255)
    services={'离线视觉截图':lambda p:(image.copy(),(0,0),None),'离线视觉输入':lambda *args:events.append(time.monotonic())}
    commands=[CommandRecord(1,'多线程启动',{'线程名称':'a','入口编号':10,'运行方式':'循环运行'}),
      CommandRecord(2,'多线程启动',{'线程名称':'hp','入口编号':20}),CommandRecord(3,'MainWait'),
      CommandRecord(4,'多线程关闭',{'关闭范围':'全部线程'}),CommandRecord(5,'Probe'),
      CommandRecord(10,'Probe'),CommandRecord(20,'多线程血量判断',{'区域':'0,0,100,10','连续次数':1,'间隔':.05,'冷却':.1})]
    for index,c in enumerate(commands):c.order=index
    graph=snapshot(commands,[('start',1,0),(1,2,0),(2,3,0),(3,4,0),(4,5,0),(5,'end',0),(10,'end',0),(20,'end',0)])
    engine=ExecutionEngine(ExecutionServices(db,output=logs.append))
    context=ExecutionContext(services=services,output=logs.append)
    def run():
        try:engine.execute(graph,context)
        except Exception as error:errors.append(error)
    worker=threading.Thread(target=run);worker.start()
    until(lambda:main_ready.is_set() and counts.get(True,0)>2 and len(events)>1)
    manager=context.metadata['parallel_manager']
    assert len(manager.tasks)==2
    manager.start(engine,context,commands[0].parameters)
    assert len(manager.tasks)==2
    engine.pause();time.sleep(.12)
    frozen=(counts.get(True,0),len(events));time.sleep(.2)
    assert frozen==(counts.get(True,0),len(events)), 'pause must freeze all workers'
    engine.resume();until(lambda:counts.get(True,0)>frozen[0] and len(events)>frozen[1])
    engine.pause_for_schedule(True);time.sleep(.12)
    frozen=(counts.get(True,0),len(events));time.sleep(.15)
    assert frozen==(counts.get(True,0),len(events))
    engine.pause_for_schedule(False);until(lambda:len(events)>frozen[1])
    main_release.set();worker.join(4)
    assert not worker.is_alive() and not errors, errors
    assert counts.get(False)==1, 'reserved branches ran in main flow'
    assert all(not t.thread.is_alive() for t in manager.tasks.values())
    print('PASS branch execution, duplicate start, all-worker pause/resume, schedule pause, close-all, no main duplication')
    # Stop while paused must wake every child without requiring resume.
    main_ready.clear();main_release.clear();counts.clear();events.clear()
    engine=ExecutionEngine(ExecutionServices(db,output=logs.append))
    context=ExecutionContext(services=services,output=logs.append)
    worker=threading.Thread(target=run);worker.start()
    until(lambda:main_ready.is_set() and events)
    engine.pause();time.sleep(.06);engine.request_stop();worker.join(4)
    assert not worker.is_alive() and not errors,errors
    assert all(not t.thread.is_alive() for t in context.metadata['parallel_manager'].tasks.values())
    print('PASS stop while paused joins branch and health threads')
    # A capture begun before pause/resume must not produce an action afterwards.
    entered=threading.Event();release=threading.Event();captures=[0];events.clear()
    def capture(p):
        captures[0]+=1
        if captures[0]==1:entered.set();release.wait(2)
        frame=image.copy() if captures[0]==1 else np.full_like(image,(0,0,255))
        return frame,(0,0),None
    engine=ExecutionEngine(ExecutionServices(db));context=ExecutionContext(services={'离线视觉截图':capture,'离线视觉输入':lambda *a:events.append(a)})
    engine._active_context=context;engine._prepare_context(context)
    vision('多线程血量判断',commands[-1].parameters,context)
    assert entered.wait(2)
    engine.pause();engine.resume();release.set();time.sleep(.2)
    close_monitors(context);assert not events
    print('PASS stale screenshot discarded across pause/resume')
    from anclicker.execution.parallel_runtime import execute as parallel_execute
    context.services=services
    vision('多线程血量判断',commands[-1].parameters,context)
    parallel_execute('多线程关闭',{'关闭范围':'全部线程'},context)
    assert not context.metadata.get('vision_monitors')
    print('PASS close-all includes health monitors started directly in main flow')
    from anclicker.execution.parallel_runtime import BranchManager
    engine=ExecutionEngine(ExecutionServices(db,output=logs.append))
    context=ExecutionContext(output=logs.append)
    engine._active_context=context;engine._prepare_context(context)
    manager=BranchManager();context.metadata['parallel_manager']=manager
    # Named close leaves the other worker running, and the closed name can restart.
    context.metadata['parallel_snapshot']=graph
    manager.start(engine,context,{'线程名称':'one','入口编号':10,'运行方式':'循环运行'})
    manager.start(engine,context,{'线程名称':'two','入口编号':10,'运行方式':'循环运行'})
    until(lambda:all(t.thread.is_alive() for t in manager.tasks.values()))
    manager.stop('one');assert not manager.tasks['one'].thread.is_alive() and manager.tasks['two'].thread.is_alive()
    manager.start(engine,context,{'线程名称':'one','入口编号':10,'运行方式':'循环运行'})
    assert manager.tasks['one'].thread.is_alive();manager.stop()
    print('PASS named close, other worker survives, restart same name')
    loop_commands=[CommandRecord(10,'循环',{'次数':3}),CommandRecord(11,'Probe')]
    loop_graph=snapshot(loop_commands,[('start','end',0),(10,11,3),(11,10,0),(10,'end',4)])
    context.metadata['parallel_snapshot']=loop_graph;before=counts.get(True,0)
    manager.start(engine,context,{'线程名称':'loop','入口编号':10})
    until(lambda:not manager.tasks['loop'].thread.is_alive())
    assert counts.get(True,0)==before+3
    context.metadata['parallel_snapshot']=snapshot([CommandRecord(30,'FailProbe')],[('start','end',0)])
    manager.start(engine,context,{'线程名称':'failure','入口编号':30})
    until(lambda:not manager.tasks['failure'].thread.is_alive())
    assert engine.start_state and any('synthetic worker failure' in line for line in logs)
    print('PASS real loop traversal inside branch and isolated worker error')
    # Natural main completion closes background workers without a close instruction.
    counts.clear();natural=snapshot([CommandRecord(1,'多线程启动',{'线程名称':'natural','入口编号':10,'运行方式':'循环运行'}),CommandRecord(10,'Probe')],[('start',1,0),(1,'end',0),(10,'end',0)])
    engine=ExecutionEngine(ExecutionServices(db));context=ExecutionContext()
    engine.execute(natural,context)
    assert all(not t.thread.is_alive() for t in context.metadata['parallel_manager'].tasks.values())
    print('PASS natural main completion releases all workers')
    for name in ('多线程启动','多线程关闭'):
        spec=get_instruction_spec(name);assert spec.category=='流程'
        editor=spec.create_editor(context=ExecutionContext(metadata={'database':db}))
        assert not editor.test_button.isEnabled()
        if name=='多线程关闭':
            editor._controls['关闭范围'].setCurrentText('全部线程')
            assert editor._controls['线程名称'].isHidden()
        assert editor.get_draft().type_id==name
        editor.close();editor.deleteLater()
    print('PASS flow category, editor controls and save')
ExecutionEngine._execute_one=original
print('PASS parallel runtime suite')
