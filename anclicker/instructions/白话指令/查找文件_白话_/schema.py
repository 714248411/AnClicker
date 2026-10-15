"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '查找文件（白话）'
FIELDS = (FieldSpec('folder', '在哪个文件夹找', 'text', '', choices=(), minimum=0), FieldSpec('keyword', '文件名包含什么字(留空=列出全部)', 'text', '', choices=(), minimum=0), FieldSpec('ext', '只找这种类型(如 txt，留空=全部)', 'text', '', choices=(), minimum=0))
