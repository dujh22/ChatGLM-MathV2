import json

import sys
sys.path.append('F://code//github//ChatGLM-MathV2//shepherd_prm')
from shepherd_prm.query_api import standard_prompt_response, critic_math_problem, prepare_template
from shepherd_prm.prm_evaluate_process import generate_process, evaluate_process, select_math_data_by_rating2

# 设置模板路径
prompt_template_path = 'F://code//github//ChatGLM-MathV2//shepherd_prm//templates//criticllm_math_template.txt'


def api_both(question, response = None, answer = None):
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
    
    return data_path_pred_judge_aggregate

def main():
    question = "Janet pays $40/hour for 3 hours per week of clarinet lessons and $28/hour for 5 hours a week of piano lessons. How much more does she spend on piano lessons than clarinet lessons in a year?"
    result = api_both(question)
    result = json.dumps(result, indent=4, ensure_ascii=False)
    print(result)

if __name__ == '__main__':
    main()