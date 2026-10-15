"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '后台答题器'
FIELDS = (FieldSpec('题库路径', 'Word 题库 (.docx)', 'path', '', required=True), FieldSpec('题目来源', '题目来源', 'choice', '输入题目', ('输入题目', '最近OCR文字', '变量')), FieldSpec('题目', '题目内容 / 变量名', 'text', ''), FieldSpec('匹配方式', '匹配方式', 'choice', '精准', ('精准', '包含', '模糊')), FieldSpec('相似度', '模糊匹配相似度', 'float', 0.85, minimum=0.01, maximum=1), FieldSpec('未找到', '未找到答案', 'choice', '报错', ('报错', '返回空值')), FieldSpec('变量', '答案变量', 'text', '答案', required=True))
