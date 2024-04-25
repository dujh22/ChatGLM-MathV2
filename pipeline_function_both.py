import os
import json
import sys
sys.path.append('F://code//github//ChatGLM-MathV2//shepherd_prm')
from shepherd_prm.query_api import standard_prompt_response, critic_math_problem, prepare_template, build_training_file
from shepherd_prm.prm_evaluate_process import generate_process, evaluate_process, select_math_data_by_rating, select_math_data_by_rating2
from get_data_for_codeTest import get_data_for_codeTest
from Step1_SplitByRow import Step1_SplitByRow
from Step1_SplitByRow_forMathShepherd import Step1_SplitByRow_forMathShepherd
from Step2_IsCalculationOrReasoning import Step2_IsCalculationOrReasoning
from Step3_JudgmentStepCalculatedCorrectly import Step3_JudgmentStepCalculatedCorrectly
from Step4_JudgmentStepReasoningCorrectly import Step4_JudgmentStepReasoningCorrectly

from functools import partial  # 从functools模块导入partial函数，用于固定函数的部分参数

# 设置模板路径
prompt_template_path = 'F://code//github//ChatGLM-MathV2//shepherd_prm//templates//criticllm_math_template.txt'

# 获取项目所在位置
base_folder = os.path.dirname(os.path.abspath(__file__))
base_folder = base_folder.replace("\\", "//")


def pipeline_api(question, response = None, answer = None):
    data = data = {"questions": question}
    
    # 如果提供了回答，就用回答作为回答, 否则生成回答
    if response:
        data["response"] = response
    else:
        data["response"] = standard_prompt_response(
            data, 
            backbone = "tgi",
            prompt_key = "questions",
            response_key = "response"
        )

    # 如果没有提供标准答案
    if answer == None:
        data["answer"] = "no reference answer"

    # 后向结果评分反馈
    PROMPT_TEMPLATE = prepare_template(prompt_template_path) # 准备提示模板
    data_back = critic_math_problem(
        data, 
        backbone= "chatglm_platform",
        prompt_key = "questions",
        reference_key = "answer",
        response_key = "response",
        PROMPT_TEMPLATE = PROMPT_TEMPLATE
    )

    # 前向过程路径预测
    data_path_pred = generate_process(
        data_back,
        prompt_key = "questions",
        response_key = "response"
    )
    
    # 前向过程路径评估
    data_path_pred_judge = evaluate_process(
        data_path_pred,
        backbone = "chatglm_platform",
        prompt_key = "questions",
        process_response_key = "generated_paths",
        reference_answewr_key = "answer",
        PROMPT_TEMPLATE = PROMPT_TEMPLATE
    )

    data_path_pred_judge_aggregate = select_math_data_by_rating2(
        data_path_pred_judge
    )

    # 构造数据
    line = {
        "questions": data_path_pred_judge_aggregate['questions'],
        "solution": data_path_pred_judge_aggregate['response'],
        "dataset": 'test'
    }
    # 保存到指定路径
    dataset_name = "api_both" # 数据集名称
    source_folder = base_folder + '//raw_data//' + dataset_name # 原始数据集所在位置
    mid_name = base_folder + '//data//' + dataset_name + '//' + dataset_name # 中间文件所在位置
    target_folder1 = mid_name + "_Step1_SplitByRow"
    target_folder2 = mid_name + "_Step2_IsCalculationOrReasoning"
    target_folder3 = mid_name + "_Step3_JudgmentStepCalculatedCorrectly"
    target_folder4 = mid_name + "_Step4_JudgmentStepReasoningCorrectly"
    Step1_SplitByRow(source_folder, target_folder1, line)
    Step2_IsCalculationOrReasoning(target_folder1, target_folder2)
    Step3_JudgmentStepCalculatedCorrectly(target_folder2, target_folder3)
    Step4_JudgmentStepReasoningCorrectly(target_folder3, target_folder4)
    # 读取结果并返回
    result = {}
    # 识别target_folder4下的jsonl文件
    for root, dirs, files in os.walk(target_folder4):
        for file in files:
            if file.endswith(".jsonl"):
                source_file_path = os.path.join(root, file)
                with open(source_file_path, 'r', encoding='utf-8') as src_file:
                    for line in src_file:
                        data = json.loads(line)
                        result = data


    output_data = data_path_pred_judge_aggregate
    output_data['solution'] = result['solution']
    
    return output_data

