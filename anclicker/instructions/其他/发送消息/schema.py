"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '发送消息'
FIELDS = (FieldSpec('联系人', '微信联系人（精确名称）', 'text', '', required=True), FieldSpec('消息内容', '消息内容', 'multiline', '', required=True))
