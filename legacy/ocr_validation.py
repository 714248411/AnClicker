"""Compatibility alias."""
import importlib
import sys
sys.modules[__name__] = importlib.import_module("anclicker.app.ocr_validation")
