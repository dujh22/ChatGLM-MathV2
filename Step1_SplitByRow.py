import json
import os
import re
from tqdm import tqdm
from highlight_equations import highlight_equations

def process_json_line(line):
    # 加载原始JSON
    data = json.loads(line)

    # 初始化新的JSON格式
    new_json = {
        "questions": data["questions"],
        "solution": {},
        "dataset": data["dataset"],
    }

    # 判断solution中的换行符数量
    newline_count = data['solution'].count('\n')

    if newline_count >= 2:
        # 如果不少于2个换行符，按照换行符切割
        solutions = data['solution'].split('\n')
    else:
        # 否则，使用正则表达式按句号切割非小数点
        solutions = re.split(r'(?<=[^.0-9])\.(?=[^0-9])', data['solution'])

    # 处理每个解决方案部分
    for i, solution in enumerate(solutions):
        if solution.strip():  # 确保切割后的文本不为空
            new_json["solution"][f"Step {i+1}"] = {
                "content": solution.strip(),
                "label": 1  # 默认标签为1
            }

    # 处理每个解决方案部分的数学公式高亮
    for step, info in new_json["solution"].items():
        temp_content = info["content"]
        info["content"] = highlight_equations(temp_content)
            
    # 返回新的JSON格式
    return json.dumps(new_json, ensure_ascii=False)

def process_files(source_folder, target_folder):
    # 确保目标文件夹存在
    os.makedirs(target_folder, exist_ok=True)

    # 遍历文件夹中的所有JSONL文件
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.endswith(".jsonl"):
                source_file_path = os.path.join(root, file)
                target_file_path = os.path.join(target_folder, file)
                
                with open(source_file_path, 'r', encoding='utf-8') as src_file, \
                     open(target_file_path, 'w', encoding='utf-8') as tgt_file:
                    for line in tqdm(src_file, desc='Processing'):
                        processed_line = process_json_line(line)
                        tgt_file.write(processed_line + '\n')

def create_jsonl_file(source_folder, data={}):
    # 确保源文件夹存在，如果不存在则创建
    if not os.path.exists(source_folder):
        os.makedirs(source_folder, exist_ok=True)
        
        # 完整的文件路径
        file_path = os.path.join(source_folder, 'api.jsonl')
        
        with open(file_path, 'w', encoding='utf-8') as file:
            if not data:
                # 提示用户输入每个 JSON 对象的数据
                questions = input("请输入问题部分内容: ")
                solution = input("请输入解决方案部分内容: ")
                dataset = input("请输入数据集名称: ")
                
                # 创建 JSON 数据结构
                data = {
                    "questions": questions,
                    "solution": solution,
                    "dataset": dataset
                }
            else:
                # 将数据写入文件（每个 JSON 对象为一行）
                json.dump(data, file, ensure_ascii=False)
                file.write('\n')  # 换行，以便每个 JSON 对象占据一行
            
def Step1_SplitByRow(source_folder, target_folder, data):
    create_jsonl_file(source_folder, data)
    process_files(source_folder, target_folder)

def main():
    source_folder = 'F://code//github//ChatGLM-MathV2//raw_data//pipeline_test'
    target_folder = 'F://code//github//ChatGLM-MathV2//data//pipeline_test_step1'
    Step1_SplitByRow(source_folder, target_folder)

if __name__ == '__main__':
    main()
