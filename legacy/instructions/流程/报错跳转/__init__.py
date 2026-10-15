"""Lazy compatibility exports; UI resources do not import editors."""
from importlib import import_module

__all__ = ["InstructionEditor", "InstructionExecutor"]

def __getattr__(name):
    paths = {"InstructionEditor": 'anclicker.ui.instruction_editors.流程.报错跳转',
             "InstructionExecutor": 'anclicker.instructions.流程.报错跳转.executor'}
    if name in paths:
        return getattr(import_module(paths[name]), name)
    raise AttributeError(name)
