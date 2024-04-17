import json

from chatglm import ChatGLM
ChatGLM = ChatGLM()


def read_jsonl(file_path):
    """读取JSONL文件，返回一个包含多个JSON对象的列表。"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data.append(json.loads(line))
    return data

def analyze_data(json_data):
    """分析JSON对象列表，计算所需的统计数据。"""
    total_entries = len(json_data)  # 总的JSON对象数
    all_correct_json_count = 0  # 所有正确标注的JSON对象数
    sympy_count = 0  # 使用SymPy的次数
    python_code_count = 0  # 使用Python编程的次数
    
    # 用于存储正确判断的次数
    correct_judgments = {
        'JudgmentStepCalculatedCorrectly': 0,
        'JudgmentStepReasoningCorrectly': 0,
        'total_steps': 0  # 总步骤数
    }
    
    for entry in json_data:
        all_correct = True
        sympy_used = False
        python_used = False
        
        history = ""
        for step_key, step_info in entry['solution'].items():
            # 计算总步骤数
            correct_judgments['total_steps'] += 1
            
            # 检查每种判断类型

            # 检测针对计算步骤的判断是否正确
            # prompt1 = f"""我正在尝试检查一个数学问题的求解过程是否计算正确、推理合理。具体问题是：{entry['question']}。\n\n 我目前采用的解题步骤如下：{history} \n\n 现在我要检查的步骤是：{step_key}，内容是：{step_info['content']}。\n\n请问这个步骤的计算是否正确？（是/否）"""
            prompt1 = f"""I'm trying to check that the solution to a math problem is calculated correctly and reasoned correctly. The specific problem is: {entry['question']} \n\n The steps I have used so far to solve the problem are as follows:{history} \n\n Now the steps I want to check are:{step_key} and the content is:{step_info['content']}. \n\n Is this step calculated correctly? (Yes/No)
            """
            response1 = ChatGLM.generate(prompt1)
            # 获取response的第一句话或者如果没有符号就是完整的response
            response1_first_sentence = response1.split(".")[0]

            if response1_first_sentence[:3].lower() == "yes" or ("correct" in response1_first_sentence.lower() and "incorrect" not in response1_first_sentence.lower()):  # 如果计算正确
                if all(item == 1 for item in step_info['JudgmentStepCalculatedCorrectly']):
                    correct_judgments['JudgmentStepCalculatedCorrectly'] += 1
                else:
                    all_correct = False
            else:
                if any(item == 0 for item in step_info['JudgmentStepCalculatedCorrectly']):
                  correct_judgments['JudgmentStepCalculatedCorrectly'] += 1
                else:
                    all_correct = False  
            
            # 检测针对推理步骤的判断是否正确
            # prompt2 = f"""我正在尝试检查一个数学问题的求解过程是否计算正确、推理合理。具体问题是：{entry['question']}。\n\n 我目前采用的解题步骤如下：{history} \n\n 现在我要检查的步骤是：{step_key}，内容是：{step_info['content']}。\n\n请问这个步骤的推理是否合理？（是/否）"""
            prompt2 = f"""I'm trying to check that the solution to a math problem is calculated correctly and reasoned correctly. The specific problem is: {entry['question']} \n\n The steps I have used so far to solve the problem are as follows:{history} \n\n Now the steps I want to check are:{step_key} and the content is:{step_info['content']}. \n\n Is this step reasoned correctly? (Yes/No)"""
            response2 = ChatGLM.generate(prompt2)
            # 获取response的第一句话或者如果没有符号就是完整的response
            response2_first_sentence = response2.split(".")[0]

            if response2_first_sentence[:3].lower() == "yes" or ("correct" in response2_first_sentence.lower() and "incorrect" not in response2_first_sentence.lower()):  # 如果推理正确
                if step_info['JudgmentStepReasoningCorrectly'] == 1:
                    correct_judgments['JudgmentStepReasoningCorrectly'] += 1
                else:
                    all_correct = False
            else:
                if step_info['JudgmentStepReasoningCorrectly'] == 0:
                    correct_judgments['JudgmentStepReasoningCorrectly'] += 1
                else:
                    all_correct = False

            
            # 检查是否使用了SymPy或Python编程
            if 'leftSideOfEqual_use_sympy_or_llm' in step_info:
                if 'sympy and llm' in step_info['leftSideOfEqual_use_sympy_or_llm']:
                    python_used = True
                else:
                    sympy_used = True
            if 'rightSideOfEqual_use_sympy_or_llm' in step_info:
                if 'sympy and llm' in step_info['rightSideOfEqual_use_sympy_or_llm']:
                    python_used = True
                else:
                    sympy_used = True
            
            history += f"{step_key}: {step_info['content']}\n"
        
        if all_correct:
            all_correct_json_count += 1
        if sympy_used:
            sympy_count += 1
        if python_used:
            python_code_count += 1
    
    return {
        'correct_judgments': correct_judgments,
        'all_correct_json_count': all_correct_json_count,
        'sympy_count': sympy_count,
        'python_code_count': python_code_count,
        'total_entries': total_entries
    }

def main():
    # 根据需要修改文件路径
    file_path = 'your_file.jsonl'
    json_data = read_jsonl(file_path)
    stats = analyze_data(json_data)
    
    # 打印统计信息
    print("计算步骤正确性准确率:", 
          stats['correct_judgments']['JudgmentStepCalculatedCorrectly'] / stats['correct_judgments']['total_steps'])
    print("推理步骤正确性准确率:", 
          stats['correct_judgments']['JudgmentStepReasoningCorrectly'] / stats['correct_judgments']['total_steps'])
    print("全部正确的JSON占比:", 
          stats['all_correct_json_count'] / stats['total_entries'])
    print("使用SymPy的占比:", 
          stats['sympy_count'] / stats['total_entries'])
    print("使用Python编程的占比:", 
          stats['python_code_count'] / stats['total_entries'])

if __name__ == "__main__":
    main()
