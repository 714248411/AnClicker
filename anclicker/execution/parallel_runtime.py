"""Named, cooperative branch workers owned by one main execution."""
import threading
import time
from dataclasses import replace
from anclicker.domain.instructions import ExecutionContext
from anclicker.execution.control import ExecutionControl


def branch_nodes(snapshot, entry):
    node = next((n.node_id for n in snapshot.nodes if n.command_id == int(entry)), None)
    if node is None:
        raise ValueError('多线程入口指令编号不存在：' + str(entry))
    outgoing = {}
    for edge in snapshot.edges:
        outgoing.setdefault(edge.source, []).append(edge.target)
    from anclicker.domain.flow_jumps import target_config, row_node
    ordered = sorted(snapshot.commands, key=lambda c: c.order)
    node_by_command = {n.command_id: n.node_id for n in snapshot.nodes if n.command_id is not None}
    by_node = {node_by_command[c.id]: (i,c) for i,c in enumerate(ordered)}
    seen, pending = set(), [node]
    while pending:
        current = pending.pop()
        if current in seen or current == 'end':
            continue
        if current == 'start':
            raise ValueError('子线程分支不能返回主流程开始节点')
        seen.add(current)
        pending.extend(outgoing.get(current, ()))
        index, command = by_node[current]
        prefixes = ('是', '否') if command.type_id == '变量比较' else (('',) if command.type_id == '报错跳转' else ())
        for prefix in prefixes:
            mode, row, _ = target_config(command.parameters, prefix)
            if mode == '当前项目行':
                pending.append(row_node(snapshot, row))
            elif command.type_id == '变量比较' and mode in ('继续执行', '其他项目行') and index+1 < len(ordered):
                pending.append(node_by_command[ordered[index+1].id])
    return node, seen


def prepare_flow(snapshot, context):
    context.metadata['parallel_snapshot'] = snapshot
    if context.metadata.get('parallel_worker') and snapshot is context.metadata.get('parallel_scope_snapshot'):
        context.metadata['parallel_allowed'] = context.metadata['parallel_members']
        context.metadata['parallel_reserved'] = set()
        return
    context.metadata['parallel_allowed'] = None
    from anclicker.domain.flow_comments import snapshot_disabled_ids
    disabled = snapshot_disabled_ids(snapshot)
    reserved = set(context.metadata.get('connected_reserved', ()))
    for command in snapshot.commands:
        if command.type_id != '多线程启动' or command.id in disabled or '_连线线程' in command.parameters:
            continue
        _, members = branch_nodes(snapshot, command.parameters.get('入口编号', 0))
        starts = {n.node_id for n in snapshot.nodes if n.command_id == command.id}
        if members & starts:
            raise ValueError('多线程分支包含启动指令自身，请把子分支与主流程分开连线')
        reserved.update(members)
    main_roots = {e.target for e in snapshot.edges if e.source == 'start'}
    pending, main_seen = list(main_roots), set()
    outgoing = {}
    for edge in snapshot.edges:
        outgoing.setdefault(edge.source, []).append(edge.target)
    while pending:
        current = pending.pop()
        if current in main_seen or current == 'end':
            continue
        if current in reserved:
            raise ValueError('多线程分支与主流程连线重叠，请把子分支独立连接到结束')
        main_seen.add(current)
        pending.extend(outgoing.get(current, ()))
    context.metadata['parallel_reserved'] = reserved


class BranchControl(ExecutionControl):
    def __init__(self, parent):
        self.parent = parent
        self.local_running = True
        self.local_paused = False
        super().__init__()

    @property
    def start_state(self):
        return self.local_running and self.parent.start_state and not self.parent._stop_requested

    @start_state.setter
    def start_state(self, value):
        self.local_running = bool(value)

    @property
    def is_paused(self):
        return (self.local_paused or self.parent.is_paused or self.parent.schedule_pause_requested)

    @is_paused.setter
    def is_paused(self, value):
        self.local_paused = bool(value)

    def check_mutex(self):
        started = time.monotonic()
        waited = False
        while self.start_state and self.is_paused:
            waited = True
            time.sleep(.02)
        if waited and self._active_context is not None:
            for clock in self._active_context.metadata.get('recorded_clocks', {}).values():
                clock[0] += time.monotonic() - started
        if not self.start_state and self._active_context is not None:
            self._active_context.stop_requested = True
        return self.start_state


