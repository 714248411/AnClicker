"""带最大次数的条件循环流程控制节点。"""

from instructions.流程.控制节点 import 条件循环Editor, 条件循环Executor


class InstructionEditor(条件循环Editor):
    pass


class InstructionExecutor(条件循环Executor):
    CONSUMED_FIELDS = ("方式", "条件", "次数")
