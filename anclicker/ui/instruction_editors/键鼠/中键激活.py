"""Use the same configurable trigger editor as window middle activation."""
from anclicker.ui.instruction_editors.窗口键鼠.窗口中键激活 import InstructionEditor as TriggerEditor
from anclicker.instructions.键鼠.中键激活.schema import FIELDS
from anclicker.instructions.键鼠.中键激活.executor import InstructionExecutor


class InstructionEditor(TriggerEditor):
    TYPE_ID = DISPLAY_NAME = '中键激活'
    FIELDS = FIELDS
