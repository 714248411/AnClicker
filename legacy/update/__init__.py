"""Historical package API; children resolve through thin aliases."""
import importlib as _importlib
import sys as _sys
_implementation = _importlib.import_module('anclicker.app.updates')
__all__ = getattr(_implementation, '__all__', [name for name in vars(_implementation) if not name.startswith('_')])
def __getattr__(name):
    return getattr(_implementation, name)
