from PySide6.QtGui import QColor


BACKGROUND_COLOR = QColor("#171a21")
GRID_SMALL_COLOR = QColor("#222732")
GRID_LARGE_COLOR = QColor("#2c3340")
NODE_COLOR = QColor("#252b36")
NODE_BORDER_COLOR = QColor("#414b5d")
NODE_SELECTED_COLOR = QColor("#58a6ff")
TEXT_COLOR = QColor("#e6edf3")
MUTED_TEXT_COLOR = QColor("#9aa7b5")
INPUT_PORT_COLOR = QColor("#6cb6ff")
OUTPUT_PORT_COLOR = QColor("#f2cc60")
PORT_TYPE_COLORS = {
    "流程": QColor("#a5d6ff"),
    "输入": QColor("#6cb6ff"),
    "成功": QColor("#56d364"),
    "完成": QColor("#56d364"),
    "异常": QColor("#f47067"),
    "真": QColor("#3fb950"),
    "假": QColor("#f2cc60"),
}
EDGE_COLOR = QColor("#77869a")
EDGE_SELECTED_COLOR = QColor("#58a6ff")
INVALID_EDGE_COLOR = QColor("#f47067")
STRAIGHT_EDGE_DISTANCE = 100.0
AUTO_CONNECT_DISTANCE = 32.0

NODE_MIN_WIDTH = 88.0
NODE_HEIGHT = 54.0
PORT_RADIUS = 6.0


NODE_TYPES = {
    "开始": {
        "category": "流程",
        "color": QColor("#238636"),
        "inputs": [],
        "outputs": ["流程"],
    },
    "结束": {
        "category": "流程",
        "color": QColor("#da3633"),
        "inputs": ["流程"],
        "outputs": [],
    },
    "图像点击": {
        "category": "动作",
        "color": QColor("#1f6feb"),
        "inputs": ["输入"],
        "outputs": ["成功", "异常"],
    },
    "文本输入": {
        "category": "动作",
        "color": QColor("#8957e5"),
        "inputs": ["输入"],
        "outputs": ["成功", "异常"],
    },
    "时间等待": {
        "category": "等待",
        "color": QColor("#9e6a03"),
        "inputs": ["输入"],
        "outputs": ["完成"],
    },
    "变量判断": {
        "category": "判断",
        "color": QColor("#bf4b8a"),
        "inputs": ["输入"],
        "outputs": ["真", "假", "异常"],
    },
}
