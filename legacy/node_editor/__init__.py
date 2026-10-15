"""Compatibility alias for anclicker.ui.node_editor."""
import importlib as _importlib
import sys as _sys
_implementation = _importlib.import_module('anclicker.ui.node_editor')
# Register children before exposing the canonical package's __path__. Otherwise
# Python can execute the same source again under node_editor.items, producing
# distinct NodeItem/EdgeItem classes and breaking isinstance checks.
for _child in ('cutting', 'flow_arrows', 'items', 'palette', 'routing_index',
               'scene', 'specs', 'style', 'view', 'widget'):
    _name = 'anclicker.ui.node_editor.' + _child
    _sys.modules[__name__ + '.' + _child] = _importlib.import_module(_name)
_sys.modules[__name__] = _implementation
