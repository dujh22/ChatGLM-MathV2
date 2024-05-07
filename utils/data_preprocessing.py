import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
from Step1_SplitByRow_forMathShepherd import process_json_line

def data_preprocessing(input_file_path, new_folder_suffix, num_points, language):
    # 1. 从大数据中获得小批量数据
    with open(input_file_path, 'r', encoding='utf-8') as file:
        lines = [json.loads(line) for line in file]

        # 2. 用于从math_shepherd数据集转化获得原始测试数据集
        lines2 = []
        line_prompt = set() # 用于查重
        chinese_chars = re.compile(r'[\u4e00-\u9fff]+')  # 用于判断是否为中文
        for data in lines:
            # 将每行的内容从JSON转换为字典
            input_text = data['input']        
            # 提取问题和解决方案
            split_point = input_text.find("Step 1:")
            question = input_text[:split_point].strip()
            solution = input_text[split_point:].strip()        
            # 移除所有的“Step n: ”和“ки”
            solution = solution.replace("ки", "")  # 删除所有的ки
            for i in range(1, 200):  # 假设步骤不超过200
                solution = solution.replace(f"Step {i}: ", "")       
            # 使用正则表达式移除<< >>和其内部的内容
            solution = re.sub(r'<<.*?>>', '', solution)
            # 更新字典
            new_data = {}
            new_data['question'] = question
            new_data['solution'] = solution
            new_data['standardLabelAnswer'] = json.loads(process_json_line(json.dumps(data)))

            # 3. 查重与语言分析
            if question not in line_prompt:
                if chinese_chars.search(question) and language == 'zn': # 如果是中文
                    lines2.append(new_data)
                    line_prompt.add(question)
                elif chinese_chars.search(question) == None and language == 'en': # 如果是英文
                    lines2.append(new_data)
                    line_prompt.add(question)
                elif language != 'zn' and language != 'en': # 如果不是中文也不是英文
                    lines2.append(new_data)
                    line_prompt.add(question)
            
            # 4. 限制数量
            if len(lines2) >= num_points:
                break
        
        # 5. 保存数据
        base_folder_path = os.path.dirname(input_file_path) # 确定新文件夹的路径
        new_folder_path = base_folder_path + '_' + new_folder_suffix
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        output_file_path = new_folder_path + '/' + new_folder_suffix + '.jsonl'
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            for line in lines2:
                json.dump(line, outfile, ensure_ascii=False)
                outfile.write('\n')

def data_preprocessing2(input_file_path, output_file_path, num_points, language):
    # 1. 从大数据中获得小批量数据
    with open(input_file_path, 'r', encoding='utf-8') as file:
        lines = [json.loads(line) for line in file]

        # 2. 用于从math_shepherd数据集转化获得原始测试数据集
        lines2 = []
        line_prompt = set() # 用于查重
        chinese_chars = re.compile(r'[\u4e00-\u9fff]+')  # 用于判断是否为中文
        for data in lines:
            # 将每行的内容从JSON转换为字典
            input_text = data['input']        
            # 提取问题和解决方案
            split_point = input_text.find("Step 1:")
            question = input_text[:split_point].strip()
            solution = input_text[split_point:].strip()        
            # 移除所有的“Step n: ”和“ки”
            solution = solution.replace("ки", "")  # 删除所有的ки
            for i in range(1, 200):  # 假设步骤不超过200
                solution = solution.replace(f"Step {i}: ", "")       
            # 使用正则表达式移除<< >>和其内部的内容
            solution = re.sub(r'<<.*?>>', '', solution)
            # 更新字典
            new_data = {}
            new_data['question'] = question
            new_data['solution'] = solution
            new_data['standardLabelAnswer'] = json.loads(process_json_line(json.dumps(data)))

            # 3. 查重与语言分析
            if question not in line_prompt:
                if chinese_chars.search(question) and language == 'zn': # 如果是中文
                    lines2.append(new_data)
                    line_prompt.add(question)
                elif chinese_chars.search(question) == None and language == 'en': # 如果是英文
                    lines2.append(new_data)
                    line_prompt.add(question)
                elif language != 'zn' and language != 'en': # 如果不是中文也不是英文
                    lines2.append(new_data)
                    line_prompt.add(question)
            
            # 4. 限制数量
            if len(lines2) >= num_points:
                break
        
        # 5. 保存数据
        base_folder_path = os.path.dirname(output_file_path) # 确定新文件夹的路径
        if not os.path.exists(base_folder_path):
            os.makedirs(base_folder_path)
        
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            for line in lines2:
                json.dump(line, outfile, ensure_ascii=False)
                outfile.write('\n')

def main():
    if len(sys.argv) > 4:
        # 输入文件路径
        input_file_path = sys.argv[1]
        # 输出文件路径后缀
        output_file_path = sys.argv[2]
        # 输出文件数量
        num_points = int(sys.argv[3])
        # 语言
        language = sys.argv[4]
        data_preprocessing2(input_file_path, output_file_path, num_points, language)
    else:
        # 输入文件路径
        input_file_path = 'F://code//github//ChatGLM-MathV2//raw_data//peiyi9979_Math_Shepherd//math-shepherd.jsonl'
        # 输出文件路径后缀
        new_folder_suffix = 'math_shepherd_test_data100'
        # 输出文件数量
        num_points = 100
        # 语言
        language = 'en'
        # 调用函数
        data_preprocessing(input_file_path, new_folder_suffix, num_points, language)

if __name__ == "__main__":
    main()