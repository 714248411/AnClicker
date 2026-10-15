"""Lazy compatibility exports; UI resources do not import editors."""
from importlib import import_module

__all__ = ["InstructionEditor", "InstructionExecutor"]

def __getattr__(name):
    paths = {"InstructionEditor": 'anclicker.ui.instruction_editors.白话指令.查找文件_白话_',
             "InstructionExecutor": 'anclicker.instructions.白话指令.查找文件_白话_.executor'}
    if name in paths:
        return getattr(import_module(paths[name]), name)
    raise AttributeError(name)
