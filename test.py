import re

def replace_calculated_result(content, equations, judge, result):
    for i, equation in enumerate(equations):
        if judge[i] == 0:  # 需要修改的等式
            # 分解等式，获取左侧变量和原始结果
            variable, original_result = equation.split('=')
            variable = variable.strip()
            original_result = original_result.strip()
            
            # 构造用于搜索和替换的正则表达式
            search_pattern = re.escape(variable) + r'\s*=\s*' + re.escape(original_result)
            replace_pattern = f'{variable} = {result[i]}'
            
            # 替换等式
            content = re.sub(search_pattern, replace_pattern, content)
            
            # 替换全文中的原结果
            content = re.sub(r'\b' + re.escape(original_result) + r'\b', result[i], content)
    
    return content

content = "TAustin reaches the ground floor 60 seconds later because 9 + 1 = <<9+1=10>>10 seconds to reach the elevator + 60 seconds in the elevator = <<10+60=70>>70 seconds to reach the ground."
equations = ['9+1=10', '10+60=70']
judge = [0, 1]  # 只替换a的结果
result = ['10.0000000000000', '70.0000000000000']
  # 将a的结果替换为5，b的结果不变（虽然这里b不需要替换）

updated_content = replace_calculated_result(content, equations, judge, result)
print(updated_content)
