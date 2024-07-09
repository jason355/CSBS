import os, sys
from implementV2_9_5 import Teacher, Bot
import databaseV2_9_5 as db
from urllib.parse import parse_qsl
from linebot.models import  FollowEvent, MessageEvent, TextMessage, TextSendMessage, UnfollowEvent, PostbackEvent, FileMessage
from linebot.exceptions import InvalidSignatureError
from linebot import LineBotApi, WebhookHandler
from flask import Flask, request, abort, jsonify, render_template
from werkzeug.serving import make_server




app = Flask(__name__) # 建立 Flask 物件


channel_access_token = os.getenv("SSBS_test2A") # 取得Line bot channel access token 環境變數
channel_secret = os.getenv("SSBS_test2C") # 取得 Line bot channel secret 環境變數


line_bot_api = LineBotApi(channel_access_token) #  建立 Line bot API 實例
handler = WebhookHandler(channel_secret) # 建立 webhook 實例


users = {} # 初始化 users
Manager = Bot(line_bot_api, db, users) # Bot 實例 在 implement 中定義

# # 班級列表
# class_list = ['701', '702', '703', '704', '705', '706', '801', '802', '803', '804', '805', '806', '901', '902', '903', '904', '905',
#               '906', '101', '102', '103', '104', '105', '106', '111', '112', '113', '114', '115', '116', '121', '122', '123', '124', '125', '126']
# # 年級列表
# grade_list = ['1', '2', '3', '4', '5','7', '8', '9']

errorText = "*An Error in appV2.9.5" # 錯誤訊息基本文字
# error_messages = [] # 錯誤訊息 List
global errorIndex # 錯誤訊息索引值紀錄
errorIndex = 1 # 初始化索引值



# 處理callback事項
@app.route("/callback", methods=['POST']) # 設置一個路由，處理來自指定URL的POST請求
def callback(): # 定義一個名為callback的函數
    signature = request.headers["X-Line-Signature"] # 從請求頭部獲取X-Line-Signature
    body = request.get_data(as_text=True) # 從請求中獲取數據，並將其作為文本返回
    try: 
        handler.handle(body, signature) # 調用handler的handle方法來處理請求
    except InvalidSignatureError: # 如果簽名無效，則觸發InvalidSignatureError異常
        abort(400)  # 返回HTTP狀態碼400，表示請求無效
    return 'OK'  # 返回OK字串，表示請求已經成功處理

# 訊息傳輸失敗回傳
@app.route("/return", methods=['POST'])
def test():
    data = request.json  # 從 POST 請求中取得 JSON 資料
    message = data.get("content") # 取得 data 中 key = 'content' 的資料 
    cls = data.get("cls") # 取得 data 中 key = 'cls' 的資料 
    time = data.get("time") # 取得 data 中 key = 'time' 的資料 
    tea = data.get("name") # 取得 data 中 key = 'name' 的資料 
    print(cls, time, tea, message)
    try:
        id = db.getID(tea) # 取得傳輸者 Line ID
        print(id)
        if id : # 若不為空值則傳輸錯誤訊息
            line_bot_api.push_message(id.lineID, TextSendMessage(text=f"資料傳輸失敗\n原定派送班級 : {cls}\n訊息內容 : {message}\n發送時間 : {time}"))
            print(f"資料傳輸失敗\n原定派送班級\n:id:{id.lineID}\n{cls}\n訊息內容 :{message}\n發送時間 :{time}")
        print("data process success")
        return  jsonify({"status": "success"})
    except Exception as e: # 若try下方有任何exception會跳到此然後更新error網站顯示錯誤訊息
        error = f"{errorText}-test()\n{e}"
        print(error)
        Manager.addError(error)
    



@app.route('/errors', methods=['GET'])
def show_errors():
    error_messages = Manager.getErrorList()     # 取得在implement 中的error List
    return render_template('errors.html', errors=error_messages) # 渲染畫面顯示error list

