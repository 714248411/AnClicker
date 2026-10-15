"""Restricted expression evaluation used by condition nodes."""
import ast

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
            values_ = (bool(value_(item_)) for item_ in node_.values)
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
