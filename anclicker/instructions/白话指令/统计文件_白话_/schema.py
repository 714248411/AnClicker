"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '统计文件（白话）'
FIELDS = (FieldSpec('folder', '统计哪个文件夹', 'text', '', choices=(), minimum=0), FieldSpec('ext', '只统计这种类型(如 txt，留空=全部)', 'text', '', choices=(), minimum=0))