@app.route('/classlist', methods=['GET'])
def showClassList():
    try:
        codeList = db.getClassCodeList()
        nameList = db.getClassNameList()
        return render_template('classList.html', length = len(codeList),codeList=codeList, nameList=nameList)
    except Exception as e:
        error = f"{errorText}-showClassList\n{e}"
        print(error)
        Manager.addError(error)

# 教師初次登入
@handler.add(FollowEvent)
def handle_follow(event):
    user_id = event.source.user_id # 取得使用者 Line ID
    if db.findAdmin(): # 確認是否有管理員在資料庫中
        Manager.users[user_id] = Teacher(user_id, status = "FSs1") # 設定首次登入之 Teacher 物件 詳細在implement中
        reply_message = "老師好, 請輸入您的名稱"
        line_bot_api.reply_message(  # 回傳文字 reply_message
            event.reply_token, TextSendMessage(text=reply_message))
    else: # 若無管理員則需在終端機中輸入名稱與組別，將此第一名登入用戶設定成管理員
        name = input("請輸入管理員名稱> ")
        office = input("請輸入管理員所在組別> ")
        try:
            db.insertAdmin(user_id, {'name':name, 'office':office, 'verifyStat':1, 'isAdmin':1})
        except Exception as e:
            error = f"{errorText}-handle_follow()\n{e}"
            print(error)
            Manager.addError(error)
            sys.exit()
        
# 用戶封鎖 Linebot時處理
@handler.add(UnfollowEvent)
def handle_unfollow(event):
    user_id = event.source.user_id # 取得使用者 Line ID
    try:
        teacher = db.findTeacher(user_id) # 取得教師資訊
        if teacher: # 如果teacher 為真
            del Manager.users[user_id] # 刪除在 Manager 物件 users 中的資料
            db.DelTeacherData(user_id) # 刪除資料庫中的使用者資料
            print(f"Unfollowed by {user_id}")
    except Exception as e:
        error = f"{errorText}-handle_unfollow()\n{e}"
        print(error)
        Manager.addError(error)
    



