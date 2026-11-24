from anclicker.ui.instruction_editors.键鼠.图像点击 import InstructionEditor as BaseEditor

class InstructionEditor(BaseEditor):
    TYPE_ID = DISPLAY_NAME = '窗口图像点击'
    WINDOW_IMAGE = True
