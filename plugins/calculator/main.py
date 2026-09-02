"""Calculator plugin — provides calculate tool."""


def calculate(expression: str) -> dict:
    """Evaluate a mathematical expression safely."""
    try:
        # Use eval with restricted namespace (safe for basic math)
        import ast
        import operator
        
        allowed_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        def safe_eval(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                op = allowed_ops.get(type(node.op))
                if op is None:
                    raise ValueError("Unsupported operator")
                return op(left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = safe_eval(node.operand)
                op = allowed_ops.get(type(node.op))
                if op is None:
                    raise ValueError("Unsupported operator")
                return op(operand)
            else:
                raise ValueError("Unsupported expression")
        
        parsed = ast.parse(expression, mode='eval')
        result = safe_eval(parsed.body)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


def register_tools(registry):
    """Register plugin tools with registry."""
    registry.register(
        "calculate",
        "Evaluate a mathematical expression",
        {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate"}
            },
            "required": ["expression"],
        },
        calculate
    )