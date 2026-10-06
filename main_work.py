"""Branch-capable command execution thread backed by the instruction registry."""

from __future__ import annotations

import gc
import time

from PySide6.QtCore import QMutex, QThread, QWaitCondition, Signal

from graph_repository import GraphRepository, GraphValidationError
from instructions.models import CommandRecord, ExecutionContext
from instructions.registry import get_instruction_spec
from 数据库操作 import DatabaseOperation


class CommandThread(QThread):
    """Execute a validated start-to-end flow in stable topological order."""

    send_message = Signal(str, name="send_message")
    finished_signal = Signal(str, name="finished_signal")
    send_type_and_id = Signal(str, str, name="send_type_and_id")
    cache_cleanup_requested = Signal(int, name="cache_cleanup_requested")

    CACHE_CLEANUP_INTERVAL = 25

    def __init__(self, main_window):
        super().__init__(parent=None)
        self.main_window = main_window
        self.db = DatabaseOperation()
        self.repository = GraphRepository(self.db.db_path)
        self.number = 1
        self.number_cycles = 1
        self.start_state = True
        self.suspended = False
        self.run_mode: tuple[str, int] = ("全部指令", 0)
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.is_paused = False
        self._active_context: ExecutionContext | None = None
        self._stop_requested = False

    def set_run_mode(self, mode: str, info: int) -> None:
        """Set mode to 全部指令、单行指令 or 从当前行运行.

        ``info`` is always a stable command ID for the two scoped modes.
        """
        self.run_mode = (str(mode), int(info))

    def set_repeat_number(self, number: int) -> None:
        self.number_cycles = int(number)

    def prepare_for_start(self) -> None:
        """在启动一次新运行前重置可协作停止状态。"""
        if self.isRunning():
            raise RuntimeError("执行线程仍在运行")
        self.mutex.lock()
        try:
            self._stop_requested = False
            self.start_state = True
            self.is_paused = False
            self._active_context = None
        finally:
            self.mutex.unlock()

    def run(self) -> None:
        self.mutex.lock()
        try:
            self.start_state = not self._stop_requested
            self.suspended = False
            self.is_paused = False
        finally:
            self.mutex.unlock()
        if not self.start_state:
            self.finished_signal.emit("任务已终止")
            return
        try:
            commands_ = self._commands_for_mode()
        except Exception as error_:
            self.send_message.emit(f"无法开始运行：{error_}")
            self.finished_signal.emit("任务未启动")
            return

        if not commands_:
            self.send_message.emit("没有可执行的指令。")
            self.finished_signal.emit("任务完成")
            return

        variables_ = self._load_variables()
        services_ = getattr(self.main_window, "execution_services", {}) or {}
        loop_is_infinite_ = self.number_cycles == -1
        self.number = 1
        while self.start_state and (
            loop_is_infinite_ or self.number <= self.number_cycles
        ):
            context_ = ExecutionContext(
                variables=variables_,
                services=services_,
                output=lambda message_: self.send_message.emit(f"----{message_}"),
                iteration=self.number,
                metadata={"database": self.db, "main_window": self.main_window},
            )
            self.mutex.lock()
            try:
                self._active_context = context_
            finally:
                self.mutex.unlock()
            try:
                self._execute_commands(commands_, context_)
                self._persist_variables(context_.variables)
            finally:
                from instructions.common.actions import release_recorded_inputs
                release_recorded_inputs(context_)
                self.mutex.lock()
                try:
                    if self._active_context is context_:
                        self._active_context = None
                finally:
                    self.mutex.unlock()
            if not self.start_state:
                break
            self.send_message.emit("换行")
            self.send_message.emit(f"完成第{self.number}次循环")
            if self.number % self.CACHE_CLEANUP_INTERVAL == 0:
                self._release_runtime_cache()
            self.number += 1

        self._release_runtime_cache(notify=False)
        self.finished_signal.emit("任务完成" if self.start_state else "任务已终止")

    def _release_runtime_cache(self, notify: bool = True) -> None:
        """Release cyclic Python objects and ask the GUI to drop image caches."""
        gc.collect()
        if notify:
            self.cache_cleanup_requested.emit(self.number)

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

    def pause(self) -> None:
        self.mutex.lock()
        try:
            if self.start_state:
                self.is_paused = True
        finally:
            self.mutex.unlock()

    def resume(self) -> None:
        self.mutex.lock()
        try:
            self.is_paused = False
            self.condition.wakeAll()
        finally:
            self.mutex.unlock()

    def request_stop(self) -> None:
        """协作式停止线程，并确保暂停等待立即被唤醒。"""
        self.mutex.lock()
        try:
            self.start_state = False
            self._stop_requested = True
            self.is_paused = False
            if self._active_context is not None:
                self._active_context.stop_requested = True
            self.condition.wakeAll()
        finally:
            self.mutex.unlock()

    def stop_and_wait(
        self, timeout_ms: int = 5000, terminate_wait_ms: int = 2000
    ) -> bool:
        """
        先协作式停止并唤醒暂停等待，超时后再有界强制终止。

        强制终止只作为长时间 sleep 或外部阻塞调用的最后兜底。
        在进入该路径前，request_stop 已经清除暂停并唤醒条件变量。
        """
        context_to_release_ = self._active_context
        self.request_stop()
        if not self.isRunning():
            return True
        if self.wait(max(0, int(timeout_ms))):
            return True
        self.terminate()
        stopped_ = bool(self.wait(max(0, int(terminate_wait_ms))))
        if stopped_:
            if context_to_release_ is not None:
                from instructions.common.actions import release_recorded_inputs
                release_recorded_inputs(context_to_release_)
            # terminate() may interrupt code near a mutex operation.  The old
            # worker has exited, so replace synchronization primitives before
            # this QThread instance is reused.
            self.mutex = QMutex()
            self.condition = QWaitCondition()
            self.is_paused = False
            self._active_context = None
        return stopped_

    def check_mutex(self) -> bool:
        self.mutex.lock()
        try:
            paused_at_ = time.monotonic() if self.is_paused else None
            while self.is_paused and self.start_state:
                self.condition.wait(self.mutex)
            if paused_at_ is not None and self._active_context is not None:
                duration_ = time.monotonic() - paused_at_
                for clock_ in self._active_context.metadata.get("recorded_clocks", {}).values():
                    clock_[0] += duration_
            return self.start_state
        finally:
            self.mutex.unlock()

    def _execute_commands(
        self, commands_: list[CommandRecord], context_: ExecutionContext
    ) -> None:
        if self.run_mode[0] == "全部指令":
            self._execute_flow(self.repository.execution_snapshot(), context_)
            return
        active_nodes_: set[str] | None = None
        node_by_command_: dict[int, object] = {}
        outgoing_: dict[str, list[str]] = {}
        node_by_id_: dict[str, object] = {}
        if self.run_mode[0] == "全部指令":
            snapshot_ = self.repository.validate_graph()
            node_by_id_ = {node_.node_id: node_ for node_ in snapshot_.nodes}
            node_by_command_ = {
                int(node_.command_id): node_
                for node_ in snapshot_.nodes
                if node_.command_id is not None
            }
            outgoing_ = {node_id_: [] for node_id_ in node_by_id_}
            for edge_ in snapshot_.edges:
                outgoing_[edge_.source].append(edge_.target)
            active_nodes_ = set(outgoing_.get("start", ()))
        for command_ in commands_:
            if not self.start_state:
                return
            node_ = node_by_command_.get(int(command_.id)) if active_nodes_ is not None else None
            if active_nodes_ is not None and (node_ is None or node_.node_id not in active_nodes_):
                continue
            result_ = None
            while self.start_state:
                if not self.check_mutex():
                    return
                try:
                    result_ = self._execute_one(command_, context_)
                    self._persist_variables(context_.variables)
                    if context_.stop_requested:
                        self.send_message.emit(
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
            if active_nodes_ is not None and node_ is not None:
                targets_ = list(outgoing_.get(node_.node_id, ()))
                if command_.type_id in {"条件判断", "颜色判断", "条件循环"} and targets_:
                    targets_.sort(key=lambda target_: (node_by_id_[target_].y, node_by_id_[target_].x))
                    selected_index_ = 0 if bool(result_) else min(1, len(targets_) - 1)
                    targets_ = [targets_[selected_index_]]
                active_nodes_.update(targets_)

    def _execute_flow(self, snapshot_, context_: ExecutionContext) -> None:
        """Follow persisted links, including condition branches and loop backs."""
        node_by_id_ = {node_.node_id: node_ for node_ in snapshot_.nodes}
        command_by_id_ = {int(command_.id): command_ for command_ in snapshot_.commands}
        outgoing_: dict[str, list] = {node_id_: [] for node_id_ in node_by_id_}
        for edge_ in snapshot_.edges:
            outgoing_[edge_.source].append(edge_)
        start_edges_ = outgoing_.get("start", ())
        # IDs are persistent insertion order; graph projection can change 排序.
        insertion_nodes_ = sorted(
            (node_ for node_ in snapshot_.nodes if node_.command_id is not None),
            key=lambda node_: int(node_.command_id),
        )
        connected_ = {edge_.source for edge_ in snapshot_.edges} | {
            edge_.target for edge_ in snapshot_.edges
        }
        incoming_ = {edge_.target for edge_ in snapshot_.edges}
        roots_ = [edge_.target for edge_ in start_edges_]
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
                if not pending_:
                    fallback_ = True
                    pending_ = [node_.node_id for node_ in insertion_nodes_
                                if node_.node_id not in executed_]
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
        self.send_message.emit("换行")
        self.send_message.emit(
            f"执行ID为{command_.id}的指令：{spec_.display_name}"
        )
        self.send_type_and_id.emit(command_.type_id, str(command_.id))
        return executor_.execute(context_, command_)

    def _handle_command_error(
        self, command_: CommandRecord, error_: Exception
    ) -> str:
        from instructions.common.actions import release_recorded_inputs
        if self._active_context is not None:
            release_recorded_inputs(self._active_context)
        policy_ = command_.error_policy
        error_text_ = str(error_) or type(error_).__name__
        command_id_ = command_.id
        if policy_ == "自动跳过":
            self.send_message.emit(
                f"ID为{command_id_}的指令执行异常，已自动跳过：{error_text_}"
            )
            return "continue"

        self.db.system_prompt_tone("执行异常")
        if policy_ == "提示异常并暂停":
            import pymsgbox

            self.send_message.emit(
                f"ID为{command_id_}的指令执行异常，等待处理。"
            )
            choice_ = pymsgbox.confirm(
                text=(
                    f"ID为{command_id_}的指令执行异常！\n是否重试？"
                    f"\n\n错误类型：{error_text_}"
                ),
                title="提示",
                buttons=[
                    pymsgbox.ABORT_TEXT,
                    pymsgbox.RETRY_TEXT,
                    pymsgbox.IGNORE_TEXT,
                ],
            )
            if choice_ == pymsgbox.RETRY_TEXT:
                return "retry"
            if choice_ == pymsgbox.IGNORE_TEXT:
                return "continue"
            return "stop"

        if policy_ == "提示异常并停止":
            import pymsgbox

            self.send_message.emit(
                f"ID为{command_id_}的指令执行异常，任务已停止。"
            )
            pymsgbox.alert(
                text=f"ID为{command_id_}的指令抛出异常！\n\n错误类型：{error_text_}",
                title="提示",
                icon=pymsgbox.STOP,
            )
            return "stop"

        self.send_message.emit(
            f"ID为{command_id_}的异常处理方式“{policy_}”无效，任务已停止。"
        )
        return "stop"

    def _load_variables(self) -> dict:
        try:
            return dict(self.db.get_variable_info("dict"))
        except Exception as error_:
            self.send_message.emit(f"读取变量池失败：{error_}")
            return {}

    def _persist_variables(self, variables_: dict) -> None:
        try:
            self.db.persist_global_variables(variables_)
        except Exception as error_:
            self.send_message.emit(f"保存全局变量失败：{error_}")


__all__ = ["CommandThread", "GraphValidationError"]
