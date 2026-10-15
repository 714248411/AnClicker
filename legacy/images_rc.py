"""Compatibility alias for generated Qt resources."""
import importlib
import sys
sys.modules[__name__] = importlib.import_module("anclicker.ui.generated.images_rc")
