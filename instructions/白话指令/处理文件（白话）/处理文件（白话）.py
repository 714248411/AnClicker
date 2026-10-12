from instructions.common import FieldSpec
from instructions.common.rpa_instruction import RpaInstructionEditor, RpaInstructionExecutor
from importlib import import_module
Ui_InstructionEditor = import_module('.处理文件（白话）_ui', __package__).Ui_InstructionEditor

class InstructionEditor(RpaInstructionEditor):
    TYPE_ID = '处理文件（白话）'
    DISPLAY_NAME = '处理文件(白话)'
    COMMAND_ID = 'fileOp'
    UI_CLASS = Ui_InstructionEditor
    FIELDS = (
        FieldSpec('action', '做什么', 'choice', '删除', choices=('删除', '复制', '移动', '列出文件名'), minimum=0),
        FieldSpec('folder', '哪个文件夹', 'text', '', choices=(), minimum=0),
        FieldSpec('sortBy', '按什么排序', 'choice', '文件名', choices=('文件名', '修改时间', '文件大小'), minimum=0),
        FieldSpec('order', '排序方向', 'choice', '从小到大', choices=('从小到大', '从大到小'), minimum=0),
        FieldSpec('index', '第几个文件(如 1、1,3,5、1-3、-1=倒数第1)', 'text', '1', choices=(), minimum=0),
        FieldSpec('dst', '复制/移动到哪(文件夹或新路径)', 'text', '', choices=(), minimum=0),
    )

class InstructionExecutor(RpaInstructionExecutor):
    TYPE_ID = '处理文件（白话）'
    COMMAND_ID = 'fileOp'
