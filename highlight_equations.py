def all_alpha(str):
    if str == 'x': # 特例
        return False
    if all(temp.isalpha() for temp in str):
        return True
    else:
        return False

def highlight_equations(text):
    parts2 = text.split(' ')
    if len(parts2) == 1:
        return text  # 没有等号，返回原文本
    
    # 预处理，如果数字后面紧跟着一个字母串，可以删去这个字母串
    parts = []
    i = 0
    while i < len(parts2):
        parts.append(parts2[i])
        if parts2[i].isdigit():
            if i + 1 < len(parts2) and all_alpha(parts2[i + 1]):
                i += 2
            else:
                i += 1
        else:
            i += 1

    result = []
    last_pos = 0
    
    for i in range(len(parts)):
        # 找到=所在的位置
        if '=' not in parts[i]:
            continue
        else:
            start_pos = i
            end_pos = i
            if start_pos > 0:
                while all_alpha(parts[start_pos - 1]) == False:
                    start_pos -= 1
                    if start_pos == 0:
                        break
            if end_pos < len(parts) - 1:
                while all_alpha(parts[end_pos + 1]) == False:
                    end_pos += 1
                    if end_pos == len(parts) - 1:
                        break
            # print(parts[start_pos:end_pos + 1])
            equation = ' '.join(parts[start_pos:end_pos + 1])
            equation = equation.replace('=', f'=<<{equation}>>')
            for item in range(last_pos, start_pos):
                result.append(parts[item])
            result.append(equation)
            last_pos = end_pos + 1
    
    # 添加最后一个没有等号的部分
    for item in range(last_pos, len(parts)):
        result.append(parts[item])

    return ' '.join(result)


if __name__ == '__main__':
    example_text = [
        "Janet pays $40/hour for 3 hours per week of clarinet lessons and $28/hour for 5 hours a week of piano lessons. How much more does she spend on piano lessons than clarinet lessons in a year? Step 1: Janet spends 3 hours + 5 hours = 8 hours per week on music lessons. ки Step 2: She spends 40 * 3 = 120 on clarinet lessons per week. ки Step 3: She spends 28 * 5 = 140 on piano lessons per week. ки Step 4: Janet spends 120 + 140 = 260 on music lessons per week. ки Step 5: She spends 260 * 52 = 13520 on music lessons in a year. The answer is: 13520 ки",
        "Val cuts a single watermelon into 40 slices, and each slice has 20 black seeds and 20 white seeds. What is the total number of seeds in a watermelon? Step 1: There are 20 x 40 = 8000 black seeds. ки Step 2: There are 20 x 40 = 8000 white seeds. ки Step 3: So, the total number of seeds is 8000 + 8000 = 16000. The answer is: 16000 ки",
        "Sue is traveling from New York to San Francisco, 16 hours later after landing in New York from New Orleans. If the journey from New Orleans to New York took 3/4 times as much time as she takes to travel from New York to San Francisco, and she lands in San Francisco 24 hours later after departing from New York, calculate the total time she took to reach San Francisco from New Orleans? Step 1: If the journey from New Orleans to New York took 3/4 times as much time as she takes to travel from New York to San Francisco, the journey from New Orleans to New York took (3/4)*(16)=12 hours. ки Step 2: Since she landed in San Francisco 24 hours later after departing from New York, she took 24+16=40 hours to reach San Francisco from New Orleans. The answer is: 40 ки",
        "Grant spends $200.00 a year to have the newspaper delivered daily to his house.  Juanita buys the newspaper daily.  Monday through Saturday, she spends $0.50 and on Sunday she spends $2.00.  How much more money does Juanita spend buying the newspaper yearly than Grant? Step 1: Juanita spends 6 days * $0.50/day = $3.00/day on the newspaper ки Step 2: She spends $3.00/day * 365 days/year = $1095/year on the newspaper ки Step 3: She spends 1 day * $2.00 = $2.00 on the newspaper ки Step 4: That means she spends $2.00 + $1095 = $1100/year ки Step 5: Juanita spends $1100 - $200 = $900 more on the newspaper than Grant The answer is: 900 ки",
        "If Buzz bought a pizza with 78 slices at a restaurant and then decided to share it with the waiter in the ratio of 5:8, with Buzz's ratio being 5, what's twenty less the number of slices of pizza that the waiter ate? Step 1: The total ratio representing the pizza is 5+8 = 13. ки Step 2: The waiter ate 13 x 8 / 13 = 6 slices of the pizza. ки Step 3: Buzz ate 78 - 6 = 72 slices of the pizza. ки Step 4: The waiter ate 20 less than the number of slices that Buzz ate which is 72 - 20 = 52. ки Step 5: The waiter ate 52 slices of the pizza. The answer is: 52 ки"
    ]

    # 测试代码
    for item in example_text:
        highlighted_text = highlight_equations(item)
        print(highlighted_text)
        print('\n')