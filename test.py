import sympy as sp

def evaluate_expression(expr):
    try:
        # 将表达式中的变量正确处理，如将'3m'解析为3*m
        expr = expr.replace('Sandy\'s_age', 'Sandy_age')  # 替换为有效的变量名
        expr = expr.replace('3m', '3*m')  # 替换为 3*m
        expr = expr.replace('3B', '3*B')  # 替换为 3*B
        # 处理隐式乘法，如'3(10)'应该为'3*10'
        expr = expr.replace(')', ')*').replace(')*)', ')')  # 替换所有括号后的数字以添加乘号

        # 使用 sympy 解析和计算表达式
        expr = sp.sympify(expr)
        return expr, expr.evalf()
    except Exception as e:
        return None, str(e)

# 测试一些表达式
expressions = [
    "10*Sandy's_age",
    "27-3B/2",
    "10+3(10)",
    "16+3(16)+7",
    "12+2(3)",
    "3m+5"
]

for expr in expressions:
    result, message = evaluate_expression(expr)
    print(f"处理表达式 '{expr}' 的结果是：{result}, 错误信息：{message}")
