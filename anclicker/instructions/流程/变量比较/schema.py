"""Instruction parameter schema."""
from __future__ import annotations
from anclicker.domain.fields import FieldSpec
from anclicker.domain.flow_jumps import TARGET_MODES
from anclicker.domain.flow_jumps import OPERATORS
TYPE_ID = '变量比较'
FIELDS = (FieldSpec('变量', '左侧变量', 'text', '', required=True), FieldSpec('比较条件', '比较条件', 'choice', '等于', OPERATORS), FieldSpec('比较对象', '右侧类型', 'choice', '固定值', ('固定值', '变量')), FieldSpec('比较值', '右侧值 / 变量名', 'text', ''), FieldSpec('比较类型', '比较类型', 'choice', '自动', ('自动', '数字', '文本')), *(field for prefix in ('是', '否') for field in (FieldSpec(prefix + '跳转方式', prefix + '：跳转方式', 'choice', '连线节点', TARGET_MODES), FieldSpec(prefix + '目标行', prefix + '：目标行（从 1 开始）', 'int', 1), FieldSpec(prefix + '项目路径', prefix + '：目标项目文件', 'text', ''))))
