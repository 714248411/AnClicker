"""独立指令模块入口。"""

from .models import CommandRecord, ExecutionContext, InstructionDraft
from .base import InstructionEditorInterface, InstructionExecutorInterface
from .registry import (
    INSTRUCTION_SPECS,
    InstructionSpec,
    get_instruction_spec,
    hidden_imports,
    iter_instruction_specs,
)

__all__ = [
    "CommandRecord",
    "ExecutionContext",
    "InstructionDraft",
    "InstructionEditorInterface",
    "InstructionExecutorInterface",
    "INSTRUCTION_SPECS",
    "InstructionSpec",
    "get_instruction_spec",
    "hidden_imports",
    "iter_instruction_specs",
]
