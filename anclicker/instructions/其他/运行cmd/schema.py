"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '运行cmd'
FIELDS = (FieldSpec('命令', 'CMD命令', 'multiline', '', required=True), FieldSpec('等待完成', '等待命令完成', 'bool', True))
