import json  # 导入json模块，用于处理JSON数据
import argparse  # 导入argparse模块，用于处理命令行参数
from functools import partial  # 从functools模块导入partial，用于固定函数的部分参数
import re  # 导入re模块，用于正则表达式操作
import requests  # 导入requests模块，用于进行HTTP请求
import random  # 导入random模块，用于生成随机数

from query_api import build_training_file, critic_math_problem, prepare_template  # 从query_api模块导入三个函数


def query_tgi_completion(prompt):
    '''
        这段 Python 代码会配置并向文本生成 API 发送 POST 请求，其中的特定参数会影响生成文本的风格和多样性。这些配置的温度和 top_p 值各不相同，会影响文本生成的确定性或创造性。随机模块用于在这些配置之间进行选择，从而在生成过程中引入可变性。这种设置尤其适用于需要可控和多样化文本输出的应用，例如自动内容生成或聊天机器人。
    '''
    url = "http://xxx:8080/generate"  # 设置API的URL地址
    configs = [
        {"temperature": 0.1, "top_p": 0.7},  # 配置列表第一个配置项，温度较低，生成内容较为保守
        {"temperature": 0.9, "top_p": 0.9},  # 配置列表第二个配置项，温度较高，生成内容较为多样
    ]
    if random.randint(0, 5) == 0:  # 随机决定使用哪个配置项，有1/6的概率使用第一个配置
        config = configs[0]
    else:
        config = configs[1]  # 默认情况下使用第二个配置
        
    payload = {  # 定义请求的数据载荷
        "best_of": 1,  # 指定返回的最佳结果数量为1
        "decoder_input_details": False,  # 是否返回解码器输入的详细信息
        "details": False,  # 是否返回额外的详细信息
        "do_sample": True,  # 启用随机采样生成文本，使输出更加多样
        "max_new_tokens": 2048,  # 指定生成的最大令牌数量
        "seed": random.randint(0, 100000),  # 随机种子，用于生成结果的可复现性
        "temperature": config["temperature"],  # 从选定的配置中获取温度参数
        "top_p": config["top_p"],  # 从选定的配置中获取top_p参数，控制生成的集中性
        "stop": ["", "", ""]  # 设置终止符，这里为空，不指定特定终止符
    }
    requests.post(url, json=payload, verify=False)  # 发送POST请求到服务器，携带定义好的数据载荷，verify=False表示不验证SSL证书


def split_response(response): # 使用正则表达式按换行符分割响应文本
    steps = re.split(r"\n", response)
    return steps
    
def generate_process(x, prompt_key, response_key, num_path=3, backbone="glm-code-v3"):
    '''
        该函数处理包含提示和响应详细信息的给定字典 x，为响应的每个步骤生成扩展路径。它使用辅助函数 query_tgi_completion，尝试生成扩展路径，每一步最多可生成三次，以确保稳健的错误处理和重试机制。这种方法适用于需要根据先前步骤顺序生成内容的场景，例如为机器学习模型或自动应答系统创建训练数据。
    '''
    prompt = x[prompt_key]  # 从字典x中获取提示信息
    response = x[response_key]  # 从字典x中获取响应信息
    output = []  # 初始化输出列表，用来存储所有生成的扩展路径
    steps = split_response(response)  # 使用split_response函数分割响应文本成多个步骤

    # 遍历每一个步骤
    for idx in range(len(steps)):
        extension_path = []  # 为当前步骤初始化扩展路径列表
        
        # 为当前步骤生成指定数量的扩展路径
        for _p in range(num_path):
            _step = "\n".join(steps[:idx+1])  # 将当前步骤之前的所有步骤连接成一个新的查询提示
            query_prompt = f"\n{prompt}\n{_step}"  # 构造新的查询提示，包括原始提示和当前步骤
            
            result = None  # 初始化结果变量
            for _ in range(3):  # 最多尝试三次获取生成结果
                try:
                    result = query_tgi_completion(query_prompt)  # 调用query_tgi_completion函数尝试获取生成结果
                    if result is not None:  # 如果成功获取到结果，终止循环
                        break
                except Exception as e:
                    continue  # 如果在尝试过程中发生异常，忽略异常，继续尝试
            if result is None:
                continue  # 如果三次尝试后仍未获取到结果，跳过当前路径的生成
            
            extension_path.append(result)  # 将获取到的结果添加到扩展路径列表

        output.append({  # 将当前步骤的所有扩展路径添加到输出列表
            "step": _step,
            "extension": extension_path
        })

    x["generated_paths"] = output  # 将生成的所有扩展路径存储在输入字典x中的"generated_paths"键下
    return x  # 返回更新后的字典x

