"""Visual constants shared by the node editor components."""

from qt_compat.QtGui import QColor


BACKGROUND_COLOR = QColor("#171a21")
GRID_SMALL_COLOR = QColor("#222732")
GRID_LARGE_COLOR = QColor("#2c3340")
NODE_COLOR = QColor("#252b36")
NODE_BORDER_COLOR = QColor("#414b5d")
NODE_SELECTED_COLOR = QColor("#7c8cff")
TEXT_COLOR = QColor("#e6edf3")
INPUT_PORT_COLOR = QColor("#a5b0ff")
OUTPUT_PORT_COLOR = QColor("#7c8cff")
EDGE_COLOR = QColor("#77869a")
EDGE_SELECTED_COLOR = QColor("#7c8cff")

START_COLOR = QColor("#6574d8")
END_COLOR = QColor("#da3633")
DEFAULT_NODE_COLOR = QColor("#6574d8")

NODE_MIN_WIDTH = 130.0
NODE_HEIGHT = 68.0
PORT_RADIUS = 6.0
AUTO_CONNECT_DISTANCE = 48.0
STRAIGHT_EDGE_DISTANCE = 100.0

MIN_ZOOM = 0.000001
MAX_ZOOM = 64.0


def apply_theme(mode: str) -> None:
    """Update the shared mutable colors used by all editor scenes/items."""
    palette = (
        {
            "background": "#f7f7f8", "grid_small": "#ececf1",
            "grid_large": "#d9d9e0", "node": "#ffffff",
            "border": "#c7c7cf", "text": "#2f2f2f", "edge": "#7b8190",
        }
        if mode == "light"
        else {
            "background": "#09090b", "grid_small": "#141417",
            "grid_large": "#202024", "node": "#18181b",
            "border": "#3c3c43", "text": "#f1f1f3", "edge": "#8b98a8",
        }
    )
    for color, key in (
        (BACKGROUND_COLOR, "background"),
        (GRID_SMALL_COLOR, "grid_small"),
        (GRID_LARGE_COLOR, "grid_large"),
        (NODE_COLOR, "node"),
        (NODE_BORDER_COLOR, "border"),
        (TEXT_COLOR, "text"),
        (EDGE_COLOR, "edge"),
    ):
        color.setRgba(QColor(palette[key]).rgba())
    accent = "#0088ff" if mode == "dark" else "#6574d8"
    for color in (NODE_SELECTED_COLOR, OUTPUT_PORT_COLOR, EDGE_SELECTED_COLOR,
                  START_COLOR, DEFAULT_NODE_COLOR):
        color.setRgba(QColor(accent).rgba())
    INPUT_PORT_COLOR.setRgba(QColor("#6cbaff" if mode == "dark" else "#a5b0ff").rgba())
