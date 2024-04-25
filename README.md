# ChatGLM-MathV2：前向自动标注与后向评分反馈结合进行计算过程奖励

大模型在求解数学问题时，给出的回答通常存在各种计算或推理错误。

为了进一步提升大模型求解数学问题的准确性和鲁棒性，本项目通过详尽的pipeline设计，完成了针对大模型数学能力提升用数据集的自动化制备流程。

具体包括三个部分：分别是模型后向评分反馈、模型过程预测标注 和 模型前向自动标注。

详细pipeline见下图：

![whiteboard_exported_image](png/4.png)

## 1. 项目配置

1. 本项目对python环境无严格的版本要求，采用常用的环境即可

2. 进行必要包安装

   ```
   pip install -r requirements.txt
   ```

## 2. 使用说明

### 2.1 最简单的使用方式：调用api

不需要考虑其他事情，只需要简单地运行：

```shell
python api_both.py
```

#### 2.1.1 需要关注的文件

| 文件名称    | 文件说明                                  | 进一步说明 |
| ----------- | ----------------------------------------- | ---------- |
| api_both.py | 这是核心文件，可模仿main函数完成api的调用 | 见下       |
| config.py   | 记录了LLM的API密钥和基本URL               |            |
| chatglm.py  | chatglm调用文件                           |            |

注意需要设置相应的环境变量：共有两个部分。

1. 最开头这两行用于命令行测试，一般不需要打开，如果需要查看api执行过程的详细信息，则打开这两行

   ```python
   import hunter # 用于调试
   hunter.trace(module=__name__) # 用于调试
   ```

2. 设置调用LLM的相关信息。请根据具体情况进行调整，注意llm_response函数名和传入参数、返回值不可更改，否则影响api.py运行

   ```python
   # 该部分用于设置调用的LLM相关信息
   import config # 记录了密钥等实际值
   import openai
   # 设定API密钥和基本URL
   openai.api_key = config.GPT_API_KEY
   openai.api_base = config.GPT_BASE_URL
   from chatglm import ChatGLM
   ChatGLM = ChatGLM()
   USE_GLM_OR_GPT = 'glm'
   # 这里设置使用的llm进行生成，注意在本项目中只有这里一个地方进行相关设置
   def llm_response(prompt, use_glm_or_gpt = USE_GLM_OR_GPT):
       response = "ERROR for LLM"
       for i in range(10):
           if use_glm_or_gpt == 'glm':
               try:
                   response = ChatGLM.generate(prompt)
                   return response
               except:
                   continue
           else:
               try:
                   # 构造messages
                   messages = [{"role": "user", "content": prompt}]
                   # 调用GPT接口
                   # model = "gpt-3.5-turbo"
                   model = "gpt-4-1106-preview"
                   chat_completion = openai.ChatCompletion.create(model=model, messages = messages)
                   response = chat_completion.choices[0].message.content
                   return response
               except:
                   continue
       return response
   ```

在api_both.py的核心函数api中，有一部分可以自适应打开关闭：【可选】

```
def api_both(question, response = None, answer = None):
    ……

    # 如果全量输出，则关闭下面一行，否则只输出必要信息【可选】
    # out_data = postprocess(data4)

    # 如果有到导出文件的必要，可打开下面一行【可选】
    out_to_file(out_data)

    # 返回处理后的数据
    return out_data
```

#### 2.1.2 字段说明

##### 传入字段

```json
{
    "question":"问题", # 一个英文字符串
    "response":"针对问题LLM的响应", # 一个英文字符串（可选）
    "answer":"针对问题的参考答案" # 一个英文字符串（可选）
}
```

##### 主要传出字段

```json
{
  
}
```









### 2.2 可debug的一般使用方式：结合本地文件系统调用api

如果希望对中间过程进行输出，并进行全面跟踪，推荐这种方式

```shell
python pipeline_function.py
```

#### 2.2.1 需要关注的文件

