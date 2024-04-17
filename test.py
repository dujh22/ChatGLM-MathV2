def get_display_width(text):
    """计算字符串的显示宽度，中文字符计为2，英文字符计为1"""
    width = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            width += 2  # 假设中文字符宽度为2
        else:
            width += 1
    return width

def print_padded_line(label, value, total_width=40):
    """打印填充后的行，保证右侧对齐"""
    label_width = get_display_width(label)
    spaces = ' ' * (total_width - label_width - len(value))
    print(f"{label}{spaces}{value}")

def print_statistics(stats):
    """打印统计信息为表格形式，并格式化为固定宽度的列，使用print函数，并考虑字符宽度。"""
    print_padded_line("统计指标", "值")
    print('-' * 40)  # 根据总宽度调整分隔线长度

    # 打印数据行
    print_padded_line("计算步骤正确性准确率", f"{stats['correct_judgments']['JudgmentStepCalculatedCorrectly'] / stats['correct_judgments']['total_steps'] * 100:.2f}%")
    print_padded_line("推理步骤正确性准确率", f"{stats['correct_judgments']['JudgmentStepReasoningCorrectly'] / stats['correct_judgments']['total_steps'] * 100:.2f}%")
    print_padded_line("全部正确的JSON占比", f"{stats['all_correct_json_count'] / stats['total_entries'] * 100:.2f}%")
    print_padded_line("使用SymPy的占比", f"{stats['sympy_count'] / stats['total_entries'] * 100:.2f}%")
    print_padded_line("使用Python编程的占比", f"{stats['python_code_count'] / stats['total_entries'] * 100:.2f}%")

# 示例统计数据，仅为展示使用
stats = {
    'correct_judgments': {'JudgmentStepCalculatedCorrectly': 95, 'JudgmentStepReasoningCorrectly': 90, 'total_steps': 100},
    'all_correct_json_count': 80,
    'sympy_count': 50,
    'python_code_count': 30,
    'total_entries': 100
}

print_statistics(stats)
