import re

def split_into_max_parts(text, delimiter, max_parts=10):
    # 使用正则表达式拆分文本
    parts = re.split(delimiter, text)
    # 计算每个新部分应该包含的原始部分数目
    num_parts_per_section = len(parts) // max_parts + (len(parts) % max_parts > 0)
    
    # 重新组合部分以不超过最大部分数
    new_parts = []
    for i in range(0, len(parts), num_parts_per_section):
        # 将一定数量的部分合并为一个新部分
        new_parts.append('\n\n'.join(parts[i:i+num_parts_per_section]))
    
    # 如果合并后的部分数仍然多于最大允许的部分数，再次合并最后两个部分直到满足条件
    while len(new_parts) > max_parts:
        new_parts[-2:] = ['\n\n'.join(new_parts[-2:])]
    
    return new_parts

# 示例使用
response = "你的response字符串"
steps = split_into_max_parts(response, r"\n\n", 10)
print(steps)
