from anclicker.ui.instruction_editors.extensions.extraction_export import ExportEditor
from anclicker.instructions.网页抓取工具.提取转Excel.schema import FIELDS

class InstructionEditor(ExportEditor):
    TYPE_ID = DISPLAY_NAME = '提取转Excel'
    FORMAT = 'Excel'
    FIELDS = FIELDS
