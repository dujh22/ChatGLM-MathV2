import os
import json
import re

from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
from tqdm import tqdm

from get_data_for_codeTest import get_data_for_codeTest
from Step1_SplitByRow_forMathShepherd import Step1_SplitByRow_forMathShepherd
from Step2_IsCalculationOrReasoning import Step2_IsCalculationOrReasoning
from Step3_JudgmentStepCalculatedCorrectly import Step3_JudgmentStepCalculatedCorrectly, replace_calculated_result, llm_response
from Check1_JsonlVisualization import Check1_JsonlVisualization
from Check2_CalculateAccuracy import Check2_CalculateAccuracy


# 判断单步推理是否正确
def check_reasoning(per_step, content, question, history):
    for i in range(10):
        try:
            # 历史信息的构造
            historys = ""
            for step, info in history.items():
                temp_content = info["content"]
                if len(info["JudgmentStepCalculatedCorrectly"]) > 0:
                    # 找到info["content"]中错误的部分进行替换
                    # 主要是在字符串中找到<<80*2=1600>>1600比如，然后替换1600>>1600
                    temp_content = replace_calculated_result(temp_content, info["equation"], info["JudgmentStepCalculatedCorrectly"], info["StepCalculatedCorrectlyResult"])
                historys += f"{step}: {temp_content}\n"
            promt = f"""我正在尝试解决一个数学问题，具体问题是：“{question}”。\n\n 我目前采用的解题步骤如下：“{historys}” \n\n 现在我正在推理的步骤是：“{per_step}”，具体推理内容是：“{content}”。\n\n 请评估我的推理过程。如果我目前的推理步骤正确并且与问题相关，请回答“yes”。如果推理步骤错误或者不相关，请指出问题所在，并提供正确或更相关的推理步骤。"""
            prompt = f"""I am trying to solve a math problem, the specific question is: \"{question}\". \n\n The steps I have used so far to solve the problem are as follows: \"{historys}\" \n\n Now I am reasoning about the steps:\"{per_step}\" and the specific reasoning is:\"{content}\". \n\n Please evaluate my reasoning process. If my current reasoning steps are correct and relevant to the question, please answer "yes". If the reasoning steps are incorrect or irrelevant, please point out the problem and provide the correct or more relevant reasoning steps."""
            
            # response = gpt_generate(prompt)
            response = llm_response(prompt)  # 调用生成方法
            
            # 提取 response 的前三个字符，并将它们转换成小写来进行判断。
            # 注意也有可能是response中第一句话里面存在correct但不存在incorrect，所以需要加上or ()
            
            # 获取response的第一句话或者如果没有符号就是完整的response
            response_first_sentence = response.split(".")[0]

            if response_first_sentence[:3].lower() == "yes" or ("correct" in response_first_sentence.lower() and "incorrect" not in response_first_sentence.lower()):  
                return 1, response
            else:
                return 0, response
        except Exception as e:
            print(e)
    return 0, "Error"

# 串行处理
def process_jsonl_file(source_path, dest_path):
    with open(source_path, 'r', encoding='utf-8') as src_file, \
         open(dest_path, 'w', encoding='utf-8') as dest_file:
        for line in tqdm(src_file, desc='Processing'):
            data = json.loads(line)
            # 遍历每一步的解决方案
            if 'solution' in data:
                # 获取历史信息
                history = {}
                question = data['questions']
                for step, info in data['solution'].items(): # step变量会接收步骤的名称（如"Step 1"），而info变量会接收与这个步骤名称对应的字典值。
                    # 判断并添加新键
                    info['JudgmentStepReasoningCorrectly'], info['StepReasoningCorrectlyResult'] = check_reasoning(step, info['content'], question, history)
                    # 添加到历史信息中
                    history[step] = info
            # 将修改后的数据写回新的JSONL文件
            json.dump(data, dest_file, ensure_ascii=False)
            dest_file.write('\n')

