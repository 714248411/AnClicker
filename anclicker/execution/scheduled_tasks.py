"""Compatibility alias for the application scheduler."""
import sys
from importlib import import_module
sys.modules[__name__] = import_module("anclicker.app.scheduled_tasks")
