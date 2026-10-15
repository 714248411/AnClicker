"""Lazy compatibility exports; UI resources do not import editors."""
from importlib import import_module

__all__ = ["InstructionEditor", "InstructionExecutor"]

def __getattr__(name):
    paths = {"InstructionEditor": 'anclicker.ui.instruction_editors.Excel.粘贴到单元格',
             "InstructionExecutor": 'anclicker.instructions.Excel.粘贴到单元格.executor'}
    if name in paths:
        return getattr(import_module(paths[name]), name)
    raise AttributeError(name)
