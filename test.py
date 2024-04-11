import re

def process_solution(solution):
    # 通过正则表达式匹配句号，但要排除小数点和引号内的句号
    pattern = r"(?<!\d)\.(?!\d)|(?<!['\"])\.(?=['\"])"
    # 将句号分割成列表
    segments = re.split(pattern, solution)
    # 进一步处理引号内的句号，确保它们保持在同一行
    cleaned_segments = []
    quote_open = False
    for segment in segments:
        if "'" in segment or '"' in segment:
            if not quote_open:
                cleaned_segments.append(segment)
                quote_open = True
            else:
                cleaned_segments[-1] += segment
                quote_open = False
        else:
            cleaned_segments.extend(segment.split('\n'))
    # 构建结果字典
    result = {str(index): line for index, line in enumerate(cleaned_segments)}
    return result

# 测试
solution = "This is a test sentence. It has a decimal point, like 3.14. But this one is in quotes: 'This is a test sentence with a period.'. And this one is in double quotes: \"Another test sentence with a period.\""
print(process_solution(solution))
