"""One live view of application activity and operation eligibility."""
from __future__ import annotations
import weakref


class ApplicationState:
    def __init__(self, window):
        try:
            self._window = weakref.ref(window)
        except TypeError:
            # Small extension/test hosts may not support weak references.
            self._window = lambda: window

    @property
    def window(self):
        return self._window()

    def activities(self):
        window = self.window
        workspace = getattr(window, 'workspace', None)
        view = getattr(window, 'view_workspace', None)
        thread = getattr(window, 'command_thread', None)
        scheduler = getattr(window, 'task_scheduler', None)
        states = {
            'execution': bool(thread is not None and thread.isRunning()),
            'test': bool(getattr(workspace, '_instruction_test_active', False)),
            'schedule': bool(getattr(scheduler, 'busy', False)),
            'update': bool(getattr(window, '_update_preparing', False)),
        }
        for name, attribute in [('recording', 'recording_page'),
                                ('web_recording', 'web_recording_page'),
                                ('agent', 'agent_page')]:
            states[name] = bool(getattr(getattr(view, attribute, None), 'busy', False))
        return frozenset(name for name, active in states.items() if active)

    def is_busy(self, *, excluding=()):
        return bool(self.activities() - set(excluding))

    def can_edit_project(self):
        return not self.is_busy()

    def can_start_execution(self):
        return not self.is_busy()


def application_state(window):
    """Also supports small test/extension hosts without Main_window setup."""
    state = getattr(window, 'application_state', None)
    return state if state is not None else ApplicationState(window)
