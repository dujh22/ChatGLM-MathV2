import json

def all_alpha(str):
    if str == 'x': # 特例
        return False
    if all(temp.isalpha() for temp in str):
        return True
    if any(temp.isalpha() for temp in str):
        if any(temp.isdigit() for temp in str) == False:
            return True
    
    return False

def highlight_equations(text):
    # 预处理，在数字和字母之间加一个空格
    raw_text = text


    # 去除$
    text = text.replace('$', '')
    
    text2 = text
    text3 = ""
    
    i = 0
    while i < len(text2): 
        if text2[i].isdigit():
            if i + 1 < len(text2):
                if text2[i + 1].isdigit(): # 连续两个数字
                    text3 = text3 +text2[i]
                    i += 1
                elif text2[i + 1] == '.' and i + 2 < len(text2) and text2[i + 2].isdigit(): # 小数点后面是数字
                    text3 = text3 + text2[i] + text2[i + 1] + text2[i + 2]
                    i += 3
                elif text2[i + 1] == ')' or text2[i + 1] == '）': # 有括号
                    text3 = text3 + text2[i] + ')'
                    i += 2
                elif text2[i + 1] == '(' or text2[i + 1] == '（': # 有括号
                    if i + 2 < len(text2):
                        if text2[i + 2].isdigit():
                            text3 = text3 + text2[i] + " *( " + text2[i + 2]
                            i += 3
                        else:
                            text3 = text3 + text2[i]   + " ("
                            i += 2
                    else:
                       text3 = text3 + text2[i]
                       i += 2
                else:
                    text3 = text3 + text2[i] + ' '
                    i += 1
            else:
                text3 += text2[i]
                i += 1
        elif text2[i] in ['+', '-', '*', '/']:
            text3 = text3 + ' ' + text2[i] + ' '
            i += 1
        else: # 非数字
            if i + 1 < len(text2):
                if text2[i + 1].isdigit():
                    if text2[i] == '.':
                        if i - 1 >= 0:
                            if text3[i - 1].isdigit():
                                text3 = text3 + text2[i] + text2[i + 1]
                                i += 2
                            else:
                                text3 = text3 + text2[i] + ' ' + text2[i + 1]
                                i += 2
                        elif i == 0:
                            text3 = 0 + text2[i] + text2[i + 1]
                            i += 2
                    else: 
                        text3 = text3 + text2[i] + ' ' + text2[i + 1]
                        i += 2
                else:
                    text3 = text3 + text2[i]
                    i += 1
            else:
                text3 = text3 + text2[i]
                i += 1
    
    # 将连续的空格替换为1个
    temp_text = ""
    for i in range(0, len(text3)):
        if text3[i] == ' ':
            if i + 1 < len(text3):
                if text3[i + 1] == ' ':
                    continue
                else:
                    temp_text = temp_text + text3[i]
            else:
                continue
        else:
            temp_text = temp_text + text3[i]
    text3 = temp_text

    # 去寻找x, 如果其前后有数字，那么应该替换为*
    for i in range(0, len(text3) - 1):
        if text3[i] == 'x':
            if i - 1 > 0:
                if text3[i - 1].isdigit():
                    text3 = text3[:i] + '*' + text3[i + 1:]
                elif text3[i - 1] == ')':
                    text3 = text3[:i] + '*' + text3[i + 1:]
                elif text3[i - 1] == '）':
                    text3 = text3[:i] + '*' + text3[i + 1:]
                elif text3[i - 1] == ' ':
                    if i - 2 > 0:
                        if text3[i - 2].isdigit():
                            text3 = text3[:i] + '*' + text3[i + 1:]

    text = text3          
            
    # 下面是主逻辑       

    parts = text.split(' ')
    if len(parts) == 1:
        return text  # 没有等号，返回原文本

    # 找到所有的等式
    part2 = parts.copy()

    part3 = []
    equations = []
    # 首先去除所有数字后面存在的字母串
    i = 0
    while i < len(part2):
        if part2[i].isdigit() and i + 1 < len(part2) and all_alpha(part2[i + 1]):
            # 如果字母串后面还是数字，那么这个字母串其实不需要去
            if i + 2 < len(part2) and part2[i + 2].isdigit():
                part3.append(part2[i])
                i += 1
            else:   
                part3.append(part2[i])
                i += 2         
        else:
            part3.append(part2[i])
            i += 1
    # 然后开始在part3中找等式
    for i in range(len(part3)):
        # 找到=所在的位置
        if '=' not in part3[i]:
            continue
        else:
            start_pos = i - 1
            end_pos = i + 1
            
            while True:
                if start_pos - 1 >= 0:
                    if all_alpha(part3[start_pos - 1]) == False:
                        start_pos = start_pos - 1
                    else:
                        break
                else:
                    break

            equation = "".join(part3[start_pos:end_pos + 1])

            equations.append(equation)

    # equation_id = 0
    
    # for i in range(len(parts)):
    #     # 找到=所在的位置
    #     if '=' not in parts[i]:
    #         continue
    #     else:
    #         parts[i] = parts[i].replace('=', f'= <<{equations[equation_id]}>>')
    #         equation_id += 1

    # result = ' '.join(parts)
    # result = result.replace('>> ', '>>')

    equation_id = 0
    result = []
    for i in raw_text:
        if i == '=':
            result.append(f'= <<{equations[equation_id]}>>')
            equation_id += 1
        else:
            result.append(i) 

    return "".join(result)# , "".join(result).replace('>> ', '>>')


