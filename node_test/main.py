import os
import sys


if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication

from node_test.window import NodeEditorWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Clicker Node Editor Prototype")
    window = NodeEditorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
