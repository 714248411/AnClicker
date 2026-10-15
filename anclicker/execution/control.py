"""Cooperative execution control implemented with Python synchronization."""
import time
from threading import RLock, Condition, Event

class _Mutex:
    def __init__(self):
        self.lock_object = RLock()
    def lock(self):
        self.lock_object.acquire()
    def unlock(self):
        self.lock_object.release()

class _WaitCondition:
    def __init__(self, mutex):
        self.condition = Condition(mutex.lock_object)
    def wait(self, mutex, timeout_ms=None):
        return self.condition.wait(None if timeout_ms is None else timeout_ms / 1000)
    def wakeAll(self):
        self.condition.notify_all()

class ExecutionControl:
    CPU_SLICE_SECONDS = 0.015
    COOPERATIVE_YIELD_MS = 2
    def __init__(self):
        self.mutex = _Mutex()
        self.condition = _WaitCondition(self.mutex)
        self.schedule_pause_ack = Event()
        self.schedule_pause_requested = False
        self._active_context = None
        self._stop_requested = False
        self.start_state = True
        self.is_paused = False
        self._next_cpu_yield = time.thread_time() + self.CPU_SLICE_SECONDS

    def reset(self):
        self.mutex.lock()
        try:
            self._stop_requested = False
            self.start_state = True
            self.is_paused = False
            self._active_context = None
        finally:
            self.mutex.unlock()

    def pause(self) -> None:
        self.mutex.lock()
        try:
            if self.start_state:
                self.is_paused = True
                if self._active_context is not None:
                    metadata = self._active_context.metadata
                    metadata['visual_input_generation'] = metadata.get('visual_input_generation', 0) + 1
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


    def pause_for_schedule(self, enabled):
        self.mutex.lock()
        try:
            self.schedule_pause_requested = bool(enabled)
            if not enabled:
                self.schedule_pause_ack.clear()
            self.condition.wakeAll()
        finally:
            self.mutex.unlock()


    def check_mutex(self) -> bool:
        self.mutex.lock()
        try:
            if self.start_state and time.thread_time() >= self._next_cpu_yield:
                self.condition.wait(self.mutex, self.COOPERATIVE_YIELD_MS)
                self._next_cpu_yield = time.thread_time() + self.CPU_SLICE_SECONDS
            metadata = self._active_context.metadata if self._active_context else {}
            # Finish held-key / mouse-drag sequences before yielding input ownership.
            safe = not metadata.get('recorded_keys') and not metadata.get('recorded_buttons')
            scheduled = self.schedule_pause_requested and safe
            paused_at_ = time.monotonic() if self.is_paused or scheduled else None
            while (self.is_paused or (self.schedule_pause_requested and safe)) and self.start_state:
                if self.schedule_pause_requested and safe:
                    self.schedule_pause_ack.set()
                self.condition.wait(self.mutex)
            self.schedule_pause_ack.clear()
            if paused_at_ is not None and self._active_context is not None:
                duration_ = time.monotonic() - paused_at_
                for clock_ in self._active_context.metadata.get("recorded_clocks", {}).values():
                    clock_[0] += duration_
            return self.start_state
        finally:
            self.mutex.unlock()
