"""是/否条件分支流程控制节点。"""

from anclicker.ui.instruction_editors.control_nodes import 条件判断Editor, 条件判断Executor

from anclicker._imports import DeferredImports as _DeferredImports

# Dependencies declared here retain their existing on-demand loading boundaries.
_module_imports = _DeferredImports(globals(), {
    'InstructionExecutor': ('from', 'anclicker.instructions.流程.条件判断.executor', ('InstructionExecutor',), 0),
})



class InstructionEditor(条件判断Editor):
    pass


InstructionExecutor = _module_imports.load('InstructionExecutor')
