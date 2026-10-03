"""Linear command execution thread backed by the instruction registry."""

from __future__ import annotations

import gc

from PySide6.QtCore import QMutex, QThread, QWaitCondition, Signal

from graph_repository import GraphRepository, GraphValidationError
from instructions.models import CommandRecord, ExecutionContext
from instructions.registry import get_instruction_spec
from 数据库操作 import DatabaseOperation


class CommandThread(QThread):
    """Execute the validated start-to-end chain in stored linear order."""

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
        self.repository.validate_graph()
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
        self.request_stop()
        if not self.isRunning():
            return True
        if self.wait(max(0, int(timeout_ms))):
            return True
        self.terminate()
        stopped_ = bool(self.wait(max(0, int(terminate_wait_ms))))
        if stopped_:
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
            while self.is_paused and self.start_state:
                self.condition.wait(self.mutex)
            return self.start_state
        finally:
            self.mutex.unlock()

    def _execute_commands(
        self, commands_: list[CommandRecord], context_: ExecutionContext
    ) -> None:
        for command_ in commands_:
            if not self.start_state:
                return
            while self.start_state:
                if not self.check_mutex():
                    return
                try:
                    self._execute_one(command_, context_)
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

    def _execute_one(
        self, command_: CommandRecord, context_: ExecutionContext
    ) -> None:
        spec_ = get_instruction_spec(command_.type_id)
        executor_ = spec_.create_executor()
        self.send_message.emit("换行")
        self.send_message.emit(
            f"执行ID为{command_.id}的指令：{spec_.display_name}"
        )
        self.send_type_and_id.emit(command_.type_id, str(command_.id))
        executor_.execute(context_, command_)

    def _handle_command_error(
        self, command_: CommandRecord, error_: Exception
    ) -> str:
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
        for name_, value_ in variables_.items():
            try:
                self.db.set_variable_value(str(name_), value_)
            except Exception as error_:
                self.send_message.emit(f"写入变量“{name_}”失败：{error_}")


__all__ = ["CommandThread", "GraphValidationError"]
