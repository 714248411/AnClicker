"""Historical import alias; implementation lives in anclicker."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.generated.instructions.网页自动化.网页截图.网页截图_ui')
