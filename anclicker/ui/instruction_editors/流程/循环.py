"""循环流程控制节点。"""

from anclicker.ui.instruction_editors.control_nodes import 循环Editor, 循环Executor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.流程.循环.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(循环Editor):
    pass


InstructionExecutor = _module_imports.load('InstructionExecutor')
