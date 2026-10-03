"""Embeddable instruction graph editor widgets.

The package deliberately has no dependency on the Clicker database or main
window.  Hosts provide instruction specifications and graph records, then
persist changes emitted through :class:`NodeEditorWidget` signals.
"""

from node_editor.palette import INSTRUCTION_MIME_TYPE, InstructionPalette
from node_editor.widget import NodeEditorWidget

__all__ = [
    "INSTRUCTION_MIME_TYPE",
    "InstructionPalette",
    "NodeEditorWidget",
]
