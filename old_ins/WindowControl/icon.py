from PySide6.QtGui import QIcon, QPixmap


class Icon:
    def __init__(self):
        self.move_up = self.get_icon(":/按钮图标/Window/res/上移.png")
        self.move_down = self.get_icon(":/按钮图标/Window/res/下移.png")
        self.delete = self.get_icon(":/按钮图标/Window/res/清除.png")
        self.save = self.get_icon(":/按钮图标/Window/res/保存.png")
        self.main = self.get_icon(":/按钮图标/Window/res/图标.png")
        self.add = self.get_icon(":/按钮图标/Window/res/添加.png")
        self.setting = self.get_icon(":/按钮图标/Window/res/设置.png")
        self.view = self.get_icon(":/按钮图标/Window/res/查看.png")
        self.modify_instruction = self.get_icon(":/按钮图标/Window/res/修改指令.png")
        self.copy = self.get_icon(":/按钮图标/Window/res/复制.png")

    @staticmethod
    def get_icon(path):
        """获取图标
        :param path: 图标路径"""
        icon = QIcon()
        icon.addPixmap(QPixmap(path))
        return icon
