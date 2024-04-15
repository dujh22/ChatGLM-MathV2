# 计算单步

import os
import json
import re
from get_data_for_codeTest import get_data_for_codeTest
from Step1_SplitByRow_forMathShepherd import Step1_SplitByRow_forMathShepherd
from Step2_IsCalculationOrReasoning import Step2_IsCalculationOrReasoning
from use_gpt_api_for_glm_generate import gpt_generate
# from use_glm_api_for_glm_generate import glm_generate
from run_python_func import run_python
from tqdm import tqdm
import sympy as sp
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
import logging

# 配置日志记录器
logging.basicConfig(filename='Step3_JudgmentStepCalculatedCorrectly.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# 输出函数
def log(*args):
    '''
    输出函数
    :param need_log: 是否需要输出
    :param args: 输出参数
    '''
    need_log = False
    if need_log:
        print(*args)
    time.sleep(0)

# 公式预处理
def formula_preprocessing(input_str):
    # 去除数字前的前导零
    input_str = re.sub(r'\b0+(\d+)', r'\1', input_str)
    
    # 处理时间表示 (假设时间表示为小时和分钟，如 4:30 转换为 4/30)
    input_str = re.sub(r'(\d+):(\d+)', r'\1/\2', input_str)

    # 处理百分比
    input_str = re.sub(r'(\d+)%', r'(\1/100)', input_str)

    # 处理分数表示中的空格（假设意图是将 3 3/4 写成 33/4）
    input_str = re.sub(r'(\d+)\s+(\d+)/(\d+)', r'\1\2/\3', input_str)

    # 使用正则表达式添加必要的乘法符号
    input_str = re.sub(r'(\d)(\()', r'\1*\2', input_str)  # 处理数字后跟左括号的情况16+3(16)+7
    input_str = re.sub(r'(\))(\d)', r'\1*\2', input_str)  # 处理右括号后跟数字的情况(1/2)20
    input_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', input_str)  # 处理数字后跟变量的情况2x
    input_str = re.sub(r'([a-zA-Z])(\()', r'\1*\2', input_str)  # 处理变量后跟左括号的情况x(5+2)

    # 处理货币符号
    currency_match = re.match(r'\$(\d+(\.\d+)?)(\*\d+(\.\d+)?)?', input_str)
    if currency_match:
        # 提取金额和可能的乘数
        amount = float(currency_match.group(1))
        multiplier = currency_match.group(3)
        if multiplier:
            # 计算乘积
            result = amount * float(multiplier.strip('*'))
            input_str = f"${result:.2f}"
        input_str = f"${amount:.2f}"
      
    return input_str


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
            # 处理strout为纯数字结论，这里是一个特例，假设计算中只包含数字！！！！！！！！
            pattern = re.compile(r"\b\d+\.?\d*\b") # 匹配所有数字
            matches = pattern.findall(stdout)
            if matches:
                # 提取所有找到的数字
                amounts = [float(match) for match in matches]
                return amounts[0]
            return stdout
        else:
            answer = "python脚本无法运行"
    return answer

def get_sympy_calculate_result(input_str):
    log(f"计算表达式: {input_str}")
    input_str = formula_preprocessing(input_str) # 公式预处理，采用规则库
    log(f"计算表达式处理后: {input_str}")

    # 定义可能的符号变量，确保它们被识别为符号而不是字符串
    symbols = re.findall(r'[a-zA-Z]+', input_str)
    symbols = set(symbols)  # 去除重复项
    local_dict = {s: sp.symbols(s) for s in symbols}

    try:
        # 将字符串转换为sympy表达式 expr = sp.sympify(input_str)
        # 使用 locals 参数显式地将这些变量定义为符号
        expr = sp.sympify(input_str, locals=local_dict)
        # 计算表达式
        result = expr
        # 化简表达式
        simplified_expr = sp.simplify(result)
        log(f"化简结果: {simplified_expr}")
        # 检查结果是否为布尔值
        if isinstance(simplified_expr, bool):  # 直接使用 Python 的内建类型 bool
            return simplified_expr
        try:
            # 如果是数学表达式，返回计算结果
            actual_result = simplified_expr.evalf()
            log(f"计算结果: {actual_result}")
            return actual_result
        except Exception as e:
            logging.error(f"无法计算<< {simplified_expr} >>: {str(e)}")
            actual_result = simplified_expr
            # actual_result = get_llm_calculate_result(simplified_expr)
            return actual_result
    except Exception as e:
        simplified_expr = input_str
        # actual_result = get_llm_calculate_result(simplified_expr)
        actual_result = simplified_expr
        logging.error(f"无法化简<< {input_str} >>: {str(e)}")
        
    return actual_result

def check_calculation(input_str):
    # 使用正则表达式查找计算表达式和结果
    pattern = r"<<(.+?)=(.+?)>>" # <>是必须的, =是必须的
    # pattern = r"<<?(.+?)=(.+?)>>?" # <>是可选的
    matches = re.findall(pattern, input_str)

    # 初始化 expected_result
    expected_result = None

    # 遍历所有匹配项进行检查
    for expr, expected_result in matches: # expr变量会接收表达式的内容（如"20*40"），而expected_result变量会接收表达式的结果（如"800"）。
        log(f"表达式: {expr}, 期望结果: {expected_result}")
        # 为什么能根据=号分割，因为=号是必须的
        # 去除头尾的 <<
        expr = expr.lstrip("<")
        # 如果还存在=，保留=前面的，如果不存在=，那就是其本身
        expr = expr.split("=")[0]
        # 去除头尾的 >>
        expected_result = expected_result.rstrip(">")
        # 如果还存在-，则保留=后面的
        expected_result = expected_result.split("=")[-1]
        # 使用 sympy 计算表达式的结果
        actual_result = get_sympy_calculate_result(expr)
        expected_result = get_sympy_calculate_result(expected_result)
        log(f"实际结果: {actual_result}, 期望结果: {expected_result}")
        # 比较实际结果和期望结果
        if actual_result != expected_result: # sympify(expected_result).evalf()是将expected_result转换为sympy对象并计算其值，evalf()方法返回计算结果。
            # print(f"计算错误: {expr} = {actual_result}, 期望结果: {expected_result}")
            return 0, f"{actual_result}"

    # 如果所有计算都正确，则返回 True
    return 1, f"{expected_result}"

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