def pipeline_file():
    # case 1

    prompt_template_path = 'F://code//github//ChatGLM-MathV2//shepherd_prm//templates//criticllm_math_template.txt'
    prompt_key = "question"
    response_key = "response"
    reference_key = "solution"

    input_file_path = "F://code//github//ChatGLM-MathV2//data//test_data//test_data0.jsonl"
    backbone = "tgi"

    # 构建训练文件
    build_training_file(
        input_file=input_file_path,
        output_file=input_file_path.replace(".jsonl", f"_{backbone}.jsonl"),  # 设置输出文件路径
        worker_func=partial(
            standard_prompt_response, 
            skip_response=False, 
            skip_generated=False, 
            backbone=backbone, 
            prompt_key=prompt_key, 
            response_key=response_key
        ),
        is_glm=False,
        num_process=10  # 设置是否使用GLM模型和处理数量
    )

    # case 2
    input_file_path = "F://code//github//ChatGLM-MathV2//data//test_data//test_data0_tgi.jsonl"
    backbone = "chatglm_platform"

    PROMPT_TEMPLATE = prepare_template(prompt_template_path)  # 准备提示模板
    # 构建训练文件
    build_training_file(
        input_file=input_file_path,
        output_file=input_file_path.replace(".jsonl", "_math_critic.jsonl"),  # 设置输出文件路径
        worker_func=partial(
            critic_math_problem, 
            backbone=backbone, 
            prompt_key=prompt_key, 
            reference_key=reference_key,
            response_key=response_key,
            PROMPT_TEMPLATE = PROMPT_TEMPLATE
        ),
        is_glm=False, 
        num_process=10  # 设置是否使用GLM模型和处理数量
    )

    # case 3

    input_file_path = "F://code//github//ChatGLM-MathV2//data//test_data//test_data0_tgi.jsonl"
    backbone = "tgi" 

    build_training_file(
        input_file=input_file_path,  # 输入文件
        output_file=input_file_path.replace(".jsonl", "_path.jsonl"),  # 输出文件路径
        worker_func=partial(
            generate_process,  # 指定工作函数
            prompt_key=prompt_key,  # 传递prompt_key参数
            response_key=response_key  # 传递response_key参数
        ),
        is_glm=False  # 指定是否使用GLM模型
    )

    # case 4
    input_file_path = "F://code//github//ChatGLM-MathV2//data//test_data//test_data0_tgi_path.jsonl"
    backbone = "chatglm_platform"
    process_response_key = "generated_paths"
    reference_answewr_key = "solution"

    build_training_file(
        input_file=input_file_path,  # 输入文件
        output_file=input_file_path.replace(".jsonl", "_math_critic.jsonl"),  # 输出文件路径
        worker_func=partial(
            evaluate_process,  # 指定工作函数
            backbone=backbone,  # 传递模型参数
            prompt_key=prompt_key,  # 传递prompt_key参数
            process_response_key=process_response_key,  # 传递response_key参数
            reference_answewr_key=reference_answewr_key,
            PROMPT_TEMPLATE = PROMPT_TEMPLATE
        ),  # 传递reference_key参数
        is_glm=False  # 指定是否使用GLM模型
    )

    select_math_data_by_rating(
        input_file=input_file_path.replace(".jsonl", "_math_critic.jsonl"),
        output_file=input_file_path.replace(".jsonl", "_math_critic2.jsonl")
    )  # 选择评分数据

    # case 5
    is_test = True # 小样本开关：如果为True，则只处理少量数据
    test_num = 10

    dataset_name = "peiyi9979_Math_Shepherd" # 数据集名称
    source_folder = base_folder + '//raw_data//' + dataset_name # 原始数据集所在位置
    mid_name = base_folder + '//data//' + dataset_name # 中间文件所在位置

    if is_test:
        get_data_for_codeTest(source_folder, new_folder_suffix='_for_codeTest', num_points=test_num)
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

    if dataset_name == "peiyi9979_Math_Shepherd":
        Step1_SplitByRow_forMathShepherd(source_folder, target_folder1) 
    else:
        Step1_SplitByRow(source_folder, target_folder1)
    
    Step2_IsCalculationOrReasoning(target_folder1, target_folder2)
    Step3_JudgmentStepCalculatedCorrectly(target_folder2, target_folder3)
    Step4_JudgmentStepReasoningCorrectly(target_folder3, target_folder4)


def main():
    type = 'api'
    if type == 'api':
        question = "Janet pays $40/hour for 3 hours per week of clarinet lessons and $28/hour for 5 hours a week of piano lessons. How much more does she spend on piano lessons than clarinet lessons in a year?"
        result = pipeline_api(question)
        result = json.dumps(result, indent=4, ensure_ascii=False)
        print(result)
    else:
        pipeline_file()

if __name__ == '__main__':
    main()