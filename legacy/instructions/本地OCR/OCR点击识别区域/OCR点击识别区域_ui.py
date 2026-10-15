"""Historical import alias; implementation lives in anclicker."""
import importlib as _importlib
import sys as _sys
_sys.modules[__name__] = _importlib.import_module('anclicker.ui.generated.instructions.本地OCR.OCR点击识别区域.OCR点击识别区域_ui')