| 文件名称                                 | 文件说明                                                     | 进一步说明 |
| ---------------------------------------- | ------------------------------------------------------------ | ---------- |
| pipeline_function.py                     | 这是核心文件，main函数中可选择采用api还是pipeline的形式，2.2节指这里采用api的形式 | 见下       |
| Step1_SplitByRow.py                      | 步骤一：数据按行拆分为步，识别计算公式（注意，如果针对对应的数据集，建议实现对应的预处理脚本，比如Step1_SplitByRow_forMathShepherd.py就是针对MathShepherd数据集的进一步实现） |            |
| Step2_IsCalculationOrReasoning.py        | 步骤二：判断单步是计算步还是推理步                           |            |
| Step3_JudgmentStepCalculatedCorrectly.py | 步骤三：针对计算步进行详细自动化标注                         |            |
| Step4_JudgmentStepReasoningCorrectly.py  | 步骤四：针对推理步进行详细自动化标注                         |            |
| Check1_JsonlVisualization.py             | Step3&4支撑性文件，用于针对jsonl输出可视化为csv格式          |            |
| Check2_CalculateAccuracy.py              | Step4支撑性文件，用于计算自动标注的ACC准确率                 |            |

#### 2.2.2 具体流程说明

所有流程的中间结果会存在本项目所在文件夹下的data和raw_data子文件夹中，可进行具体查看，方便debug和Acc计算比较

##### 2.2.2.1 步骤一：数据按行拆分为步，识别计算公式

这里值得说明的是，Step1_SplitByRow.py只提供了基础的数据拆分原则：比如按照句号或者换行符。针对具体的数据集，需要更具体的实现，比如Step1_SplitByRow_forMathShepherd.py就是针对MathShepherd数据集的进一步实现

##### 2.2.2.1 步骤二：判断单步是计算步还是推理步

判断单步是包括计算公式的计算步骤还是不包括计算公式的推理步骤

##### 2.2.2.1 步骤三：针对计算步进行详细自动化标注

这里会对每一个计算步进行详细的标注，Check1_JsonlVisualization.py支持对标注结果进行二维横纵向对比

##### 2.2.2.1 针对推理步进行详细自动化标注

这里会对每一个推理步进行详细的标注，Check2_CalculateAccuracy.py支持输出最终的Acc准确性结果

### 2.3 推荐方式：并发pipeline

如果希望全面使用该项目算法，优化加速整体调用流程，推荐这种方式

如果希望对中间过程进行输出，并进行全面跟踪，推荐这种方式

```shell
python pipeline_function.py
```

#### 2.3.1 需要关注的文件

| 文件名称                        | 文件说明                                                     | 进一步说明 |
| ------------------------------- | ------------------------------------------------------------ | ---------- |
| pipeline_function.py            | 这是核心文件，main函数中可选择采用api还是pipeline的形式，2.3节指这里采用pipeline的形式 | 见下       |
| data_download.py                | Step1支撑性文件，数据集下载脚本，用于针对data_urls.txt中给定的huggingface上数据集进行自动化下载 |            |
| get_data_for_codeTest.py        | Step1支撑性文件，小样本处理脚本，用于简化数据集大小，输出更小的数据集，方便进行项目的代码测试 |            |
| highlight_equations.py          | Step3支撑性文件，公式高亮脚本，用于识别步骤中的潜在公式      |            |
| run_python_func.py              | Step3支撑性文件，python代码自动化运行脚本，用于运行python代码 |            |
| use_gpt_api_for_glm_generate.py | Step3&4支撑性文件，用于调用GPT进行数据标注与校验             |            |

#### 2.3.2 具体流程说明（对2.2.2的补充）

##### 2.3.2.1 数据集的下载

* 如果有数据集下载需要，https://pypi.org/project/pycrawlers/ 下载后将其中pycrawlers放到代码同一级目录下（本项目已经包含这一文件夹，可以不二次执行）
* 参照data_urls.txt进行修改
* 多次运行 `python data_download.py`

##### 2.3.2.2 针对Step3&4的并发实现

在非API调用的情景下，默认step3和step4会采用并发完成，目前并发参数max_workers设置为10，可在脚本中找到相应位置进行设置

```python
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
```

