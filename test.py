import re

def replace_calculated_result(content, calculated_result):
    # 使用正则表达式找到 << 和 >> 之间的内容
    pattern = re.compile(r'<<([^>]*=[^>]*)>>')
    match = pattern.search(content)
    
    if match:
        full_expr = match.group(0)  # 完整的 <<...>> 表达式
        expr_inside = match.group(1)  # << 和 >> 之间的内容
        equal_pos = expr_inside.find('=')
        original_result = expr_inside[equal_pos+1:].strip()  # 等号后面的结果
        
        # 构造新的替换表达式，其中包含正确的计算结果
        new_expr = f"<<{expr_inside[:equal_pos+1]}{calculated_result}>>"
        
        # 替换原内容中的表达式
        content = content.replace(full_expr, new_expr)
        
        # 替换 >> 后面相同的结果
        content = re.sub(r'\b' + re.escape(original_result) + r'\b', calculated_result, content)
    
    return content

# 测试用例
content = "Since each percentage point is worth $2, Paul earns 80*$2 = $<<80*2=1600>>1600. The answer is: 1600"
result = "160.000000000000"
updated_content = replace_calculated_result(content, result)
print(updated_content)
