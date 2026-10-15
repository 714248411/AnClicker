"""Historical import alias; implementation lives in anclicker."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.generated.instructions.键鼠.中键激活.中键激活_ui')