# 定義處理函数
action_handlers = {
    "@confirm_yes": Manager.confirm_yes,
    "@confirm_no": Manager.confirm_no,
    "@文字廣播": lambda event, user_id: Manager.postback_Bs(event, user_id) if Manager.users[user_id].status != "Ss3" else None,
    "@教師個人資訊": Manager.postback_Ss,
    "@歷史訊息": lambda event, user_id: Manager.postback_Hs(event, user_id) if Manager.users[user_id].status != "Ss3" else None,
    "@幫助": lambda event, user_id: Manager.postback_Help(event),
    "@select_class": Manager.postback_Sc,
    "@select_group": Manager.postback_Sg,
    "@Cselect_class": lambda event, user_id: (setattr(Manager.users[user_id], "status", "Bs1"), Manager.postback_Sc(event, user_id)) if Manager.users[user_id].status == "Bs2.2" else None, 
    "@Cselect_group": lambda event, user_id: (setattr(Manager.users[user_id], "status", "Bs1"), Manager.postback_Sg(event, user_id))  if Manager.users[user_id].status == "Bs2.1" else None, 
    "@cancel": Manager.postback_C,
    "@CofS_Y": lambda event, user_id: Manager.postback_US(event, user_id, "CofS_Y"),
    "@CofS_N": lambda event, user_id: Manager.postback_US(event, user_id, "CofS_N"),
    "@FD": lambda event, user_id: Manager.postback_Bs5(event, user_id) if Manager.users[user_id].status == "Cs" else None,
    "@EC": lambda event, user_id: Manager.edit_class(event, user_id) if Manager.users[user_id].status == "Cs" else None,
    "@ET": lambda event, user_id: (Manager.reply_cancel(event, "重新輸入廣播訊息"), setattr(Manager.users[user_id], "status", "Bs3c")) if Manager.users[user_id].status == "Cs" else None,
    "@ES": lambda event, user_id: (setattr(Manager.users[user_id], "status", "Bs4"), Manager.sound_select(event, user_id)) if Manager.users[user_id].status == "Cs" else None,
    "@EA": lambda event, user_id: Manager.edit_all(event, user_id) if Manager.users[user_id].status == "Cs" else None,
    "@Eselect_class": lambda event, user_id: Manager.postback_Sc(event, user_id, True) if Manager.users[user_id].status == "Bs1" else None,
    "@Eselect_group": lambda event, user_id: Manager.postback_Sg(event, user_id, True) if Manager.users[user_id].status == "Bs1" else None,
    "@sound_yes": lambda event, user_id: (Manager.users[user_id].data.update({"sound": "1"}),setattr(Manager.users[user_id], 'status', 'Cs'), Manager.sendConfirm(event, user_id)) if Manager.users[user_id].status == 'Bs4' else None,
    "@sound_no": lambda event, user_id: (Manager.users[user_id].data.update({"sound": "0"}),setattr(Manager.users[user_id], 'status', 'Cs'), Manager.sendConfirm(event, user_id)) if Manager.users[user_id].status == 'Bs4' else None,
    "@Adm_func": lambda event, user_id: Manager.cmd_button(event, user_id) if Manager.users[user_id].status == 'Fs' else None,
    "@reset_yes": lambda event, user_id: (print("****Server Shuting Down****"), [line_bot_api.push_message(teacher, TextSendMessage(text="⚠️系統即將重新啟動，請稍後再試")) for teacher in db.GetAllTeacherID() if teacher != user_id], sys.exit()) if Manager.users[user_id].status == 'Rs' else None,
    "@reset_no": lambda event, user_id: (setattr(Manager.users[user_id], 'status', 'Fs'), line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已取消"))) if Manager.users[user_id].status == 'Rs' else None,
    "@del_yes": lambda event, user_id: (setattr(Manager.users[user_id], 'status', 'Fs'), [line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message)) for reply_message in [f"已刪除 {rows}筆資料" if rows > 0 else "無資料可刪除" if rows == 0 else f"錯誤:{rows}" for rows in [db.DelDataAll()]]]) if Manager.users[user_id].status == 'Ds' else None,
    "@del_no": lambda event, user_id: (setattr(Manager.users[user_id], 'status', 'Fs'), line_bot_api.reply_message(event.reply_token, TextSendMessage(text="已取消"))) if Manager.users[user_id].status == 'Ds' else None,
    "@ExamStatus":lambda event, user_id: Manager.postback_ExamStatus(event, user_id),
    "@EndExamStatus":lambda event, user_id: Manager.postback_EndExamStatus(event),
    "@StartExamStatus":lambda event, user_id: Manager.postback_StartExamStatus(event)
}



# 指令縮寫說明
# Bs (Bordcast stage)廣播訊息階段 (1: 選擇單獨或群發/2.1 個別發送/2.2 群體發送/ 3 取得文字/ 4 取得結束廣播時間 c修改狀態)
# Fs (Free stage)空閒
# Ss (Setting stage)設定教師個人資訊 (F第一次登入/1/2/3 等待管理員確認)
# ACs (Admin Confirm stage) 
# Cs (Confirm stage)
# Rs (Reset stage)
# Ds (Delet Data stage)
@handler.add(PostbackEvent)
def handle_postback(event):
    user_id = event.source.user_id
    backdata = dict(parse_qsl(event.postback.data))

    if not db.findAdmin():
        name = input("請輸入管理員名稱> ")
        office = input("請輸入管理員所在組別> ")
        try:
            db.insertAdmin(user_id, {'name':name, 'office':office, 'verifyStat':1, 'isAdmin':1})
        except Exception as e:
            print(f"*An Error: {e}")
            Manager.addError(e)
            sys.exit()
    
    # 程式開啟後第一次加入，建立物件
    if user_id not in Manager.users:
        Manager.users[user_id] = Teacher(user_id, status = "Fs")
        try:
            teacher = db.getTeacher(user_id)
            if teacher:
                Manager.users[user_id].name = teacher.name
                Manager.users[user_id].office = teacher.office
                if teacher.isAdmin == 1:
                    Manager.users[user_id].isAdm = 1
            else:
                Manager.users[user_id].status = "FSs1"
                reply_message =  "老師好, 請輸入您的名稱"
                line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=reply_message))
        except Exception as e:
            print(f"{errorText}-handle_message()\n{e}")
            Manager.addError(e)
            reply_message = "資料庫異常，請再試一次或是洽詢 #9611資訊組"
            line_bot_api.push_message(user_id, TextSendMessage(text=reply_message))

    get = backdata.get('action') # 取得action
    handler = action_handlers.get(get) # 取得action對應函數
    if handler:
        handler(event, user_id)
        




