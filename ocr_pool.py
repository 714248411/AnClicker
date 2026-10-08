"""Application-owned, serialized OCR workers. No screenshots during warmup."""
import threading
from local_ocr import OcrSession, OcrCancelled


class OcrPool:
    def __init__(self):
        self._guard = threading.Lock()
        self._entries = {}
        self.stop_requested = False

    def _entry(self, engine):
        with self._guard:
            if self.stop_requested:
                raise OcrCancelled()
            return self._entries.setdefault(engine, {'lock': threading.Lock(), 'session': None,
                                                      'warming': False, 'thread': None})

    def prewarm(self, engine, config):
        try:
            entry = self._entry(engine)
        except OcrCancelled:
            return
        with self._guard:
            if entry['warming'] or entry['session'] is not None:
                return
            entry['warming'] = True
            def warm():
                try:
                    self.recognize(None, engine, config, self, 30)
                except Exception:
                    # Execution will retry and report a normal command error.
                    pass
                finally:
                    with self._guard:
                        entry['warming'] = False
            thread = threading.Thread(target=warm, name='OCR-prewarm', daemon=True)
            entry['thread'] = thread
            thread.start()

    def recognize(self, image, engine, config, context, timeout):
        entry = self._entry(engine)
        pool = self
        class Cancellation:
            @property
            def stop_requested(self):
                return pool.stop_requested or context.stop_requested
        cancel = Cancellation()
        while not entry['lock'].acquire(timeout=.05):
            if cancel.stop_requested:
                raise OcrCancelled()
        try:
            if cancel.stop_requested:
                raise OcrCancelled()
            if entry['session'] is None:
                entry['session'] = OcrSession()
            try:
                return entry['session'].recognize(image, engine, config, cancel, timeout)
            except Exception:
                # Discard pending responses after stop/timeout; never consume a
                # late result as the next request's answer.
                entry['session'].close()
                entry['session'] = None
                raise
        finally:
            entry['lock'].release()

    def close(self):
        with self._guard:
            self.stop_requested = True
            entries = list(self._entries.values())
        for entry in entries:
            with entry['lock']:
                if entry['session'] is not None:
                    entry['session'].close()
                    entry['session'] = None
