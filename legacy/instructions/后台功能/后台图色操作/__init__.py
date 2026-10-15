"""Lazy compatibility exports; UI resources do not import editors."""
from importlib import import_module

__all__ = ["InstructionEditor", "InstructionExecutor"]

def __getattr__(name):
    paths = {"InstructionEditor": 'anclicker.ui.instruction_editors.后台功能.后台图色操作',
             "InstructionExecutor": 'anclicker.instructions.后台功能.后台图色操作.executor'}
    if name in paths:
        return getattr(import_module(paths[name]), name)
    raise AttributeError(name)
