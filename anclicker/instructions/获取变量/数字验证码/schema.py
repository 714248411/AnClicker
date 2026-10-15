"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '数字验证码'
FIELDS = (FieldSpec('区域', '验证码区域 x,y,w,h', 'text', '', required=True), FieldSpec('变量', '变量名称', 'text', '验证码', required=True), FieldSpec('验证码类型', '验证码类型', 'choice', '通用数英1-4位', ('通用数英1-4位', '通用数英5-8位', '通用数英9~11位', '通用数英12位及以上', '通用数英1~6位plus', '定制-数英5位~qcs', '定制-纯数字4位', '通用中文字符1~2位', '通用中文字符3~5位', '通用中文字符6~8位', '通用中文字符9位及以上', '定制-XX西游苦行中文字符', '通用数字计算题', '通用中文计算题')))
