"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
TYPE_ID = '打开网页'
FIELDS = (FieldSpec('url', '网页地址', 'text', 'https://', choices=(), minimum=0), FieldSpec('engine', '用哪个内核(朗坤6.5等老系统选Edge)', 'choice', '跟随当前', choices=('跟随当前', 'Chrome', 'Edge'), minimum=0), FieldSpec('target', '打开方式', 'choice', '新窗口', choices=('新窗口', '当前标签页', '新标签页'), minimum=0), FieldSpec('loginMode', '登录方式(多账号做隔离)', 'choice', '独立登录(每次全新)', choices=('独立登录(每次全新)', '独立登录(按账号位保存)', '共用登录(沿用已有登录)'), minimum=0), FieldSpec('waitType', '等待加载', 'choice', '加载完成', choices=('加载完成', '立即返回'), minimum=0))
