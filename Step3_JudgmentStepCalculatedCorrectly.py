# 计算单步

import os
import json
import re
from get_data_for_codeTest import get_data_for_codeTest
from Step1_SplitByRow_forMathShepherd import Step1_SplitByRow_forMathShepherd
from Step2_IsCalculationOrReasoning import Step2_IsCalculationOrReasoning
from use_gpt_api_for_glm_generate import gpt_generate
from run_python_func import run_python
from tqdm import tqdm
from sympy import sympify
from concurrent.futures import ThreadPoolExecutor

def get_llm_calculate_result(input_str):
    # prompt = f"""根据给定的描述生成可执行的Python代码用于计算。描述如下：“${input_str}” 请编写一个Python代码片段来计算，并打印结果。注意只返回python代码即可"""
    prompt = f"""Generate executable Python code for computation based on the given description. The description is as follows: "${input_str}". Please write a Python code snippet to perform the calculation and print the result. Note that only the Python code should be returned."""
    for i in range(10):
        code = gpt_generate(prompt)
        # 截取掉无用的部分
        # 这里的逻辑删去了
        # print(code)
        stdout, stderr = run_python(code)
        if stderr == "":
            return stdout
        else:
            answer = "python脚本无法运行"
    return answer

def get_sympy_calculate_result(input_str):
    try:
        actual_result = sympify(input_str).evalf()
    except Exception as e:
        print(f"计算表达式 {input_str} 时发生错误: {str(e)},使用python自动执行验证")

    actual_result = get_llm_calculate_result(input_str)
    pattern = re.compile(r"\b\d+\.?\d*\b")
    matches = pattern.findall(actual_result)
    if matches:
        # 提取所有找到的数字
        amounts = [float(match) for match in matches]
        return amounts[0]

    return actual_result

def check_calculation(input_str):
    # 使用正则表达式查找计算表达式和结果
    # pattern = r"<<(.+?)=(.+?)>>"
    pattern = r"<<?(.+?)=(.+?)>>?" # <>是可选的
    matches = re.findall(pattern, input_str)

    # 初始化 expected_result
    expected_result = None

    # 遍历所有匹配项进行检查
    for expr, expected_result in matches:
        # 去除头尾的 <<
        expr = expr.lstrip("<")
        # 去除头尾的 >>
        expected_result = expected_result.rstrip(">")
        # 使用 sympy 计算表达式的结果
        actual_result = get_sympy_calculate_result(expr)
        # 比较实际结果和期望结果
        if actual_result != sympify(expected_result).evalf():
            return 0, f"{actual_result}"

    # 如果所有计算都正确，则返回 True
    return 1, f"{expected_result}"

def test_check_calculation():
    # 测试函数
    test_str1 = "这是一个测试字符串，包含一个计算<<20*40=800>>。"
    test_str2 = "这是另一个测试字符串，包含一个错误计算<<30+10=50>>。"

    # 应该返回 (True, None)
    result1 = check_calculation(test_str1)

    # 应该返回 (False, '计算错误：30+10 应该等于 40 而不是 50')
    result2 = check_calculation(test_str2)

    print(result1, result2)

# 串行处理
def process_jsonl_file(source_path, dest_path):
    with open(source_path, 'r', encoding='utf-8') as src_file, \
         open(dest_path, 'w', encoding='utf-8') as dest_file:
        for line in tqdm(src_file, desc='Processing'):
            data = json.loads(line)
            # 遍历每一步的解决方案
            if 'solution' in data:
                for step, info in data['solution'].items(): # step变量会接收步骤的名称（如"Step 1"），而info变量会接收与这个步骤名称对应的字典值。
                    # 判断并添加新键
                    info['JudgmentStepCalculatedCorrectly'], info['StepCalculatedCorrectlyResult'] = check_calculation(info['content'])
            # 将修改后的数据写回新的JSONL文件
            json.dump(data, dest_file, ensure_ascii=False)
            dest_file.write('\n')

# 并发处理
def process_line(line):
    data = json.loads(line)
    if 'solution' in data:
        for step, info in data['solution'].items():
            # 此处假设 check_calculation 已正确实现
            info['JudgmentStepCalculatedCorrectly'], info['StepCalculatedCorrectlyResult'] = check_calculation(info['content'])
    # 将处理后的数据转换为字符串以便写入文件
    return json.dumps(data, ensure_ascii=False) + '\n'

def process_jsonl_file_concurrent(source_path, dest_path):
    # 读取文件的所有行
    with open(source_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    results = []

    # 使用 ThreadPoolExecutor 来并发处理每一行
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 提交所有行到线程池
        future_to_line = {executor.submit(process_line, line): line for line in tqdm(lines, desc='Processing')}

        # 使用tqdm创建进度条
        with tqdm(total=len(future_to_line), desc='Processing lines') as progress:
            # 收集处理结果
            for future in concurrent.futures.as_completed(future_to_line):
                results.append(future.result())
                progress.update(1)  # 更新进度条

    # 写入结果到目标文件
    with open(dest_path, 'w', encoding='utf-8') as file:
        file.writelines(results)



def Step3_JudgmentStepCalculatedCorrectly(source_folder, target_folder):
    
    print("第三步判断单步计算是否正确……")

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    for filename in os.listdir(source_folder):
        if filename.endswith('.jsonl'):
            source_path = os.path.join(source_folder, filename)
            print("正在处理文件:", source_path)
            dest_path = os.path.join(target_folder, filename)
            # process_jsonl_file(source_path, dest_path)
            process_jsonl_file_concurrent(source_path, dest_path)
# 使用方法：
def main():
    code_test_state = False
    base_folder = "F://code//github//ChatGLM-MathV2"
    dataset_name = "peiyi9979_Math_Shepherd"
    source_folder = base_folder + '//raw_data//' + dataset_name
    if code_test_state:
        get_data_for_codeTest(source_folder)
        source_folder = source_folder + "_for_codeTest"
    mid_name = base_folder + '//data//' + dataset_name
    if code_test_state:
        target_folder1 = mid_name + "_for_codeTest" + "_Step1_SplitByRow_forMathShepherd"
        target_folder2 = mid_name + "_for_codeTest" + "_Step2_IsCalculationOrReasoning"
        target_folder3 = mid_name + "_for_codeTest" + "_Step3_JudgmentStepCalculatedCorrectly"
    else:
        target_folder1 = mid_name + "_Step1_SplitByRow_forMathShepherd"
        target_folder2 = mid_name + "_Step2_IsCalculationOrReasoning"
        target_folder3 = mid_name + "_Step3_JudgmentStepCalculatedCorrectly"

    #Step1_SplitByRow_forMathShepherd(source_folder, target_folder1)
    #Step2_IsCalculationOrReasoning(target_folder1, target_folder2)
    Step3_JudgmentStepCalculatedCorrectly(target_folder2, target_folder3)

def main2():
    print(get_llm_calculate_result("Paul is collecting license plates from different states. He has plates from 40 different states. For each percentage point of total US states that he has, his parents will give him $2. How much does he earn from them?"))

if __name__ == '__main__':
    main()