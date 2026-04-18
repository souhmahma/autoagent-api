import ast
import operator

SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPS:
            raise ValueError(f"Unsupported operator: {op_type}")
        return SAFE_OPS[op_type](_safe_eval(node.left), _safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type}")
        return SAFE_OPS[op_type](_safe_eval(node.operand))
    else:
        raise ValueError(f"Unsupported node type: {type(node)}")


def calculate(expression: str) -> str:
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree.body)
        return str(result)
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"
