from tqdm import tqdm
import json
import os

def process_json_line(line):
    data = json.loads(line)
    new_data = {
        "questions": data["question"],
        "solution": data["response"],
    }
    return json.dumps(new_data, ensure_ascii=False)

def turn_response_and_solution(input_file_path, output_file_path):
    # 如果目标文件夹不存在，则创建
    if not os.path.exists(os.path.dirname(output_file_path)):
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    with open(input_file_path, 'r', encoding='utf-8') as src_file, open(output_file_path, 'w', encoding='utf-8') as tgt_file:
        for line in tqdm(src_file, desc='Processing'):
            processed_line = process_json_line(line)
            tgt_file.write(processed_line + '\n')



def main():
        
    input_file_path = 'F://code//github//ChatGLM-MathV2//data//test_data100//test_data100_tgi.jsonl'
    output_file_path = 'F://code//github//ChatGLM-MathV2//data//test_data100//front//test_data100.jsonl'

    turn_response_and_solution(input_file_path, output_file_path)

if __name__ == '__main__':
    main()