# 并发处理
def process_line(line):
    data = json.loads(line)
    if 'solution' in data:
        # 获取历史信息
        history = {}
        question = data['questions']
        for step, info in data['solution'].items(): # step变量会接收步骤的名称（如"Step 1"），而info变量会接收与这个步骤名称对应的字典值。
            # 判断并添加新键
            info['JudgmentStepReasoningCorrectly'], info['StepReasoningCorrectlyResult'] = check_reasoning(step, info['content'], question, history)
            # 添加到历史信息中
            history[step] = info
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

# 实现每1000条数据保存一次，并且能够在之后的运行中从上次结束的地方继续开始处理
def process_jsonl_file_concurrent2(source_path, dest_path, chunk_size=1000, start_from=0):
    # 读取文件的所有行
    with open(source_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # 只处理从 start_from 开始的数据
    lines = lines[start_from:]

    results = []

   # 创建线程池进行并行处理
    with ThreadPoolExecutor(max_workers=50) as executor:
        # 从 start_from 开始批量处理数据
        for chunk_start in range(0, len(lines), chunk_size):
            chunk_end = min(chunk_start + chunk_size, len(lines))
            future_to_line = {executor.submit(process_line, line): line for line in lines[chunk_start:chunk_end]}
            results = []
            
            # 使用 tqdm 创建进度条
            with tqdm(total=len(future_to_line), desc=f'Processing lines {chunk_start+1} to {chunk_end}') as progress:
                for future in as_completed(future_to_line):
                    results.append(future.result())
                    progress.update(1)  # 更新进度条
            
            # 保存这一批数据到文件
            save_file_name = f"{dest_path}_{chunk_start+1}-{chunk_end}.jsonl"
            with open(save_file_name, 'w', encoding='utf-8') as f:
                    f.writelines(results)
            print(f"Data saved to {save_file_name}")
            
            # 可视化结果输出，用于debug
            Check1_JsonlVisualization(save_file_name)

            # 计算acc
            Check2_CalculateAccuracy(save_file_name)

def Step4_JudgmentStepReasoningCorrectly(source_folder, target_folder):
    
    print("Step4: 判断步骤是否推理正确……")

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    for filename in os.listdir(source_folder):
        if filename.endswith('.jsonl'):
            source_path = os.path.join(source_folder, filename)
            print("正在处理文件:", source_path)
            dest_path = os.path.join(target_folder, filename)
            # process_jsonl_file(source_path, dest_path)
            # process_jsonl_file_concurrent(source_path, dest_path)
            process_jsonl_file_concurrent2(source_path, dest_path)

# 使用方法：
def main():
    code_test_state = True
    base_folder = "F://code//github//ChatGLM-MathV2"
    # base_folder = "/workspace/dujh22/ChatGLM-MathV2"
    dataset_name = "peiyi9979_Math_Shepherd"
    source_folder = base_folder + '//raw_data//' + dataset_name

    mid_name = base_folder + '//data//' + dataset_name

    if code_test_state:
        get_data_for_codeTest(source_folder, new_folder_suffix='_for_codeTest', num_points=100)
        source_folder = source_folder + "_for_codeTest"

        target_folder1 = mid_name + "_for_codeTest" + "_Step1_SplitByRow_forMathShepherd"
        target_folder2 = mid_name + "_for_codeTest" + "_Step2_IsCalculationOrReasoning"
        target_folder3 = mid_name + "_for_codeTest" + "_Step3_JudgmentStepCalculatedCorrectly"
        target_folder4 = mid_name + "_for_codeTest" + "_Step4_JudgmentStepReasoningCorrectly"
    else:
        target_folder1 = mid_name + "_Step1_SplitByRow_forMathShepherd"
        target_folder2 = mid_name + "_Step2_IsCalculationOrReasoning"
        target_folder3 = mid_name + "_Step3_JudgmentStepCalculatedCorrectly"
        target_folder4 = mid_name + "_Step4_JudgmentStepReasoningCorrectly"

    Step1_SplitByRow_forMathShepherd(source_folder, target_folder1)
    Step2_IsCalculationOrReasoning(target_folder1, target_folder2)
    Step3_JudgmentStepCalculatedCorrectly(target_folder2, target_folder3)
    Step4_JudgmentStepReasoningCorrectly(target_folder3, target_folder4)

   

if __name__ == '__main__':
    main()