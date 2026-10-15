"""Explicit host services; execution does not retain a main window."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'ExecutionContext': ('from', 'anclicker.domain.instructions', ('ExecutionContext',), 0),
})



def _ignore(*args, **kwargs):
    pass


@dataclass
class ExecutionServices:
    database: Any
    output: Callable[[str], None] = _ignore
    command_started: Callable[[str, str], None] = _ignore
    finished: Callable[[str], None] = _ignore
    error_requested: Callable[[dict], None] = _ignore
    cache_cleanup: Callable[[int], None] = _ignore
    notify_error: Callable[[], None] = _ignore
    command_services: Callable[[], Mapping[str, Callable]] = dict
    ocr_pool: Any = None


@dataclass
class RuntimeDependencies:
    database: Any = None
    wait: Callable | None = None
    run_project: Callable | None = None
    ocr_pool: Any = None


ExecutionContext = _module_imports.load('ExecutionContext')


@dataclass
class EditorContext(ExecutionContext):
    """UI capabilities are confined to parameter editing."""
    owner: Any = None

    def for_execution(self) -> ExecutionContext:
        database = self.metadata.get('database')
        return ExecutionContext(
            variables=self.variables, services=self.services, output=self.output,
            iteration=self.iteration, stop_requested=self.stop_requested,
            metadata={'database': database} if database is not None else {},
            runtime=RuntimeDependencies(database=database,
                                        ocr_pool=getattr(self.owner, 'ocr_pool', None)),
        )
