import subprocess
import re
from chatglm import ChatGLM

# 初始化 ChatGLM
chat_glm = ChatGLM()

def run_python(code, timeout=None):
    # 在子进程中执行Python代码
    result = subprocess.run(['python', '-c', code], capture_output=True, text=True, timeout=timeout)
    stdout = result.stdout
    stderr = result.stderr
    return stdout, stderr

def extract_glm_code(text):
    # 使用正则表达式提取代码块
    match = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""  # 如果没有找到匹配项，返回空字符串

def get_llm_calculate_result(input_str, question, content, history):
    # 构建给语言模型的提示
    # prompt = f"""我正在尝试解决一个数下问题，具体问题是：{question}。\n\n 我目前采用的解题步骤如下：{history}。\n\n 现在我正在计算的步骤是：{content}。\n\n 我需要计算一个数学表达式，这个表达式是：{input_str}。请帮我生成可执行的Python代码用于计算这个表达式，注意代码的最终输出应该是这个表达式的值或者化简后的表达式"""
    prompt = f"""I'm trying to solve a number down problem with the following specific question:{question} \n\n The steps I am currently using to solve the problem are: {history}. \n\n The step I am currently calculating is: {content}. \n\n I need to compute a math expression which is: {input_str}. Please help me generate executable Python code for calculating this expression, noting that the final output of the code should be either the value of this expression or the simplified expression."""
    for i in range(10):  # 尝试最多10次以获取有效的代码响应
        # 使用ChatGLM模型生成代码
        response = chat_glm.generate(prompt)
        # print("response:", response)
        code = extract_glm_code(response) # 假设响应即为代码
        stdout, stderr = run_python(code)
        if not stderr:  # 如果没有错误，返回结果
            return stdout, code
    return "Python scripts not running", ""  # 经过10次尝试失败后返回错误信息

def test_get_llm_calculate_result():
    # 定义一个测试案例
    input_str = "2 + 2"
    question = "What is the sum of 2 and 2?"
    content = "Add two numbers 2 + 2"
    history = "First determine the numbers to be added."
    
    # 使用测试案例调用函数
    result, code = get_llm_calculate_result(input_str, question, content, history)
    
    # 检查输出结果
    print("测试输出\n\n", result.strip())  # 去除额外空白以清晰显示
    print("\n\n生成的代码：\n\n", code)

# 运行测试
test_get_llm_calculate_result()
