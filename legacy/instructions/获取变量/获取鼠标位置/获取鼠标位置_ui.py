"""Historical import alias; implementation lives in anclicker."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.generated.instructions.获取变量.获取鼠标位置.获取鼠标位置_ui')
