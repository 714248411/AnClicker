"""Qt-independent command execution, flow traversal and project calls."""
from __future__ import annotations
import time
from threading import Event
from pathlib import Path
from tempfile import TemporaryDirectory
from anclicker.storage.graph_repository import GraphRepository, GraphValidationError
from anclicker.domain.instructions import CommandRecord, ExecutionContext
from anclicker.instructions.registry import get_instruction_spec
from anclicker.storage.database import DatabaseOperation
from anclicker.execution.control import ExecutionControl
from anclicker.execution.services import ExecutionServices, RuntimeDependencies

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'release_execution_resources': ('from', 'anclicker.execution.actions', ('release_execution_resources',), 0),
    'snapshot_disabled_ids': ('from', 'anclicker.domain.flow_comments', ('snapshot_disabled_ids',), 0),
    'execute_jump_flow': ('from', 'anclicker.execution.flow_jump_runtime', ('execute_jump_flow',), 0),
    'execute_control_flow': ('from', 'anclicker.execution.flow_control_runtime', ('execute_control_flow',), 0),
    'comment_successors': ('from', 'anclicker.domain.flow_comments', ('comment_successors',), 0),
    'ordered_edges': ('from', 'anclicker.execution.flow_control_runtime', ('ordered_edges',), 0),
    'load_workbook': ('from', 'openpyxl', ('load_workbook',), 0),
    'row_node': ('from', 'anclicker.domain.flow_jumps', ('row_node',), 0),
    'release_recorded_inputs': ('from', 'anclicker.execution.actions', ('release_recorded_inputs',), 0),
})



class ControlAttribute:
    """Forward one declared compatibility attribute to its owner."""
    def __init__(self, name):
        self.name = name
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return getattr(instance.control, self.name)
    def __set__(self, instance, value):
        setattr(instance.control, self.name, value)
    def __delete__(self, instance):
        if self.name in vars(instance.control):
            delattr(instance.control, self.name)

