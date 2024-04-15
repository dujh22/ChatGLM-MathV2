import os
import json
import re
from use_gpt_api_for_glm_generate import gpt_generate

# 修正函数
# 1.在 content 字符串中查找被 << 和 >> 包围的表达式。
# 2.替换 = 后面直到 >> 的内容为 StepCalculatedCorrectlyResult 的值。
# 3.如果 >> 后的内容（如果存在）与 = 和 >> 之间的内容相同，则也将其替换为 StepCalculatedCorrectlyResult。
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

# 判断单步推理是否正确
def check_reasoning(content, backgroud):
    try:
        # 历史信息的构造
        history = f"question: {backgroud["question"]}\n"
        for step, info in backgroud.items():
            if step != "question":
                temp_content = info["content"]
                if info["JudgmentStepCalculatedCorrectly"] == 0:
                    # 找到info["content"]中错误的部分进行替换
                    # 主要是在字符串中找到<<80*2=1600>>1600比如，然后替换1600>>1600
                    temp_content = replace_calculated_result(temp_content, info["StepCalculatedCorrectlyResult"])
                history += f"{step}: {info['content']}\n"
        prompt = f"""判断给定的推理描述是否合理。描述如下：{content}, 如果信息不足，可参考历史信息。，具体如下：{history}。如果推理正确，只需要回答“yes”，否则请只回复正确的推理以及推理结果。"""
        response = gpt_generate(prompt)
        if responce == "yes":
            return 1, content
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
                history = {"question": data["question"]}
                for step, info in data['solution'].items(): # step变量会接收步骤的名称（如"Step 1"），而info变量会接收与这个步骤名称对应的字典值。
                    # 判断并添加新键
                    info['JudgmentStepReasoningCorrectly'], info['StepReasoningCorrectlyResult'] = check_reasoning(info['content'], history)
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
        history = {"question": data["question"]}
        for step, info in data['solution'].items(): # step变量会接收步骤的名称（如"Step 1"），而info变量会接收与这个步骤名称对应的字典值。
            # 判断并添加新键
            info['JudgmentStepReasoningCorrectly'], info['StepReasoningCorrectlyResult'] = check_reasoning(info['content'], history)
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

def Step4_JudgmentStepReasoningCorrectly(source_folder, target_folder):
    
    print("Step4: 判断步骤是否推理正确……")

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    
    for filename in os.listdir(source_folder):
        if filename.endswith('.jsonl'):
            source_path = os.path.join(source_folder, filename)
            print("正在处理文件:", source_path)
            dest_path = os.path.join(target_folder, filename)
            process_jsonl_file(source_path, dest_path)
            # process_jsonl_file_concurrent(source_path, dest_path)

# 使用方法：
def main():
    code_test_state = True
    base_folder = "F://code//github//ChatGLM-MathV2"
    dataset_name = "peiyi9979_Math_Shepherd"
    source_folder = base_folder + '//raw_data//' + dataset_name

    mid_name = base_folder + '//data//' + dataset_name

    if code_test_state:
        # get_data_for_codeTest(source_folder)
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

    # Step1_SplitByRow_forMathShepherd(source_folder, target_folder1)
    # Step2_IsCalculationOrReasoning(target_folder1, target_folder2)
    # Step3_JudgmentStepCalculatedCorrectly(target_folder2, target_folder3)
    Step4_JudgmentStepReasoningCorrectly(target_folder3, target_folder4)

if __name__ == '__main__':
    main()