if __name__ == '__main__':
    # example_text = [
    #     "Janet pays $40/hour for 3 hours per week of clarinet lessons and $28/hour for 5 hours a week of piano lessons. How much more does she spend on piano lessons than clarinet lessons in a year? Step 1: Janet spends 3 hours + 5 hours = 8 hours per week on music lessons. ки Step 2: She spends 40 * 3 = 120 on clarinet lessons per week. ки Step 3: She spends 28 * 5 = 140 on piano lessons per week. ки Step 4: Janet spends 120 + 140 = 260 on music lessons per week. ки Step 5: She spends 260 * 52 = 13520 on music lessons in a year. The answer is: 13520 ки",
    #     "Val cuts a single watermelon into 40 slices, and each slice has 20 black seeds and 20 white seeds. What is the total number of seeds in a watermelon? Step 1: There are 20 x 40 = 8000 black seeds. ки Step 2: There are 20 x 40 = 8000 white seeds. ки Step 3: So, the total number of seeds is 8000 + 8000 = 16000. The answer is: 16000 ки",
    #     "Sue is traveling from New York to San Francisco, 16 hours later after landing in New York from New Orleans. If the journey from New Orleans to New York took 3/4 times as much time as she takes to travel from New York to San Francisco, and she lands in San Francisco 24 hours later after departing from New York, calculate the total time she took to reach San Francisco from New Orleans? Step 1: If the journey from New Orleans to New York took 3/4 times as much time as she takes to travel from New York to San Francisco, the journey from New Orleans to New York took (3/4)*(16)=12 hours. ки Step 2: Since she landed in San Francisco 24 hours later after departing from New York, she took 24+16=40 hours to reach San Francisco from New Orleans. The answer is: 40 ки",
    #     "Grant spends $200.00 a year to have the newspaper delivered daily to his house.  Juanita buys the newspaper daily.  Monday through Saturday, she spends $0.50 and on Sunday she spends $2.00.  How much more money does Juanita spend buying the newspaper yearly than Grant? Step 1: Juanita spends 6 days * $0.50/day = $3.00/day on the newspaper ки Step 2: She spends $3.00/day * 365 days/year = $1095/year on the newspaper ки Step 3: She spends 1 day * $2.00 = $2.00 on the newspaper ки Step 4: That means she spends $2.00 + $1095 = $1100/year ки Step 5: Juanita spends $1100 - $200 = $900 more on the newspaper than Grant The answer is: 900 ки",
    #     "If Buzz bought a pizza with 78 slices at a restaurant and then decided to share it with the waiter in the ratio of 5:8, with Buzz's ratio being 5, what's twenty less the number of slices of pizza that the waiter ate? Step 1: The total ratio representing the pizza is 5+8 = 13. ки Step 2: The waiter ate 13 x 8 / 13 = 6 slices of the pizza. ки Step 3: Buzz ate 78 - 6 = 72 slices of the pizza. ки Step 4: The waiter ate 20 less than the number of slices that Buzz ate which is 72 - 20 = 52. ки Step 5: The waiter ate 52 slices of the pizza. The answer is: 52 ки"
    # ]

    example_text = []
    answer_text = []
    with open('F://code//github//ChatGLM-MathV2//data//test_data100//test_data100.jsonl', 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line)
            example_text.append(data['solution'])

    with open('F://code//github//ChatGLM-MathV2//raw_data//peiyi9979_Math_Shepherd_for_codeTest//math-shepherd1-100.jsonl', 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line)
            input_text = data['input']
            # 提取问题和解决方案
            split_point = input_text.find("Step 1:")
            question = input_text[:split_point].strip()
            solution = input_text[split_point:].strip()
            # 移除所有的“Step n: ”和“ки”
            solution = solution.replace("ки", "")  # 删除所有的ки
            for i in range(1, 20):  # 假设步骤不超过20
                solution = solution.replace(f"Step {i}: ", "")
            answer_text.append(solution)


    # 测试代码

    ans = 0
    for i, item in enumerate(example_text):
        highlighted_text1, highlighted_text2 = highlight_equations(item)
        if highlighted_text1 != answer_text[i] and highlighted_text2 != answer_text[i]:
            print("第", i + 1, "个样本:------------------------------------------------------")
            print("原文本：", item)
            print("高亮后：", highlighted_text1)
            print("标答案：", answer_text[i])
            print("第", i + 1, "个样本:------------------------------------------------------\n")
            ans += 1
    print("error:", ans)



    # i = 97
    # highlighted_text, _ = highlight_equations(example_text[i])
    # print("原文本：", example_text[i])
    # print("高亮后：", highlighted_text)
    # print("标准答案：", answer_text[i])
    # print()