status_handlers = {
    "FSs1": lambda event, user_id, text: Manager.handle_Ss1(event, user_id, text),
    "FSs2": lambda event, user_id, text: Manager.handle_Ss2(event, user_id, text),
    "Ss1": lambda event, user_id, text: Manager.handle_Ss1(event, user_id, text),
    "Ss2": lambda event, user_id, text: Manager.handle_Ss2(event, user_id, text),
    "Bs1": lambda event, user_id, text : line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠目前處於廣播階段，請先完成廣播或是取消")),
    "Bs2.1": lambda event, user_id, text: Manager.handle_Bs2_1(event, user_id, text),
    "Bs2.1c": lambda event, user_id, text: Manager.handle_Bs2_1(event, user_id, text),
    "Bs2.2": lambda event, user_id, text: Manager.handle_Bs2_2(event, user_id, text),
    "Bs2.2c": lambda event, user_id, text: Manager.handle_Bs2_2(event, user_id, text),
    "Bs3": lambda event, user_id, text: Manager.handle_Bs3(event, user_id, text),
    "Bs3c":lambda event, user_id, text: Manager.handle_Bs3(event, user_id, text),
    "Cs":lambda event, user_id, text: line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠請先確認傳送訊息或是取消此功能")),
    "Fs":lambda event, user_id, text: Manager.handle_Fs(event, user_id, text),
    "ACs": lambda event, user_id, text: Manager.handle_Admin1(event, user_id, text),
}



# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    user_id = event.source.user_id

    if not db.findAdmin():
        name = input("請輸入管理員名稱> ")
        office = input("請輸入管理員所在處室> ")
        try:
            db.insertAdmin(user_id, {'name':name, 'office':office, 'verifyStat':1, 'isAdmin':1})
        except Exception as e:
            print(f"*An Error: {e}")
            Manager.addError(e)
            sys.exit()

    # 判斷是否有在字典中
    if user_id not in Manager.users:
        Manager.users[user_id] = Teacher(user_id, status = "Fs")
        try:
            teacher = db.getTeacher(user_id)
            if teacher:
                Manager.users[user_id].name = teacher.name
                Manager.users[user_id].office = teacher.office
                if teacher.isAdmin == 1:
                    Manager.users[user_id].isAdm = 1
            else:
                Manager.users[user_id].status = "FSs1"
                reply_message =  "老師好, 請輸入您的名稱"
                line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=reply_message))
        except Exception as e:
            print(f"{errorText}-handle_message()\n{e}")
            Manager.addError(e)
            reply_message = "資料庫異常，請再試一次或是洽詢 #9611資訊組"
            line_bot_api.push_message(user_id, TextSendMessage(text=reply_message))


    status = Manager.users[user_id].status # 取得用戶狀態
 
    handler = status_handlers.get(status) # 取得對應函數

    if handler:
        handler(event, user_id, text)
        


if __name__ == '__main__':
    http_server = make_server('127.0.0.1', 5000, app)
    http_server.serve_forever()