class BranchTask:
    def __init__(self, manager, owner, context, name, snapshot, entry, repeat, members=None, connected=False):
        from anclicker.execution.engine import ExecutionEngine
        self.manager, self.name, self.snapshot, self.entry = manager, name, snapshot, entry
        self.repeat = repeat
        self.connected = connected
        self.owner_control = owner.control
        self.control = BranchControl(owner.control)
        self.engine = ExecutionEngine(owner.services, owner.repository, self.control)
        self.engine.run_unconnected = False
        # Variables are shared; input ownership, timers, monitors and errors are isolated.
        self.context = ExecutionContext(variables=context.variables, services=context.services,
            output=lambda text: context.emit('[' + name + '] ' + text), iteration=context.iteration,
            metadata={key: context.metadata[key] for key in ('project_path','project_stack','rpa_bridge','connected_thread_plans','parallel_source_snapshot') if key in context.metadata})
        if members is None:
            entry_command = next(n.command_id for n in snapshot.nodes if n.node_id == entry)
            _, members = branch_nodes(snapshot, entry_command)
        self.context.metadata.update(parallel_worker=True, parallel_manager=manager,
                                     parallel_scope_snapshot=snapshot, parallel_members=members)
        self.control._active_context = self.context
        self.engine.services = replace(owner.services, output=self.context.emit,
                                       command_started=lambda *args: None,
                                       database=getattr(context.runtime,'database',None) or owner.db)
        self.engine.db = self.engine.services.database
        from anclicker.storage.graph_repository import GraphRepository
        self.engine.repository = GraphRepository(self.engine.db.db_path)
        self.engine._prepare_context(self.context)
        self.engine._persist_variables = lambda values: None
        self.engine._handle_command_error = self.handle_error
        self.thread = threading.Thread(target=self.run, name='branch-' + name, daemon=True)

    def handle_error(self, command, error):
        self.context.emit('指令 #' + str(command.id) + ' 执行失败：' + str(error))
        if command.error_policy == '自动跳过':
            return 'continue'
        self.control.request_stop()
        return 'stop'

    def stop(self):
        self.control.request_stop()
        for monitor in list(self.context.metadata.get('vision_monitors', {}).values()):
            monitor.stop.set()

    def run(self):
        from anclicker.execution.actions import release_execution_resources
        try:
            while self.control.check_mutex():
                self.engine._execute_flow(self.snapshot, self.context, self.entry)
                self.manager.wait_connected(self.engine, self.context)
                if not self.repeat:
                    # Starting a health monitor is asynchronous; keep its owner alive.
                    while self.control.check_mutex() and any(m.thread.is_alive() for m in list(self.context.metadata.get('vision_monitors', {}).values())):
                        time.sleep(.02)
                    break
                if not self.engine._wait_interruptibly(.05, self.context):
                    break
        except Exception as error:
            self.context.emit('子线程异常：' + str(error))
        finally:
            self.stop()
            error = release_execution_resources(self.context)
            if error:
                self.context.emit('子线程资源释放失败：' + str(error))
            self.context.emit('线程已结束')


class BranchManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.tasks = {}
        self.closed = False

    def start(self, owner, context, parameters):
        name = str(parameters.get('线程名称', '')).strip()
        if not name:
            raise ValueError('请填写线程名称')
        snapshot = context.metadata.get('parallel_snapshot')
        if snapshot is None:
            snapshot = owner.repository.execution_snapshot()
        plan = context.metadata.get('connected_thread_plans', {}).get(parameters.get('_连线线程'))
        if plan is not None:
            snapshot, members = plan
            entry = None
        else:
            snapshot = context.metadata.get('parallel_source_snapshot', snapshot)
            entry, members = branch_nodes(snapshot, parameters.get('入口编号', 0))
        # Explicit end links prevent row-order fallback escaping the branch.
        from anclicker.domain.graph_models import EdgeRecord
        edges = list(snapshot.edges)
        sources = {e.source for e in edges}
        edges.extend(EdgeRecord(n, 'end') for n in members if n not in sources)
        snapshot = replace(snapshot, edges=tuple(edges))
        with self.lock:
            if self.closed:
                return
            old = self.tasks.get(name)
            if old and old.thread.is_alive():
                context.emit('线程已在运行，跳过重复启动：' + name)
                return
            if sum(t.thread.is_alive() for t in self.tasks.values()) >= 8:
                raise ValueError('同时最多运行 8 个子线程')
            if not owner.start_state or context.stop_requested:
                return
            task = BranchTask(self, owner, context, name, snapshot, entry, parameters.get('运行方式') == '循环运行',
                              members=members, connected=plan is not None)
            self.tasks[name] = task
            task.thread.start()
        context.emit('已启动线程：' + name)

    def wait_connected(self, owner, context):
        while owner.check_mutex() and not context.stop_requested:
            with self.lock:
                active = [task for task in self.tasks.values() if task.connected
                          and task.owner_control is owner.control and task.thread.is_alive()
                          and task.context.metadata.get('project_path') == context.metadata.get('project_path')]
            if not active:
                return
            if not owner._wait_interruptibly(.02, context):
                return

    def stop(self, name=None, wait=True, seal=False):
        with self.lock:
            if seal:
                self.closed = True
            tasks = list(self.tasks.values()) if name is None else ([self.tasks[name]] if name in self.tasks else [])
            for task in tasks:
                task.stop()
        if wait:
            deadline = time.monotonic() + 5
            for task in tasks:
                if task.thread is not threading.current_thread():
                    task.thread.join(max(0, deadline-time.monotonic()))
            pending = [t.name for t in tasks if t.thread is not threading.current_thread() and t.thread.is_alive()]
            if pending:
                raise RuntimeError('线程仍在退出，已禁止后续操作：' + '、'.join(pending))


def execute(kind, parameters, context):
    owner = getattr(getattr(context.runtime, 'wait', None), '__self__', None)
    if owner is None or not hasattr(owner, 'control'):
        raise ValueError('请在主流程中运行多线程指令')
    manager = context.metadata.setdefault('parallel_manager', BranchManager())
    if kind == '多线程启动':
        manager.start(owner, context, parameters)
    else:
        name = None if parameters.get('关闭范围') == '全部线程' else str(parameters.get('线程名称', '')).strip()
        if name == '':
            raise ValueError('请填写要关闭的线程名称')
        manager.stop(name)
        # A health command may also have launched directly in the main flow.
        monitors = context.metadata.get('vision_monitors', {})
        if name is None:
            from anclicker.platform.vision_tools.runtime import close_monitors
            close_monitors(context)
        elif name in monitors:
            monitor = monitors[name]
            monitor.close()
            monitors.pop(name, None)
        context.emit('已关闭线程：' + (name or '全部线程'))


def close_parallel(context):
    if not context.metadata.get('parallel_worker'):
        manager = context.metadata.get('parallel_manager')
        if manager:
            manager.stop(seal=True)
