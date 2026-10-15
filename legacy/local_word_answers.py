"""Compatibility alias for anclicker.execution.local_word_answers."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.execution.local_word_answers')
