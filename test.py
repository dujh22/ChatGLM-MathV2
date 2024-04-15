import re
import sympy as sp

def preprocess_and_evaluate(expression):
    # 处理货币符号
    currency_match = re.match(r'\$(\d+(\.\d+)?)(\*\d+(\.\d+)?)?', expression)
    if currency_match:
        # 提取金额和可能的乘数
        amount = float(currency_match.group(1))
        multiplier = currency_match.group(3)
        if multiplier:
            # 计算乘积
            result = amount * float(multiplier.strip('*'))
            return f"${result:.2f}"
        return f"${amount:.2f}"
    
    # 处理百分比（将其转换为小数）
    expression = re.sub(r'(\d+)/(\d+)\*(.*)', lambda m: str(float(m.group(1)) / float(m.group(2))) + '*' + m.group(3), expression)

    # 将可能的符号变量显式定义为符号
    symbols = re.findall(r'[a-zA-Z_]+', expression)
    local_dict = {s: sp.symbols(s) for s in symbols}

    try:
        # 解析并化简表达式
        expr = sp.sympify(expression, locals=local_dict)
        simplified_expr = sp.simplify(expr)
        return str(simplified_expr)
    except Exception as e:
        print("Error in processing:", str(e))
        return expression

# 测试函数
print(preprocess_and_evaluate("40/100*total_students"))
print(preprocess_and_evaluate("$2.63*14"))
