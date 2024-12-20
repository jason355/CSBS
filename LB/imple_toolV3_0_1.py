import re
import databaseV3_0_1 as db
import regex, hashlib
from datetime import datetime, time

class_list = ['701', '702', '703', '704', '705', '801', '802', '803', '804', '805', '901', '902', '903', '904', '905','101', '102', '103', '104', '105', '106', '111', '112', '113', '114', '115', '116', '121', '122', '123', '124', '125', '126']
group_index = [-1, 4, 9, 14, 20, 26, 32]
grade_list = ['1', '2', '3', '4', '5','7', '8', '9']

errorText = "*An Error in imple_toolV3_0_1"



help_text = '''歡迎加入政大附中無聲廣播系統
設定好個人資訊後，向管理員提出身分認證。

🔴🔴功能選單🔴🔴
若您使用電腦版Line，取得管理員認證後，傳送任意文字即可叫出功能選單。
若您使用手機，可透過螢幕底部按鈕樣板直接進入功能，或是傳送任意文字叫出功能選單。

🔴🔴發送廣播🔴🔴
1. 選擇"發送廣播"。
2. 選擇發送類型 "個別發送" 或 "群發年級"\n個別發送:限定發送一個班級(跳至2.1) 例如: 113\n群發年級:可組合不同年級與班級或是全校廣播(跳至2.2)
2.1 若您選擇 "個別發送"，輸入單個目標班級
2.2 若您選擇 "群體發送"，輸入班級組合(使用空格分開)
3. 輸入完目標班級後，系統提示"輸入廣播文字"，即可傳送廣播文字
4. 系統發送檢查通知，系統預設結束廣播時間為隔日(後天有傳出的廣播會被刪除)，若需延長廣播時間，請點"調整廣播結束日期"\n
5. 若無須修改結束廣播時間，按"YES我已確認"或"NO訊息有誤"更正即完成廣播。
🔴🔴重設&更正教師資訊🔴🔴
在選單點選"教師個人資訊"，按步驟更新資料，耐心等候管理員認證。

🔴🔴尋求幫助🔴🔴
忘記如何使用？歡迎連繫:#9611 資訊組長'''


# 建立下課字典
def make_break(BreakList):
    j = 0
    for i in range(8, 16, 1):
        if i == 8:
            BreakList['8S'] = "5"
            BreakList['8E'] = "10"
        elif i == 12:
            BreakList['12S'] = "0"
            BreakList['12E'] = "30"
        elif i == 13:
            BreakList['13S'] = "5"
            BreakList['13E'] = "10"
        elif i == 15:
            BreakList['15S'] = "0"
            BreakList['15E'] = "15"
        else:
            BreakList[f'{i}S'] = "0"
            BreakList[f'{i}E'] = "10"
        j+=1


# 產生 SHA-1
def sha1_hash(string):
    string_bytes = string.encode('utf-8')
    sha1 = hashlib.sha1()
    sha1.update(string_bytes)
    hashed_string = sha1.hexdigest()
    return hashed_string




# 格式化班級
def format_class(input):
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

# def addUsers(n):
#     for i in range(10,10+n):
#         user_id = sha1_hash(str(i))
#         db.insertTeaInfor(lineId=user_id, map={"name":i, "office":"A", "verifyStat": 0})
#         # # db.DelTeacherData(lineId=i)
#         print(user_id)

# addUsers(n=10)
    
