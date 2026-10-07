"""流程图专用的循环与条件控制节点。"""

from __future__ import annotations

import ast

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from instructions.base import InstructionEditorInterface, InstructionExecutorInterface
from instructions.common import FieldSpec, InstructionExecutorBase, actions
from instructions.models import CommandRecord, ExecutionContext, InstructionDraft


ERROR_POLICIES = ("提示异常并暂停", "提示异常并停止", "自动跳过")


class _ControlEditor(QDialog, InstructionEditorInterface):
    TYPE_ID = ""
    DISPLAY_NAME = ""
    CONDITION = False
    LOOP = False
    FIELDS = ()

    def __init__(self, parent=None, draft=None, context=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle(self.DISPLAY_NAME)
        self.resize(440, 250)
        layout_ = QVBoxLayout(self)
        title_ = QLabel(self.DISPLAY_NAME)
        title_.setObjectName("pageTitle")
        layout_.addWidget(title_)
        form_ = QFormLayout()
        self.condition_edit = None
        self.count_spin = None
        self.mode_combo = None
        if self.LOOP:
            self.mode_combo = QComboBox()
            self.mode_combo.addItems(("次数", "条件"))
            if self.TYPE_ID == "条件循环":
                self.mode_combo.setCurrentText("条件")
            form_.addRow("循环方式", self.mode_combo)
        if self.CONDITION or self.LOOP:
            self.condition_edit = QLineEdit()
            self.condition_edit.setPlaceholderText("例如：计数 >= 10 或 状态 == '完成'")
            form_.addRow("条件表达式", self.condition_edit)
        if self.LOOP:
            self.count_spin = QSpinBox()
            self.count_spin.setRange(1, 1_000_000)
            self.count_spin.setValue(3)
            form_.addRow("循环次数", self.count_spin)
        self.error_policy = QComboBox()
        self.error_policy.addItems(ERROR_POLICIES)
        form_.addRow("异常处理", self.error_policy)
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setRange(1, 1_000_000)
        self.repeat_spin.setValue(1)
        form_.addRow("节点重复", self.repeat_spin)
        self.note_edit = QLineEdit()
        form_.addRow("备注", self.note_edit)
        layout_.addLayout(form_)
        hint_ = QLabel("条件判断节点右侧分支为“是”，上方分支为“否”。")
        hint_.setObjectName("mutedText")
        hint_.setVisible(self.CONDITION)
        layout_.addWidget(hint_)
        buttons_ = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons_.accepted.connect(self.accept)
        buttons_.rejected.connect(self.reject)
        layout_.addWidget(buttons_)
        if draft is not None:
            self.load_draft(draft)

    def get_draft(self) -> InstructionDraft:
        parameters_ = {}
        if self.mode_combo is not None:
            parameters_["方式"] = self.mode_combo.currentText()
        if self.condition_edit is not None:
            condition_ = self.condition_edit.text().strip()
            if not condition_ and (
                self.CONDITION
                or (self.mode_combo is not None and self.mode_combo.currentText() == "条件")
            ):
                raise ValueError("判断条件不能为空")
            parameters_["条件"] = condition_ or "True"
        if self.count_spin is not None:
            parameters_["次数"] = self.count_spin.value()
        return InstructionDraft(
            type_id=self.TYPE_ID,
            parameters=parameters_,
            repeat_count=self.repeat_spin.value(),
            error_policy=self.error_policy.currentText(),
            note=self.note_edit.text().strip(),
        )

    def load_draft(self, draft) -> None:
        draft_ = draft if isinstance(draft, InstructionDraft) else InstructionDraft.from_mapping(draft)
        if self.mode_combo is not None:
            self.mode_combo.setCurrentText(str(draft_.parameters.get("方式", "条件" if self.TYPE_ID == "条件循环" else "次数")))
        if self.condition_edit is not None:
            self.condition_edit.setText(str(draft_.parameters.get("条件", "")))
        if self.count_spin is not None:
            self.count_spin.setValue(int(draft_.parameters.get("次数", 3)))
        self.error_policy.setCurrentText(draft_.error_policy)
        self.repeat_spin.setValue(draft_.repeat_count)
        self.note_edit.setText(draft_.note)


def _condition_value(expression_: str, variables_: dict) -> bool:
    """Evaluate a small, side-effect-free boolean expression."""
    expression_ = (
        expression_.replace(" 且 ", " and ")
        .replace(" 或 ", " or ")
        .replace("非 ", "not ")
    )
    tree_ = ast.parse(expression_, mode="eval")
    allowed_ = (
        ast.Expression, ast.BoolOp, ast.UnaryOp, ast.Compare, ast.Name, ast.Load,
        ast.Constant, ast.And, ast.Or, ast.Not, ast.Eq, ast.NotEq, ast.Lt,
        ast.LtE, ast.Gt, ast.GtE, ast.In, ast.NotIn,
    )
    if any(not isinstance(node_, allowed_) for node_ in ast.walk(tree_)):
        raise ValueError("条件仅支持变量、常量、比较以及 与/或/非")

    def value_(node_):
        if isinstance(node_, ast.Expression):
            return value_(node_.body)
        if isinstance(node_, ast.Constant):
            return node_.value
        if isinstance(node_, ast.Name):
            if node_.id not in variables_:
                raise KeyError(f"条件变量不存在：{node_.id}")
            return variables_[node_.id]
        if isinstance(node_, ast.UnaryOp) and isinstance(node_.op, ast.Not):
            return not bool(value_(node_.operand))
        if isinstance(node_, ast.BoolOp):
            values_ = [bool(value_(item_)) for item_ in node_.values]
            return all(values_) if isinstance(node_.op, ast.And) else any(values_)
        if isinstance(node_, ast.Compare):
            left_ = value_(node_.left)
            for operator_, comparator_ in zip(node_.ops, node_.comparators):
                right_ = value_(comparator_)
                if isinstance(operator_, ast.Eq): result_ = left_ == right_
                elif isinstance(operator_, ast.NotEq): result_ = left_ != right_
                elif isinstance(operator_, ast.Lt): result_ = left_ < right_
                elif isinstance(operator_, ast.LtE): result_ = left_ <= right_
                elif isinstance(operator_, ast.Gt): result_ = left_ > right_
                elif isinstance(operator_, ast.GtE): result_ = left_ >= right_
                elif isinstance(operator_, ast.In): result_ = left_ in right_
                elif isinstance(operator_, ast.NotIn): result_ = left_ not in right_
                else: raise ValueError("不支持的条件运算符")
                if not result_:
                    return False
                left_ = right_
            return True
        raise ValueError("不支持的条件表达式")

    return bool(value_(tree_))


class 循环Editor(_ControlEditor):
    TYPE_ID = DISPLAY_NAME = "循环"
    LOOP = True
    FIELDS = (
        FieldSpec("方式", "循环方式", "choice", "次数", ("次数", "条件")),
        FieldSpec("条件", "条件表达式", "text", "True"),
        FieldSpec("次数", "循环次数", "int", 3),
    )


class 条件判断Editor(_ControlEditor):
    TYPE_ID = DISPLAY_NAME = "条件判断"
    CONDITION = True
    FIELDS = (FieldSpec("条件", "判断条件", "text", "True", required=True),)


class 条件循环Editor(_ControlEditor):
    TYPE_ID = DISPLAY_NAME = "条件循环"
    CONDITION = True
    LOOP = True
    FIELDS = (
        FieldSpec("方式", "循环方式", "choice", "条件", ("次数", "条件")),
        FieldSpec("条件", "判断条件", "text", "True", required=True),
        FieldSpec("次数", "循环次数", "int", 3),
    )


class _ControlExecutor(InstructionExecutorBase):
    TYPE_ID = ""

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        if command.type_id != self.TYPE_ID:
            raise ValueError(f"{self.TYPE_ID}执行器不能执行{command.type_id}")
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        return result_ if delegated_ else True


class 循环Executor(_ControlExecutor):
    TYPE_ID = "循环"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        count_ = int(command.parameters.get("次数", 1))
        if str(command.parameters.get("方式", "次数")) == "条件":
            result_ = _condition_value(
                str(command.parameters.get("条件", "True")), context.variables
            )
            context.metadata[f"flow_condition:{command.id}"] = result_
            context.emit(f"条件循环结果：{'是' if result_ else '否'}")
            return result_
        context.metadata[f"flow_loop_count:{command.id}"] = count_
        context.emit(f"循环节点：{count_} 次")
        return count_


class 条件判断Executor(_ControlExecutor):
    TYPE_ID = "条件判断"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        delegated_, result_ = actions.delegated(context, self.TYPE_ID, command)
        if delegated_:
            return result_
        result_ = _condition_value(str(command.parameters.get("条件", "True")), context.variables)
        context.metadata[f"flow_condition:{command.id}"] = result_
        context.emit(f"条件判断结果：{'是' if result_ else '否'}")
        return result_


class 条件循环Executor(条件判断Executor):
    TYPE_ID = "条件循环"

    def execute_once(self, context: ExecutionContext, command: CommandRecord):
        result_ = super().execute_once(context, command)
        context.metadata[f"flow_loop_count:{command.id}"] = int(command.parameters.get("次数", 1))
        return result_
