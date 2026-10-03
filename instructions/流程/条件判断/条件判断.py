"""是/否条件分支流程控制节点。"""

from instructions.流程.控制节点 import 条件判断Editor, 条件判断Executor


class InstructionEditor(条件判断Editor):
    pass


class InstructionExecutor(条件判断Executor):
    CONSUMED_FIELDS = ("条件",)
