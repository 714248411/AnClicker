"""宿主程序使用的控件无关指令接口。"""

from __future__ import annotations

from typing import Mapping, Any

from .models import CommandRecord, ExecutionContext, InstructionDraft


class InstructionEditorInterface:
    """调用方只依赖草稿接口，不依赖任何 Qt 控件名称。"""

    def get_draft(self) -> InstructionDraft:
        raise NotImplementedError

    def load_draft(self, draft: InstructionDraft | Mapping[str, Any]) -> None:
        raise NotImplementedError


class InstructionExecutorInterface:
    def execute(self, context: ExecutionContext, command: CommandRecord):
        raise NotImplementedError
