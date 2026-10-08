"""OCR粘贴：独立拖拽指令，共享离线 OCR 引擎。"""
from instructions.common.local_ocr_instruction import LocalOcrEditor, LocalOcrExecutor, fields_for
from .OCR粘贴_ui import Ui_InstructionEditor


class InstructionEditor(LocalOcrEditor):
    TYPE_ID = 'OCR粘贴'
    DISPLAY_NAME = TYPE_ID
    UI_CLASS = Ui_InstructionEditor
    FIELDS = fields_for(TYPE_ID)


class InstructionExecutor(LocalOcrExecutor):
    TYPE_ID = 'OCR粘贴'