def evaluate_process(x, prompt_key="prompt", process_response_key="generated_paths", reference_answewr_key="reference", max_retry=3):
    '''
        该功能通过使用批判函数根据参考答案对每个回复步骤进行评分来评估生成文本路径的质量，通常用于评估数学问题或类似内容，其正确性可以客观判断。它根据分数计算软标签和硬标签，其中软标签是二进制结果（分数高于阈值）的平均值，而硬标签则表示大部分分数是否通过了阈值。这种评估在教育软件、自动辅导系统或其他需要对生成的回复进行反馈的应用中特别有用。
    '''
    generated_paths = x[process_response_key]  # 从字典x中获取生成的路径数据

    # 遍历所有生成的路径
    for path in generated_paths:
        step_paths = path["extension"]  # 获取每个路径的扩展步骤列表
        ratings = []  # 初始化评分列表

        # 为每个扩展步骤进行评分
        for step_path in step_paths:
            temp_item = {
                prompt_key: x[prompt_key],  # 提取提示信息
                "response": step_path,  # 提取响应信息
                reference_answewr_key: x[reference_answewr_key]  # 提取参考答案信息
            }
            result = critic_math_problem(  # 调用批评函数对每个响应进行评分
                temp_item,
                backbone="chatglm_platform",  # 指定使用的模型后端
                prompt_key=prompt_key,
                response_key="response",
                reference_key=reference_answewr_key
            )
            rating = result["critic_result"][0]["rating"]  # 从结果中获取评分
            ratings.append(rating)  # 将评分添加到评分列表

        path["ratings"] = ratings  # 将评分列表存储在路径信息中
        ratings_binary = [1 if x >= 8 else 0 for x in ratings]  # 将评分转换为二进制标签（8分以上为1，否则为0）
        path["soft_label"] = sum(ratings_binary) / len(ratings_binary)  # 计算软标签，即平均值
        path["hard_label"] = 1 if path["soft_label"] >= 0.5 else 0  # 根据软标签计算硬标签，平均值大于等于0.5则为1，否则为0

    x[process_response_key] = generated_paths  # 将更新后的生成路径存回字典x
    return x  # 返回更新后的字典x

def select_math_data_by_rating(input_file):
    '''
        该函数处理一组数学问题（或其他类似的评价任务），根据评分选择或过滤这些问题。它支持以文件路径或直接以数据形式输入。该函数根据给定的下限计算每个项目的平均分数和通过率，并用计算出的分数和选择指标更新每个项目。在需要自动评分和反馈以评估和改进学习材料或算法的教育或测试环境中，这一过程尤其有用。
    '''
    if isinstance(input_file, str):  # 检查输入是否为字符串类型的文件路径
        data = [json.loads(x) for x in open(input_file)]  # 从文件读取每行并解析为JSON对象
    else:
        data = input_file  # 如果不是字符串，假设输入已经是数据列表

    def judge_scores(scores, lower_bound=7):
        avg_score = sum(scores) / len(scores)  # 计算所有评分的平均值
        above_bound = [1 if x >= lower_bound else 0 for x in scores]  # 生成一个列表，评分高于阈值的为1，否则为0
        return avg_score, sum(above_bound) / len(above_bound)  # 返回平均分和超过阈值的比例
    
    def func(x, lower_bound=8):
        results = x["critic_result"]  # 从每个样本中获取评价结果
        if len(results) == 0:
            return None  # 如果没有评价结果，则返回None
        ratings = [item["rating"] for item in results if isinstance(item["rating"], str)]  # 提取所有评分，确保评分是字符串格式
        ratings = [float(x) for x in ratings]  # 将所有评分转换为浮点数
        avg_score, pass_rate = judge_scores(ratings, lower_bound=lower_bound)  # 调用judge_scores计算平均分和通过率
        x["critic_scores"] = {  # 将计算结果存回样本中
            "ratings": ratings,
            "avg_score": avg_score,
            "pass_rate": pass_rate
        }
        return x
    
    processed = [func(x) for x in data if x is not None]  # 处理数据集中的每个样本，并排除None值
    return processed  # 返回处理后的数据列表



if __name__ == "__main__":
    # 创建命令行解析器
    parser = argparse.ArgumentParser()
    # 添加各种命令行参数
    parser.add_argument("--input_file", type=str, default=None)  # 指定输入文件路径
    parser.add_argument("--mode", type=str, default="response")  # 指定运行模式
    parser.add_argument("--backbone", type=str, default="gpt-3.5-turbo")  # 指定使用的模型
    parser.add_argument("--prompt_key", type=str, default=None)  # 指定提示键名
    # "gpt-4-1106-preview"  # 注释中提及可能使用的模型版本
    parser.add_argument("--skip_response", action="store_true", default=False)  # 是否跳过响应生成
    parser.add_argument("--skip_generated", action="store_true", default=False)  # 是否跳过已生成的响应
    parser.add_argument("--prompt_template", type=str, default=None)  # 指定提示模板
    parser.add_argument("--reference_key", type=str, default="answer")  # 指定参考答案键名
    parser.add_argument("--response_key", type=str, default="response")  # 指定响应键名
    args = parser.parse_args()  # 解析命令行参数
    
    # 根据指定的模式进行相应的操作
    if args.mode == "generation":
        build_training_file(
            input_file=args.input_file,  # 输入文件
            output_file=args.input_file.replace(".jsonl", "_path.jsonl"),  # 输出文件路径
            worker_func=partial(
                generate_process,  # 指定工作函数
                prompt_key=args.prompt_key,  # 传递prompt_key参数
                response_key=args.response_key  # 传递response_key参数
            ),
            is_glm=False  # 指定是否使用GLM模型
        )
    elif args.mode == "critic":
        build_training_file(
            input_file=args.input_file,  # 输入文件
            output_file=args.input_file.replace(".jsonl", "_math_critic.jsonl"),  # 输出文件路径
            worker_func=partial(
                critic_math_problem,  # 指定工作函数
                backbone=args.backbone,  # 传递模型参数
                prompt_key=args.prompt_key,  # 传递prompt_key参数
                response_key=args.response_key,  # 传递response_key参数
                reference_key=args.reference_key
            ),  # 传递reference_key参数
            is_glm=False  # 指定是否使用GLM模型
        )
