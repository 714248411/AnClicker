"""Shared instruction contracts with lazy editor and action dependencies."""
from anclicker.domain.fields import FieldSpec
from anclicker.execution.instruction_base import InstructionExecutorBase

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'SchemaInstructionEditor': ('from', 'anclicker.ui.instruction_editors.editor', ('SchemaInstructionEditor',), 0),
    'actions': ('from', 'anclicker.execution', ('actions',), 0),
})


__all__ = ['FieldSpec', 'InstructionExecutorBase', 'SchemaInstructionEditor']


def __getattr__(name):
    if name == 'SchemaInstructionEditor':
        SchemaInstructionEditor = _module_imports.load('SchemaInstructionEditor')
        return SchemaInstructionEditor
    if name == 'actions':
        actions = _module_imports.load('actions')
        return actions
    raise AttributeError(name)
