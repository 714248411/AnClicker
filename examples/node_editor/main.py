import os
import sys

import sys as _import_sys
from pathlib import Path as _ImportPath
if __package__ in (None, ""):
    _import_sys.path.insert(0, str(_ImportPath(__file__).resolve().parents[2]))
from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'QApplication': ('from', 'anclicker.platform.qt_compat.QtWidgets', ('QApplication',), 0),
    'NodeEditorWindow': ('from', 'examples.node_editor.window', ('NodeEditorWindow',), 0),
})



if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

QApplication = _module_imports.load('QApplication')

NodeEditorWindow = _module_imports.load('NodeEditorWindow')


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Clicker Node Editor Prototype")
    window = NodeEditorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
