"""循环流程控制节点。"""

from instructions.流程.控制节点 import 循环Editor, 循环Executor


class InstructionEditor(循环Editor):
    pass


class InstructionExecutor(循环Executor):
    CONSUMED_FIELDS = ("方式", "条件", "次数")
