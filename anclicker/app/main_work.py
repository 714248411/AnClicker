"""Qt thread adapter preserving the historical command-worker API."""
from __future__ import annotations
import weakref
from functools import partial, wraps
from anclicker.platform.qt_compat.QtCore import QThread, Signal
from anclicker.storage.graph_repository import GraphRepository, GraphValidationError
from anclicker.storage.database import DatabaseOperation
from anclicker.execution.engine import ExecutionEngine
from anclicker.execution.control import ExecutionControl
from anclicker.execution.services import ExecutionServices


class EngineAttribute:
    """Forward one declared compatibility attribute to its owner."""
    def __init__(self, name):
        self.name = name
    def __get__(self, instance, owner=None):
        if instance is None:
            if callable(getattr(ExecutionEngine, self.name, None)):
                @wraps(getattr(ExecutionEngine, self.name))
                def unbound(target, *args, **kwargs):
                    engine = getattr(target, 'engine', target)
                    if self.name in {'pause', 'resume', 'request_stop', 'pause_for_schedule', 'check_mutex'}:
                        return getattr(ExecutionControl, self.name)(getattr(engine, 'control', engine), *args, **kwargs)
                    return getattr(ExecutionEngine, self.name)(engine, *args, **kwargs)
                return unbound
            return self
        return getattr(instance.engine, self.name)
    def __set__(self, instance, value):
        setattr(instance.engine, self.name, value)
    def __delete__(self, instance):
        if self.name in vars(instance.engine):
            delattr(instance.engine, self.name)

class CommandThread(QThread):
    send_message = Signal(str, name='send_message')
    finished_signal = Signal(str, name='finished_signal')
    send_type_and_id = Signal(str, str, name='send_type_and_id')
    cache_cleanup_requested = Signal(int, name='cache_cleanup_requested')
    error_requested = Signal(object)
    CACHE_CLEANUP_INTERVAL = 25
    CACHE_CLEANUP_SECONDS = 30.0
    CPU_SLICE_SECONDS = 0.015
    COOPERATIVE_YIELD_MS = 2

    def __init__(self, main_window):
        super().__init__(parent=None)
        self.main_window = main_window
        db = DatabaseOperation()
        owner = weakref.ref(self)
        def emit(name, *values):
            thread = owner()
            if thread is not None:
                getattr(thread, name).emit(*values)
        def command_services():
            thread = owner()
            return getattr(thread.main_window, 'execution_services', {}) or {} if thread is not None else {}
        services = ExecutionServices(
            database=db, output=partial(emit, 'send_message'),
            command_started=partial(emit, 'send_type_and_id'),
            finished=partial(emit, 'finished_signal'),
            error_requested=partial(emit, 'error_requested'),
            cache_cleanup=partial(emit, 'cache_cleanup_requested'),
            notify_error=lambda: db.system_prompt_tone('执行异常'),
            command_services=command_services,
            ocr_pool=getattr(main_window, 'ocr_pool', None),
        )
        self.engine = ExecutionEngine(services)

    def run(self):
        if self.isRunning():
            self.setPriority(QThread.Priority.LowPriority)
        self.engine.run()

    def prepare_for_start(self):
        if self.isRunning():
            raise RuntimeError('执行线程仍在运行')
        self.engine.control.reset()

    def stop_and_wait(
        self, timeout_ms: int = 5000, terminate_wait_ms: int = 2000
    ) -> bool:
        """Bounded join for non-UI callers; never terminate a lock-owning worker."""
        self.request_stop()
        if not self.isRunning():
            return True
        return bool(self.wait(max(0, int(timeout_ms))))

    start_state = EngineAttribute('start_state')

    is_paused = EngineAttribute('is_paused')

    schedule_pause_requested = EngineAttribute('schedule_pause_requested')

    schedule_pause_ack = EngineAttribute('schedule_pause_ack')

    _active_context = EngineAttribute('_active_context')

    _notify_command = EngineAttribute('_notify_command')

    _stop_requested = EngineAttribute('_stop_requested')

    _next_cpu_yield = EngineAttribute('_next_cpu_yield')

    mutex = EngineAttribute('mutex')

    condition = EngineAttribute('condition')

    db = EngineAttribute('db')

    repository = EngineAttribute('repository')

    number = EngineAttribute('number')

    number_cycles = EngineAttribute('number_cycles')

    suspended = EngineAttribute('suspended')

    run_mode = EngineAttribute('run_mode')

    run_unconnected = EngineAttribute('run_unconnected')

    _persisted_values = EngineAttribute('_persisted_values')

    set_run_mode = EngineAttribute('set_run_mode')

    set_repeat_number = EngineAttribute('set_repeat_number')

    _release_runtime_cache = EngineAttribute('_release_runtime_cache')

    _commands_for_mode = EngineAttribute('_commands_for_mode')

    pause = EngineAttribute('pause')

    resume = EngineAttribute('resume')

    request_stop = EngineAttribute('request_stop')

    pause_for_schedule = EngineAttribute('pause_for_schedule')

    check_mutex = EngineAttribute('check_mutex')

    _execute_commands = EngineAttribute('_execute_commands')

    _execute_flow = EngineAttribute('_execute_flow')

    _execute_one = EngineAttribute('_execute_one')

    _wait_interruptibly = EngineAttribute('_wait_interruptibly')

    _run_project = EngineAttribute('_run_project')

    _handle_command_error = EngineAttribute('_handle_command_error')

    _load_variables = EngineAttribute('_load_variables')

    _persist_variables = EngineAttribute('_persist_variables')


__all__ = ["CommandThread", "GraphValidationError"]