class ExecutionEngine:
    CACHE_CLEANUP_INTERVAL = 25
    CACHE_CLEANUP_SECONDS = 30.0
    CPU_SLICE_SECONDS = 0.015
    def __init__(self, services, repository=None, control=None):
        self.services = services
        self.db = services.database
        self.repository = repository or GraphRepository(self.db.db_path)
        self.control = control or ExecutionControl()
        self.number = 1
        self.number_cycles = 1
        self.suspended = False
        self.run_mode = ('全部指令', 0)
        self.run_unconnected = True
        self._persisted_values = {}

    def execute(self, snapshot, context, control=None, mode=('全部指令', 0)):
        """Execute an explicit snapshot without a Qt thread or window."""
        if control is not None:
            self.control = control
        self.run_mode = mode
        self._active_context = context
        self._prepare_context(context)
        try:
            if mode[0] == '全部指令':
                return self._execute_flow(snapshot, context)
            commands = list(snapshot.commands)
            if mode[0] == '单行指令':
                commands = [command for command in commands if command.id == mode[1]]
            elif mode[0] == '从当前行运行':
                index = next((i for i,c in enumerate(commands) if c.id == mode[1]), None)
                if index is None:
                    raise KeyError(f'指令不存在：{mode[1]}')
                commands = commands[index:]
            else:
                raise ValueError(f'不支持的运行模式：{mode[0]}')
            return self._execute_commands(commands, context, snapshot=snapshot)
        finally:
            release_execution_resources = _module_imports.load('release_execution_resources')
            try:
                error = release_execution_resources(context)
                if error is not None:
                    raise error
            finally:
                self._active_context = None

    def _prepare_context(self, context):
        context.runtime = RuntimeDependencies(self.db, self._wait_interruptibly,
                                              self._run_project, self.services.ocr_pool)
        # Compatibility for injected instruction services/extensions. Internal
        # executors use runtime; no window is ever placed in execution metadata.
        context.metadata.update(database=self.db, run_project=self._run_project,
                                wait_interruptibly=self._wait_interruptibly)

    def _notify_command(self, type_id, command_id):
        self.services.command_started(type_id, command_id)

    start_state = ControlAttribute('start_state')

    is_paused = ControlAttribute('is_paused')

    schedule_pause_requested = ControlAttribute('schedule_pause_requested')

    schedule_pause_ack = ControlAttribute('schedule_pause_ack')

    _active_context = ControlAttribute('_active_context')

    _stop_requested = ControlAttribute('_stop_requested')

    _next_cpu_yield = ControlAttribute('_next_cpu_yield')

    mutex = ControlAttribute('mutex')

    condition = ControlAttribute('condition')

    def pause(self) -> None:
        return self.control.pause()

    def resume(self) -> None:
        return self.control.resume()

    def request_stop(self) -> None:
        return self.control.request_stop()

    def pause_for_schedule(self, enabled):
        return self.control.pause_for_schedule(enabled)

    def check_mutex(self) -> bool:
        return self.control.check_mutex()

    def set_run_mode(self, mode: str, info: int) -> None:
        """Set mode to 全部指令、单行指令 or 从当前行运行.

        ``info`` is always a stable command ID for the two scoped modes.
        """
        self.run_mode = (str(mode), int(info))


    def set_repeat_number(self, number: int) -> None:
        self.number_cycles = int(number)


    def run(self) -> None:
        self._next_cpu_yield = time.thread_time() + self.CPU_SLICE_SECONDS
        self._persisted_values = {}
        self.mutex.lock()
        try:
            self.start_state = not self._stop_requested
            self.suspended = False
            self.is_paused = False
        finally:
            self.mutex.unlock()
        if not self.start_state:
            self.services.finished("任务已终止")
            return
        try:
            commands_ = self._commands_for_mode()
            variables_ = self._load_variables() if commands_ else {}
            self._persisted_values = {str(name): str(value) for name, value in variables_.items()}
        except Exception as error_:
            self.services.output(f"无法开始运行：{error_}")
            self.services.finished("任务未启动")
            return

        if not commands_:
            self.services.output("没有可执行的指令。")
            self.services.finished("任务完成")
            return

        last_cleanup_ = time.monotonic()
        services_ = self.services.command_services() or {}
        loop_is_infinite_ = self.number_cycles == -1
        self.number = 1
        while self.start_state and (
            loop_is_infinite_ or self.number <= self.number_cycles
        ):
            context_ = ExecutionContext(
                variables=variables_,
                services=services_,
                output=lambda message_: self.services.output(f"----{message_}"),
                iteration=self.number,
                runtime=RuntimeDependencies(self.db, self._wait_interruptibly, self._run_project, self.services.ocr_pool),
            )
            self.mutex.lock()
            try:
                self._active_context = context_
                context_.stop_requested = self._stop_requested
            finally:
                self.mutex.unlock()
            try:
                self._execute_commands(commands_, context_)
                self._persist_variables(context_.variables)
            except Exception as error_:
                self.services.output(f"流程执行失败：{error_}")
                self.request_stop()
            finally:
                release_execution_resources = _module_imports.load('release_execution_resources')
                cleanup_error = release_execution_resources(context_)
                if cleanup_error is not None:
                    self.services.output(f'运行资源释放失败：{cleanup_error}')
                    self.request_stop()
                self.mutex.lock()
                try:
                    if self._active_context is context_:
                        self._active_context = None
                finally:
                    self.mutex.unlock()
            if not self.start_state:
                break
            self.services.output("换行")
            self.services.output(f"完成第{self.number}次循环")
            if (self.number % self.CACHE_CLEANUP_INTERVAL == 0
                    and time.monotonic() - last_cleanup_ >= self.CACHE_CLEANUP_SECONDS):
                self._release_runtime_cache()
                last_cleanup_ = time.monotonic()
            self.number += 1

        self._release_runtime_cache(notify=False)
        self.services.finished("任务完成" if self.start_state else "任务已终止")


    def _release_runtime_cache(self, notify: bool = True) -> None:
        """Collect on the GUI thread: Python cycles can own Qt widgets."""
        self.services.cache_cleanup(self.number if notify else 0)


    def _commands_for_mode(self) -> list[CommandRecord]:
        # Defensive graph validation is required immediately before every run.
        self.repository.execution_snapshot()
        commands_ = self.repository.list_commands()
        mode_, command_id_ = self.run_mode
        if mode_ == "全部指令":
            return commands_
        if mode_ == "单行指令":
            return [command_ for command_ in commands_ if command_.id == command_id_]
        if mode_ == "从当前行运行":
            for index_, command_ in enumerate(commands_):
                if command_.id == command_id_:
                    return commands_[index_:]
            raise KeyError(f"指令不存在：{command_id_}")
        raise ValueError(f"不支持的运行模式：{mode_}")


    def _execute_commands(
        self, commands_: list[CommandRecord], context_: ExecutionContext, snapshot=None
    ) -> None:
        self._prepare_context(context_)
        root_path_ = self.db.get_setting_value('当前文件路径')
        if root_path_ and root_path_ != 'None' and 'project_path' not in context_.metadata:
            context_.metadata['project_path'] = str(Path(root_path_).resolve())
            context_.metadata['project_stack'] = [Path(root_path_).resolve()]
        if self.run_mode[0] == "全部指令":
            self._execute_flow((snapshot if snapshot is not None else self.repository.execution_snapshot()), context_)
            return
        snapshot_ = (snapshot if snapshot is not None else self.repository.execution_snapshot())
        snapshot_disabled_ids = _module_imports.load('snapshot_disabled_ids')
        disabled_ = snapshot_disabled_ids(snapshot_)
        commands_ = [command for command in commands_ if command.id not in disabled_]
        if any(command.type_id in {'报错跳转','变量比较','循环','条件循环'} for command in snapshot_.commands) and commands_:
            execute_jump_flow = _module_imports.load('execute_jump_flow')
            start_id = next(node.node_id for node in snapshot_.nodes if node.command_id == commands_[0].id)
            execute_jump_flow(self,snapshot_,context_,start_id,self.run_mode[0]=='单行指令')
            return
        for command_ in commands_:
            if not self.start_state:
                return
            result_ = None
            while self.start_state:
                if not self.check_mutex():
                    return
                try:
                    result_ = self._execute_one(command_, context_)
                    self._persist_variables(context_.variables)
                    if context_.stop_requested:
                        self.services.output(
                            f"ID为{command_.id}的指令触发了终止流程。"
                        )
                        self.request_stop()
                        return
                    break
                except Exception as error_:
                    action_ = self._handle_command_error(command_, error_)
                    if action_ == "retry":
                        continue
                    if action_ == "continue":
                        break
                    self.start_state = False
                    return


    def _execute_flow(self, snapshot_, context_: ExecutionContext, start_id=None) -> None:
        """Follow persisted links, including condition branches and loop backs."""
        if any(command.type_id in {'循环', '条件循环'} for command in snapshot_.commands):
            execute_control_flow = _module_imports.load('execute_control_flow')
            return execute_control_flow(self, snapshot_, context_, start_id)
        if start_id is not None or any(command.type_id in {'报错跳转','变量比较'} for command in snapshot_.commands):
            execute_jump_flow = _module_imports.load('execute_jump_flow')
            return execute_jump_flow(self,snapshot_,context_,start_id)
        comment_successors = _module_imports.load('comment_successors')
        commented_ = comment_successors(snapshot_)
        node_by_id_ = {node_.node_id: node_ for node_ in snapshot_.nodes}
        command_by_id_ = {int(command_.id): command_ for command_ in snapshot_.commands}
        outgoing_: dict[str, list] = {node_id_: [] for node_id_ in node_by_id_}
        for edge_ in snapshot_.edges:
            outgoing_[edge_.source].append(edge_)
        ordered_edges = _module_imports.load('ordered_edges')
        outgoing_ = {key: ordered_edges(edges, node_by_id_) for key, edges in outgoing_.items()}
        start_edges_ = outgoing_.get("start", ())
        # Persisted order includes explicit row moves from the table. Links
        # still take precedence; unlinked commands follow this editable order.
        insertion_nodes_ = sorted(
            (node_ for node_ in snapshot_.nodes if node_.command_id is not None),
            key=lambda node_: (command_by_id_[int(node_.command_id)].order, int(node_.command_id)),
        )
        connected_ = {edge_.source for edge_ in snapshot_.edges} | {
            edge_.target for edge_ in snapshot_.edges
        }
        incoming_ = {edge_.target for edge_ in snapshot_.edges}
        roots_ = [edge_.target for edge_ in start_edges_]
        run_unconnected_ = getattr(self, 'run_unconnected', True)
        if run_unconnected_:
            roots_.extend(node_.node_id for node_ in insertion_nodes_
                          if node_.node_id in connected_ and node_.node_id not in incoming_)
            roots_.extend(node_.node_id for node_ in insertion_nodes_
                          if node_.node_id in connected_
                          and node_.type_id in {"循环", "条件循环"})
        executed_ = set()
        pending_ = list(dict.fromkeys(roots_))
        current_id_ = "end"
        path_ = set()
        fallback_ = False
        loop_iterations_: dict[str, int] = {}
        steps_ = 0

        while self.start_state:
            if current_id_ == "end":
                pending_ = [item_ for item_ in pending_ if item_ not in executed_]
                if not pending_ and run_unconnected_:
                    fallback_ = True
                    pending_ = [node_.node_id for node_ in insertion_nodes_
                                if node_.node_id not in executed_ and node_.node_id not in connected_]
                if not pending_:
                    return
                current_id_ = pending_.pop(0)
                path_ = set()
            steps_ += 1
            if steps_ > 500_000:
                raise GraphValidationError("流程执行超过 500000 步，已停止以避免卡死")
            if not self.check_mutex():
                return
            node_ = node_by_id_.get(current_id_)
            if node_ is None or node_.command_id is None:
                raise GraphValidationError(f"流程指向了无效节点：{current_id_}")
            command_ = command_by_id_[int(node_.command_id)]
            if current_id_ in commented_:
                if current_id_ in path_:
                    raise GraphValidationError("注释区间跳转形成环路")
                path_.add(current_id_)
                executed_.add(current_id_)
                targets_ = commented_[current_id_]
                if not fallback_:
                    pending_[0:0] = [target for target in targets_[1:] if target != "end"]
                current_id_ = "end" if fallback_ else targets_[0]
                continue
            if current_id_ in path_:
                if command_.type_id not in {"循环", "条件循环"}:
                    raise GraphValidationError("检测到没有循环控制节点的循环连线，已停止")
                path_.clear()
            elif current_id_ in executed_ and not loop_iterations_:
                current_id_ = "end"
                continue
            path_.add(current_id_)
            executed_.add(current_id_)
            edges_ = [] if fallback_ else list(outgoing_.get(current_id_, ()))

            result_ = None
            while self.start_state:
                if not self.check_mutex():
                    return
                try:
                    result_ = self._execute_one(command_, context_)
                    self._persist_variables(context_.variables)
                    if context_.stop_requested:
                        self.request_stop()
                        return
                    break
                except Exception as error_:
                    action_ = self._handle_command_error(command_, error_)
                    if action_ == "retry":
                        continue
                    if action_ == "continue":
                        break
                    self.start_state = False
                    return

            if command_.type_id in {"条件判断", "颜色判断"}:
                wanted_kind_ = 1 if bool(result_) else 2
            elif command_.type_id in {"循环", "条件循环"}:
                mode_ = str(command_.parameters.get("方式", "次数"))
                if command_.type_id == "条件循环" or mode_ in {"条件", "cond"}:
                    wanted_kind_ = 3 if bool(result_) else 4
                else:
                    completed_ = loop_iterations_.get(current_id_, 0)
                    count_ = max(0, int(command_.parameters.get("次数", 1)))
                    if completed_ < count_:
                        loop_iterations_[current_id_] = completed_ + 1
                        wanted_kind_ = 3
                    else:
                        loop_iterations_.pop(current_id_, None)
                        wanted_kind_ = 4
            else:
                if not edges_:
                    current_id_ = "end"
                    continue
                pending_[0:0] = [edge_.target for edge_ in edges_[1:]
                                 if edge_.target != "end"]
                current_id_ = edges_[0].target
                continue

            selected_ = next((edge_ for edge_ in edges_ if edge_.kind == wanted_kind_), None)
            if selected_ is None:
                loop_iterations_.pop(current_id_, None)
                current_id_ = "end"
                continue
            current_id_ = selected_.target


    def _execute_one(
        self, command_: CommandRecord, context_: ExecutionContext
    ):
        pending_ = command_.parameters.get('_待补充参数')
        if pending_:
            self.services.output(f"跳过待补充指令 #{command_.id} {command_.type_id}：" + '、'.join(str(v) for v in pending_))
            return None
        group_ = command_.parameters.get("录制批次")
        if group_:
            offset_ = max(0.0, float(command_.parameters.get("录制时间", 0)))
            clocks_ = context_.metadata.setdefault("recorded_clocks", {})
            clock_ = clocks_.setdefault(group_, [time.monotonic(), -1.0])
            if offset_ < clock_[1]:
                clock_[0] = time.monotonic()
            clock_[1] = offset_
            while self.start_state:
                if not self.check_mutex():
                    return None
                remaining_ = clock_[0] + offset_ - time.monotonic()
                if remaining_ <= 0:
                    break
                time.sleep(min(0.05, remaining_))
            if not self.start_state:
                return None
        spec_ = get_instruction_spec(command_.type_id)
        executor_ = spec_.create_executor()
        self.services.output("换行")
        self.services.output(
            f"执行ID为{command_.id}的指令：{spec_.display_name}"
        )
        # Child IDs belong to an isolated database, not the visible root table.
        if not context_.metadata.get('child_project'):
            self.services.command_started(command_.type_id, str(command_.id))
        return executor_.execute(context_, command_)


    def _wait_interruptibly(self, seconds: float, context: ExecutionContext):
        if context.stop_requested or not self.check_mutex():
            return False
        remaining = max(0.0, float(seconds))
        while remaining > 0 and not context.stop_requested:
            if not self.check_mutex():
                return False
            started = time.monotonic()
            time.sleep(min(0.05, remaining))
            remaining -= time.monotonic() - started
        return self.start_state and not context.stop_requested


    def _run_project(self, file_path: str, context: ExecutionContext, start_row=None):
        """Call a workbook on this same stoppable worker, without changing UI data."""
        load_workbook = _module_imports.load('load_workbook')

        if context.stop_requested or not self.check_mutex():
            return
        if not file_path.strip():
            raise ValueError('未设置要运行的项目文件')
        path = Path(file_path.strip().strip('"')).expanduser()
        parent_path = context.metadata.get('project_path')
        if not path.is_absolute():
            if not parent_path:
                raise ValueError('当前项目尚未保存，请使用目标项目的完整路径')
            path = Path(parent_path).parent / path
        path = path.resolve()
        stack = context.metadata.get('project_stack', [])
        if path in stack:
            raise ValueError('项目循环调用已阻止：' + ' → '.join(p.name for p in [*stack, path]))
        if len(stack) >= 32:
            raise ValueError('项目嵌套超过 32 层，已阻止继续调用')
        if path.suffix.lower() != '.xlsx' or not path.is_file():
            raise ValueError(f'项目文件不存在或不是 .xlsx：{path}')
        with TemporaryDirectory(prefix='anclicker-project-') as directory:
            database = DatabaseOperation(str(Path(directory) / 'project.db'))
            repository = GraphRepository(database.db_path)
            workbook = load_workbook(path, data_only=False)
            try:
                repository.import_from_workbook(workbook)
            finally:
                workbook.close()
            snapshot = repository.execution_snapshot()
            if start_row is not None:
                row_node = _module_imports.load('row_node')
                start_id = row_node(snapshot,start_row)
            else:
                start_id = None
            if context.stop_requested or not self.check_mutex():
                return
            saved_runtime = context.runtime
            context.runtime = RuntimeDependencies(database, self._wait_interruptibly, self._run_project, self.services.ocr_pool)
            saved_metadata = context.metadata
            # Keep input ownership shared so emergency stop releases held keys.
            context.metadata = dict(saved_metadata, database=database,
                                    project_path=str(path), project_stack=[*stack, path],
                                    child_project=True, recorded_clocks={})
            try:
                for name, value in database.get_variable_info('dict').items():
                    context.variables.setdefault(name, value)
                context.emit(f'开始运行项目：{path}')
                self._execute_flow(snapshot, context, start_id)
                context.emit(f'项目{"已中断" if context.stop_requested or not self.start_state else "已完成"}：{path.name}')
            finally:
                # Propagate key/button tracking changes back to the calling scope.
                for key in ('recorded_keys', 'recorded_buttons', '_background_session', '_background_error'):
                    if key in context.metadata:
                        saved_metadata[key] = context.metadata[key]
                    else:
                        saved_metadata.pop(key, None)
                context.metadata = saved_metadata
                context.runtime = saved_runtime


    def _handle_command_error(
        self, command_: CommandRecord, error_: Exception
    ) -> str:
        if self._stop_requested or not self.start_state:
            return "stop"
        release_recorded_inputs = _module_imports.load('release_recorded_inputs')
        if self._active_context is not None:
            release_recorded_inputs(self._active_context)
        policy_ = command_.error_policy
        error_text_ = str(error_) or type(error_).__name__
        command_id_ = command_.id
        if policy_ == "自动跳过":
            self.services.output(
                f"ID为{command_id_}的指令执行异常，已自动跳过：{error_text_}"
            )
            return "continue"

        self.services.notify_error()
        if policy_ == "提示异常并暂停":
            self.services.output(
                f"ID为{command_id_}的指令执行异常，等待处理。"
            )
            request = dict(text=f"ID为{command_id_}的指令执行异常：\n{error_text_}",
                           event=Event(), action="stop", retry=True)
            self.services.error_requested(request)
            while self.start_state and not self._stop_requested:
                if request['event'].wait(0.05):
                    return request['action'] if not self._stop_requested else 'stop'
            return 'stop'

        if policy_ == "提示异常并停止":
            self.services.output(
                f"ID为{command_id_}的指令执行异常，任务已停止。"
            )
            self.services.error_requested(dict(
                text=f"ID为{command_id_}的指令抛出异常：\n{error_text_}",
                event=Event(), action='stop', retry=False))
            return "stop"

        self.services.output(
            f"ID为{command_id_}的异常处理方式“{policy_}”无效，任务已停止。"
        )
        return "stop"


    def _load_variables(self) -> dict:
        try:
            return dict(self.db.get_variable_info("dict"))
        except Exception as error_:
            self.services.output(f"读取变量池失败：{error_}")
            return {}


    def _persist_variables(self, variables_: dict) -> None:
        try:
            values_ = {str(name): str(value) for name, value in variables_.items()}
            changed_ = {name: value for name, value in values_.items()
                        if self._persisted_values.get(name) != value}
            if changed_:
                self.db.persist_global_variables(changed_)
                self._persisted_values.update(changed_)
        except Exception as error_:
            self.services.output(f"保存全局变量失败：{error_}")
