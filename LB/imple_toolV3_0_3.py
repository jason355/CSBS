import re
import regex, hashlib
from datetime import datetime, time
import copy

class Template:
    @staticmethod
    def get_dataTemplate():
        template = {'content':"", 
                'classLs': [], 
                'classStr': "", 
                'des_class': "", 
                'des_grade': "", 
                'finish_date':"", 
                'sound':""
                }
        return copy.deepcopy(template)
    def get_pattern():
        return r'(\d+)[, ]*'

    def get_AdmConPattern():
        return r'(\d+-\d+|\d+)'

errorText = "*An Error in imple_toolV3_0_2"


# 產生 SHA-1
def sha1_hash(string):
    string_bytes = string.encode('utf-8')
    sha1 = hashlib.sha1()
    sha1.update(string_bytes)
    hashed_string = sha1.hexdigest()
    return hashed_string




# 格式化班級
def format_class(input, db):
    numbers = re.findall(r'\d+', input)
    try:
        additional_class = db.getClassCodeList(34)
        dic = db.getClassDic(34)
    except Exception as e:
        raise e
    res = ""
    # 將非基本班級加入至字串中
    for i, item in enumerate(numbers):
        if item in additional_class:
            res += " " + dic[item]
            numbers[i] = 0
    numbers = list(map(int, numbers))

    if not numbers:
        return input
    numbers.sort()
    # print(numbers)
    result = []
    

    if "高中部" in input:
        res += " 高中部"
    if  "國中部" in input:
        res += " 國中部"
    if "全年級 " in input:
        res += " 全校"
    if "其他教室" in input:
        res += " 其他教室"
    start = numbers[0]
    prev_num = numbers[0]

    for current_num in numbers[1:]:
        if len(str(current_num)) == 3:
            if prev_num == current_num - 1:
                prev_num = current_num
            else:
                if start == prev_num:
                    if len(str(start)) == 3:
                        result.append(str(start))
                    else:
                        match (start):
                            case 1 | 2 | 3:
                                
                                result.append(f"高{start}")
                                
                            case 7 | 8 | 9:
                                result.append(f"國{start}")
                else:
                    result.append(f"{start}-{prev_num}")

                start = current_num
                prev_num = current_num
        else:
            match (current_num):
                case 1 | 2 | 3:
                    result.append(f"高{current_num}")
                    
                case 7 | 8 | 9:
                    result.append(f"國{current_num}")
    # 處理最後一個數字
    if start == prev_num:
        if len(str(start)) == 3:
            result.append(str(start))
        else:
            match (start):
                case 1 | 2 | 3:
                    result.append(f"高{start}")
                
                case 7 | 8 | 9:
                    result.append(f"國{start}")
    else:
        result.append(f"{start}-{prev_num}")
    
    for item in result:
        res += " "+item
    return res


# 計算字數
def calc_unicode_seg(text):
    segments = regex.findall(r'\X', text, regex.U)
    character_count = len(segments)
    return character_count


# 將讀到的傳送班級列表中，重複的刪除
def arrangeGetClass(list):
    list.sort()
    j = 0
    for i in range(len(list)):
        if j >= len(list)-1:
            return list
        if list[j] == list[j+1]:
            del list[j+1]
            # print(list)
        else:
            j+=1


# 判斷是否為下課
def isBreak(BreakList):
    NowTime = datetime.now().time()
    if NowTime.hour > 15: # 若小時超過15則回傳2 顯示將在明天廣播
        return 2
    elif NowTime.hour < 8: # 小時小於 8 則回傳3 顯示將在下一節課廣播
        return 3
    breakTime_Start = time(NowTime.hour,int(BreakList[str(NowTime.hour)+"S"]), 0) # 取得下課開始時間
    breakTime_End = time(NowTime.hour, int(BreakList[str(NowTime.hour)+"E"]), 0) # 取得下課結束時間
    if NowTime >= breakTime_Start and NowTime < breakTime_End: # 現在時間為下課?
        return 1
    else:
        return 3



    
