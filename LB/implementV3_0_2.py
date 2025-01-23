# version 3.0.2
import re, json, sys, requests, subprocess
from linebot.models import  TextSendMessage, PostbackTemplateAction, TemplateSendMessage, ButtonsTemplate, PostbackAction, DatetimePickerTemplateAction,MessageAction, URIAction, QuickReply, QuickReplyButton
from datetime import date, timedelta
import imple_toolV3_0_2 as t
from datetime import datetime
from sqlalchemy import exc



errorText = "*An Error in implementV3.0.2"
contactInfo = "{contactInfo}"
error_messages  = []
global errorIndex
errorIndex = 1
global ExamStatus
ExamStatus = False




class Teacher():
    
    def __init__(self, id, name = None, office = None, status = None, isAdm = None, data = None, preStatus = None):
        self.id = id
        self.name = name
        self.office = office
        self.isAdm = isAdm
        self.data = t.Template.get_dataTemplate() # 使用copy()创建新的字典
        self.status = status
        self.preStatus = preStatus

class Bot():

    def __init__(self, api, database, users, Confirm_List = [], webhook_url = ""):
        self.api = api
        self.db = database
        self.users = users 
        self.Confirm_List = Confirm_List
        self.webhook_url = webhook_url
        self.pattern = t.Template.get_pattern()
        self.AdmConPattern = t.Template.get_AdmConPattern()
        with open("config.json", "r", encoding="utf-8") as c:
            self.config = json.load(c)
        

        

    def init(self):
        if not self.config["Dynamic"]["initial_start"]:
            for teacher in self.db.GetAllTeacherID():
                self.api.push_message(teacher, TextSendMessage(text="系統重啟完成✅")) 
        else:
            self.config["Dynamic"]["initial_start"] = False
            with open("config.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(self.config, indent=4))

        self.webhook_url = self.query_ngork_url(self.config["Basic"]["query_url"])

        if self.config["Basic"]["ngrok_url"] == "":
            self.config["Basic"]["ngrok_url"] = self.webhook_url
            self.send_link_to_admin()
            with open("config.json", "w") as f:
                f.write(json.dumps(self.config, indent=4))
        elif self.config["Basic"]["ngrok_url"] != self.webhook_url:
            self.config["Basic"]["ngrok_url"] = self.webhook_url
            self.send_link_to_admin()
            with open("config.json", "w") as f:
                f.write(json.dumps(self.config, indent=4))
    # 抓取ngrok url
    def query_ngork_url(self, url):
        try:
            response = requests.get(url) # 透過本地API抓取對外URL
            data = response.json()

            # Extract the public URL
            webhook_url = data['tunnels'][0]['public_url'] + "/callback"
            print(f"ngrok URL: {webhook_url}")
            return webhook_url
        except requests.exceptions.ConnectionError as REC:
            ngrok_command = "ngrok http 5000"
            subprocess.Popen(ngrok_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
            with open("config.json", "r", encoding="utf-8") as c:
                self.config = json.load(c)
            with open("config.json", "w", encoding="utf-8") as f:
                self.config["Dynamic"]["initial_start"] = True
                f.write(json.dumps(self.config, indent=4))
            sys.exit()
    # 傳送連結至管理員
    def send_link_to_admin(self):
        adminList = self.db.findAdmin()
        for admin in adminList:
            self.api.push_message(admin, TextSendMessage(text= f"Linebot 已啟動，請至 https://developers.line.biz/console/channel/2000168053/messaging-api 更新\nLink: {self.webhook_url}"))



    # 傳送錯誤至錯誤網頁
    def addError(self, e):
        global errorIndex
        error_message = {'id':errorIndex, "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "error": e}
        error_messages.append(error_message)
        errorIndex += 1
    
    def getErrorList(self):
        return error_messages 

    # 傳送功能選單
    def SendButton(self, event, user_id):
        try:
            message = TemplateSendMessage(
                alt_text='按鈕樣板',
                template=ButtonsTemplate(
                    title='請選擇服務：',
                    thumbnail_image_url = "https://raw.githubusercontent.com/jason355/CSBS/master/LB/templates/image/favicon.png",
                    text='請務必先點選"教師個人資訊"按鈕以設定身分',
                    actions=[
                        PostbackTemplateAction(
                            label='發送廣播',
                            data='action=@文字廣播'
                        ),
                        PostbackTemplateAction(
                            label='更改教師個人資訊',
                            data='action=@教師個人資訊'
                        ),
                        PostbackTemplateAction(
                            label='歷史訊息',
                            data='action=@歷史訊息'
                        ),
                        PostbackTemplateAction(
                            label='幫助',
                            data = 'action=@幫助'
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            print(f"{errorText}-SendButton()\n{e}")
            self.addError(e)
            self.api.push_message(user_id, TextSendMessage(text="選擇傳送按鈕傳送錯誤，若樣板有傳出請忽略此訊息，若無請再試一次或是聯絡資訊組"))

    # 管理員樣板
    def SendButton_Adm(self, event, user_id):
        try:
            message = TemplateSendMessage(
                alt_text='按鈕樣板',
                template=ButtonsTemplate(
                    title=f'請選擇服務：',
                    thumbnail_image_url = "https://raw.githubusercontent.com/jason355/SWBS/main/img1.png",
                    text="點選下方按鈕來啟用服務",
                    actions=[
                        PostbackTemplateAction(
                            label='發送廣播',
                            data='action=@文字廣播'
                        ),
                        PostbackTemplateAction(
                            label='更改教師個人資訊',
                            data='action=@教師個人資訊'
                        ),
                        PostbackTemplateAction(
                            label='歷史訊息',
                            data='action=@歷史訊息'
                        ),
                        PostbackTemplateAction(
                            label='管理員功能',
                            data = 'action=@Adm_func'
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            error = f"{errorText}-SendButton_Adm\n{e}"
            print(error)
            self.addError(error)
            self.api.push_message(
                user_id, TextSendMessage(text='⚠️發生錯誤！請在試一次或是使用@resetBot來重啟'))

    #管理員樣板
    def cmd_button(self, event, user_id):
        try:
            message = TemplateSendMessage(
                alt_text='按鈕樣板',
                template=ButtonsTemplate(
                    title='請選擇服務：',
                    thumbnail_image_url = "https://raw.githubusercontent.com/jason355/SWBS/main/img1.png",
                    text='請務必先點選"教師個人資訊"按鈕以設定身分',
                    actions=[
                        MessageAction(
                            label='重啟linebot',
                            text="@resetBot"
                        ),
                        MessageAction(
                            label='教師列表',
                            text='@userList'
                        ),
                        MessageAction(
                            label='刪除資料庫資料',
                            text='@delData'
                        ),
                        PostbackTemplateAction(
                            label=f'考試模式 目前:{ExamStatus}',
                            data="action=@ExamStatus"
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            error = f"{errorText}-cmd_button\n{e}"
            print(error)
            self.addError(error)
            self.api.push_message(
                user_id, TextSendMessage(text='⚠️發生錯誤!請再試一次或是使用@resetBot來重啟'))
    # 考試模式樣板
    def postback_ExamStatus(self, event, user_id):
        global ExamStatus
        try:
            if ExamStatus:
                message = TemplateSendMessage(
                    alt_text='按鈕樣板',
                    template=ButtonsTemplate(
                        title='關閉考試模式?',
                        text='點選是或取消來完成操作',
                        actions=[
                            PostbackTemplateAction(
                                label='是',
                                data="action=@EndExamStatus"
                            ),
                            PostbackTemplateAction(
                                label='取消',
                                data='action=@cancel'
                            ),
                        ]
                    )
                )
            else:
                message = TemplateSendMessage(
                    alt_text='按鈕樣板',
                    template=ButtonsTemplate(
                        title='開啟考試模式?',
                        text='點選是或取消來完成操作',
                        actions=[
                            PostbackTemplateAction(
                                label='是',
                                data="action=@StartExamStatus"
                            ),
                            PostbackTemplateAction(
                                label='取消',
                                data='action=@cancel'
                            ),
                        ]
                    )
                )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            error = f"{errorText}-ExamStatus\n{e}"
            print(error)
            self.addError(error)
            self.api.push_message(
                user_id, TextSendMessage(text='發生錯誤!請再試一次或是使用@resetBot來重啟'))

    # 處理結束考試模式
    def postback_EndExamStatus(self, event):
        global ExamStatus
        if ExamStatus:
            ExamStatus = False
            reply_message = "✅已更新為平常模式"
            self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

    # 處理開始考試模式
    def postback_StartExamStatus(self, event):
        global ExamStatus
        if not ExamStatus:
            ExamStatus = True
            reply_message = "✅已更新為段考模式"
            self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

    # 回覆樣板
    def reply_cancel(self, event, text, needCancel = True):
        if len(text) > 40:
            text = text[0:35] + "..."
        if needCancel:
            message = TemplateSendMessage(
                alt_text='Text-Cancel template',
                template=ButtonsTemplate(
                    title=text,
                    text= "依照上方指示操作",
                    actions=[
                        PostbackAction(
                            label='取消',
                            data='action=@cancel'
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)

        else:
            self.api.reply_message(event.reply_token, TextSendMessage(text=text))


    # 推播樣板
    def push_cancel(self, user_id, text, needCancel = True):
        if len(text) > 40:
            text = text[0:35] + "..."
        if needCancel:
            message = TemplateSendMessage(
                alt_text='Text-Cancel template',
                template=ButtonsTemplate(
                    title=text,
                    text= "依照上方指示操作",
                    actions=[
                        PostbackAction(
                            label='取消',
                            data='action=@cancel'
                        )
                    ]
                )
            )
            self.api.push_message(user_id, message)
        else:
            self.api.push_message(user_id, TextSendMessage(text=text))


    # 幫助
    def postback_Help(self, event):
        reply_message = self.config['personal']['help_text']
        self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))


    # 取消按鈕處理
    def postback_C(self, event, user_id):
        if self.users[user_id].status != "Fs":
            self.users[user_id].status = "Fs"
            reply_message = "❎已取消"
            self.users[user_id].data = t.Template.get_dataTemplate()

            self.api.reply_message(
            event.reply_token, TextSendMessage(text=reply_message))

    # 傳送訊息按鈕
    def postback_Bs(self, event, user_id):
        if self.users[user_id].status != "Bs1":
            try:
                if self.db.verified(user_id):
                    self.users[user_id].status = "Bs1"
                    self.select_target(event, user_id)
                else:
                    reply_message = "管理員尚未驗證，請耐心等候🙏"
                    self.api.reply_message(event.reply_token,TextSendMessage(text=reply_message))
            except exc.OperationalError as oe:
                self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請再試一次"))
            except Exception as e:
                error = f"{errorText}-postback_Bs\n{e}"
                print(error)
                self.addError(error)
                reply_message = f"⚠️資料庫異常，請再試一次或是聯絡 {contactInfo}"
                self.api.push_message(user_id, TextSendMessage(text=reply_message))



    # 單獨或群發按鈕
    def select_target(self, event, user_id):
        try:
            message = TemplateSendMessage(
                alt_text='Button Template',
                template=ButtonsTemplate(
                    # 把廣播訊息重複在此
                    title="請選擇發送類型",
                    text="個別發送限定一個班級，群體發送可發送給多個班級",
                    actions=[
                        PostbackTemplateAction(
                            label='個別發送',
                            data='action=@select_class'
                        ),
                        PostbackTemplateAction(
                            label='群發年級',
                            data='action=@select_group'
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data='action=@cancel'
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            print(e)
            self.api.push_message(user_id, TextSendMessage(text="選擇傳送按鈕傳送錯誤，若樣板有傳出請忽略此訊息，若無請再試一次或是聯絡資訊組"))

    # 特定班級樣板
    def select_single(self, event,user_id):
        try:
            message = TemplateSendMessage(
                alt_text='Button Template',
                template=ButtonsTemplate(
                    title="個別發送，請輸入要發送的班級",
                    text="ex: 703",
                    actions=[
                        PostbackTemplateAction(
                            label='更改成 群發年級',
                            data='action=@Cselect_group' # Change select group
                        ),
                        URIAction(
                            label="班級列表",
                            uri=self.webhook_url[:-8]+"classList"
                        ),                        
                        PostbackTemplateAction(
                            label='取消',
                            data='action=@cancel'
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            print(e)
            self.api.push_message(user_id, TextSendMessage(text="選擇傳送按鈕傳送錯誤，若樣板有傳出請忽略此訊息，若無請再試一次或是聯絡資訊組"))


    # 選擇特定班級按鈕 Select Class
    def postback_Sc(self, event, user_id, Edit=False):
        if self.users[user_id].status == "Bs1":
            if not Edit:
                self.users[user_id].status = "Bs2.1"
                self.select_single(event, user_id)

            else:
                self.users[user_id].status = "Bs2.1c"
                self.select_single(event, user_id)
    # 選擇群發按鈕 Select group
    def postback_Sg(self, event, user_id, Edit = False):
        if self.users[user_id].status == "Bs1":
            if not Edit:
                self.users[user_id].status = "Bs2.2"
                self.select_group_list(event, user_id) # 傳送群發按鈕列表
            else:
                self.users[user_id].status = "Bs2.2c"
                self.select_group_list(event, user_id)    
    
    # 群發文字
    def select_group_list(self, event, user_id):
        try:
            text = "請輸入傳送班級(請輸入中文字後的代號)\n 全年級 0 \n 高一 1 \n 高二 2 \n 高三 3 \n 高中 4 \n 國中 5 \n 其他教室 6 \n 七年級 7 \n 八年級 8 \n 九年級 9"
            # for i in range(3):
            #     text += "\n " + database_class_name_list[i] + " " + database_class_list[i]
            text += "\n...請點選下方班級列表按鈕查看所有班級"
            message = TemplateSendMessage(
                alt_text='Button Template',
                template=ButtonsTemplate(
                    text=text,
                    actions=[
                        PostbackTemplateAction(
                            label='更改成 個別發送',
                            data='action=@Cselect_class' # Change select class
                        ),
                        URIAction(
                            label="班級列表",
                            uri=self.webhook_url[:-8]+"/classList"
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data='action=@cancel'
                        )

                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            error = f"{errorText}-select_group_list\n{e}"
            self.addError(error)
            print(e)
            self.api.push_message(user_id, TextSendMessage(text="選擇傳送按鈕傳送錯誤，若樣板有傳出請忽略此訊息，若無請再試一次或是聯絡資訊組"))


    def confirm_yes(self, event, user_id):
        if self.users[user_id].status == "Cs":
                data = {}
                try:
                    user = self.db.getTeacher(user_id)
                except exc.OperationalError as oe:
                    print(oe)
                    self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️資料庫連接錯誤，請再試一次"))
                except Exception as e:
                    error = f"{errorText}-confirm_yes\n{e}"
                    print(error)
                    self.addError(error)
                    self.users[user_id].data = t.Template.get_dataTemplate()
                    reply_message = "尋找資訊錯誤，請再試一次或洽 #9611資訊組"
                    self.api.push_message(user_id, TextSendMessage(text=reply_message)) 
                else:
                    if user:
                        data["name"] = user.name
                        data['lineID'] = user_id
                        data["office"] = user.office
                        data['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data["des_class"] = None
                        data["des_grade"] = None
                        data['content'] = self.users[user_id].data['content']
                        data['finish_date'] = self.users[user_id].data['finish_date']
                        data['sound'] = self.users[user_id].data['sound']

                        hash_text = data['name'] + data['lineID'] + data['office'] + data['time'] + data['content']
                        data['hash'] = t.sha1_hash(hash_text)

                        if "611" not in self.users[user_id].data['classLs'] or "6" not in self.users[user_id].data["classLs"]:
                            print("True")
                            data['des_class'] = 1
                            data['des_grade'] = "61"
                            try:
                                self.db.insertData(data)
                            except Exception as e:
                                error = f"{errorText}-confirm_yes-self.db.insertData()-adding 611 to database\n{e}"
                                print(error)
                                self.addError(error)    
                                
                        if len(self.users[user_id].data['classLs']) == 0:
                            data['des_class'] = self.users[user_id].data['des_class']
                            data['des_grade'] = self.users[user_id].data['des_grade'] 
                            try:
                                ack = self.db.insertData(data)
                            except exc.OperationalError as oe:
                                self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                            except Exception as e:
                                error = f"{errorText}-confirm_yes-self.db.insertData()\n{e}"
                                print(error)
                                self.addError(error)    
                                ack = False
                                self.api.push_message(user_id, TextSendMessage(text="🙇‍♂️插入資料時發生錯誤，請重新傳送，或是聯絡資訊組"))
                        else:                            
                            for C in self.users[user_id].data["classLs"]:
                                data["des_class"] = None
                                data["des_grade"] = None
                                if len(C) == 1:
                                    match (C):
                                        case "0":
                                            for i in range(7, 10, 1):
                                                for j in range(1,6, 1):
                                                    data['des_class'] = j
                                                    data['des_grade'] = str(i) + "0"
                                                    try:
                                                        ack = self.db.insertData(data)
                                                    except exc.OperationalError as oe:
                                                        self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                                                    except Exception as e:
                                                        error = f"{errorText}-confirm_yes\n{e}"
                                                        print(error)
                                                        self.addError(error)
                                                        self.api.push_message(user_id, TextSendMessage(text="🙇‍♂️插入資料時發生錯誤，請重新傳送，或是聯絡資訊組"))
                                                        ack = False
                                                        break
                                            for i in range(0, 3):
                                                for j in range(1, 7, 1):
                                                    data['des_class'] = j 
                                                    data['des_grade'] = "1"+ str(i)
                                                    try:
                                                        ack = self.db.insertData(data)
                                                    except exc.OperationalError as oe:
                                                        self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                                                    except Exception as e:
                                                        error = f"{errorText}-confirm_yes\n{e}"
                                                        print(error)
                                                        self.addError(error)
                                                        self.api.push_message(user_id, TextSendMessage(text="🙇‍♂️插入資料時發生錯誤，請重新傳送，或是聯絡資訊組"))

                                                        ack = False
                                                        break                                              
                                        case "1" | "2" | "3":
                                            for i in range(1, 7, 1):
                                                data['des_class'] = i
                                                data['des_grade'] = "1" + str(int(C) - 1)
                                                try:
                                                    ack = self.db.insertData(data)
                                                except exc.OperationalError as oe:
                                                    self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                                                except Exception as e:
                                                    error = f"{errorText}-confirm_yes\n{e}"
                                                    print(error)
                                                    self.addError(error)
                                                    self.api.push_message(user_id, TextSendMessage(text="🙇‍♂️插入資料時發生錯誤，請重新傳送，或是聯絡資訊組"))
                                                    ack = False
                                                    break     
                                            
                                        case "4":
                                            for i in range(0, 3):
                                                for j in range(1, 7, 1):
                                                    data['des_class'] = j 
                                                    data['des_grade'] = "1"+ str(i)
                                                    try:
                                                        ack = self.db.insertData(data)
                                                    except exc.OperationalError as oe:
                                                        self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                                                    except Exception as e:
                                                        error = f"{errorText}-confirm_yes\n{e}"
                                                        print(error)
                                                        self.addError(error)
                                                        self.api.push_message(user_id, TextSendMessage(text="🙇‍♂️插入資料時發生錯誤，請重新傳送，或是聯絡資訊組"))
                                                        ack = False
                                                        break     
                                        case "5":
                                            for i in range(7, 10, 1):
                                                for j in range(1,6, 1):
                                                    data['des_class'] = j
                                                    data['des_grade'] = str(i) + "0"
                                                    try:
                                                        ack = self.db.insertData(data)
                                                    except exc.OperationalError as oe:
                                                        self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                                                    except Exception as e:
                                                        error = f"{errorText}-confirm_yes\n{e}"
                                                        print(error)
                                                        self.addError(error)
                                                        self.api.push_message(user_id, TextSendMessage(text="🙇‍♂️插入資料時發生錯誤，請重新傳送，或是聯絡資訊組"))
                                                        ack = False
                                                        break     
                                        case "6":
                                            try:
                                                basic_class_num = 34
                                                additional_class = self.db.getClassCodeList(basic_class_num)
                                                for item in additional_class:
                                                    data['des_class'] = item[2:]
                                                    data['des_grade'] = item[0:2]

                                                    ack = self.db.insertData(data)

                                            except exc.OperationalError as oe:
                                                self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                                            except Exception as e:
                                                error = f"{errorText}-confirm_yes\n{e}"
                                                print(error)
                                                self.addError(error)
                                                self.api.push_message(user_id, TextSendMessage(text="🙇‍♂️插入資料時發生錯誤，請重新傳送，或是聯絡資訊組"))
                                                ack = False
                                                break
                                        
                                        case "7" | "8" | "9":
                                            for i in range(1, 6, 1):
                                                data['des_class'] = i
                                                data['des_grade'] = C + "0"
                                                try:
                                                    ack = self.db.insertData(data)
                                                except exc.OperationalError as oe:
                                                    self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                                                except Exception as e:
                                                    error = f"{errorText}-confirm_yes\n{e}"
                                                    print(error)
                                                    self.addError(error)
                                                    self.api.push_message(user_id, TextSendMessage(text="🙇‍♂️插入資料時發生錯誤，請重新傳送，或是聯絡資訊組"))
                                                    ack = False 
                                                    break     
                                else:       
                                    data['des_grade'] = C[0:2]
                                    data['des_class'] = C[2]
                                    try:
                                        ack = self.db.insertData(data)
                                    except exc.OperationalError as oe:
                                        self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                                    except Exception as e:
                                        error = f"{errorText}-confirm_yes\n{e}"
                                        print(error)
                                        self.addError(error)
                                        self.api.push_message(user_id, TextSendMessage(text="🙇‍♂️插入資料時發生錯誤，請重新傳送，或是聯絡資訊組"))
                                        ack = False
                                        break     
                        if ack == True:
                            T = t.isBreak(self.config['personal']['break_dict'])
                            if T == 1:
                                reply_message = "✅已更新置資料庫，將在現在廣播"
                            elif T == 2:
                                reply_message = "✅已更新置資料庫，將在明天廣播"
                            elif T == 3:
                                reply_message = "✅已更新置資料庫，將在下一節下課廣播"
                            message = TemplateSendMessage(
                                            alt_text='Button Template',
                                            template=ButtonsTemplate(
                                                title=reply_message,
                                                text="點選下方按鈕可查看廣播使否發出",
                                                actions=[
                                                    URIAction(
                                                        label="及時廣播狀態",
                                                        uri=self.webhook_url[:-8]+"realtimedata/"+user_id
                                                    )
                                                ]
                                            )
                                        )
                            self.api.reply_message(event.reply_token, message)

                            self.users[user_id].data = t.Template.get_dataTemplate()
                    else:
                        reply_message = f"⚠️資料庫中未找到您的資料，請您嘗試封鎖此 Line Bot再解封鎖，以重新註冊，或是聯絡 #9611資訊組 謝謝"
                        self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))



        self.users[user_id].status = "Fs"
            


        
    # 修改訊息樣板
    def confirm_no(self, event, user_id):
        if self.users[user_id].status == "Cs":
            message = TemplateSendMessage(
                alt_text='Button Template',
                template=ButtonsTemplate(
                    title="請選擇要修改的內容",
                    text="根據上方指示進行操作",
                    actions=[
                        PostbackTemplateAction(
                            label='修改發送班級',
                            data='action=@EC' # Edit Class
                        ),
                        PostbackTemplateAction(
                            label='修改廣播內容',
                            data='action=@ET' # Edit Text
                        ),
                        PostbackTemplateAction(
                            label='音效修改',
                            data='action=@ES' # Edit Sound
                        ),
                        PostbackTemplateAction(
                            label='全部修改',
                            data='action=@EA' # Edit All
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)

    # 修改班級
    def edit_class(self, event, user_id):
        try:
            self.users[user_id].status = "Bs1" # Edit Class stat
            self.users[user_id].data['classLs'] = []
            self.users[user_id].data['classStr'] = " "
            self.users[user_id].data['des_class'] = ""
            self.users[user_id].data['des_grade'] = ""            
            message = TemplateSendMessage(
                alt_text='Button Template',
                template=ButtonsTemplate(
                    title="請選擇發送類型",
                    text="個別發送限定一個班級，群體發送可發送給多個班級",
                    actions=[
                        PostbackTemplateAction(
                            label='個別發送',
                            data='action=@Eselect_class'
                        ),
                        PostbackTemplateAction(
                            label='群發年級',
                            data='action=@Eselect_group'
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data='action=@cancel'
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            print(e)
            self.api.push_message(user_id, TextSendMessage(text="選擇傳送按鈕傳送錯誤，若樣板有傳出請忽略此訊息，若無請再試一次或是聯絡資訊組"))


    # 全部修改
    def edit_all(self, event, user_id):
        self.users[user_id].data['classLs'] = []
        self.users[user_id].data['classStr'] = " "
        self.users[user_id].data['des_class'] = ""
        self.users[user_id].data['des_grade'] = "" 
        self.users[user_id].status = "Bs1"
        self.select_target(event, user_id)



    # 傳送確認樣板
    def sendConfirm(self,event, user_id):
        try:
            if ExamStatus:
                self.users[user_id].data['sound'] = "0"
                sound = "無(因考試關係，故系統將強制設為無聲)"
            elif self.users[user_id].data['sound'] == "1":
                sound = "有"
            elif self.users[user_id].data['sound'] == "0":
                sound = "無"
            reply_message = f"你確定要發送此則訊息嗎？\n教師名稱: {self.users[user_id].name}\n組別: {self.users[user_id].office}\n傳送班級: \n廣播內容:\n \n結束廣播時間: {self.users[user_id].data['finish_date']}\n廣播音效: {sound}"
            reply_len = t.calc_unicode_seg(reply_message)
            class_Max = 160 - reply_len
            class_Str = self.users[user_id].data['classStr']
            class_len = t.calc_unicode_seg(class_Str)
            print(f"reply_len:{reply_len} class_len:{class_len} content_Max:{class_Max}")
            if class_len >= class_Max-20:
                class_Str = class_Str[0:17] + "...略"
            content_Max = 160 - reply_len - class_len
            print(f"reply_len:{reply_len} class_len:{class_len} content_Max:{content_Max}")
            content_len = t.calc_unicode_seg(self.users[user_id].data['content'])
            print(f"content_len :{content_len}")
            if content_len > content_Max:
                content = self.users[user_id].data['content'][0:content_Max-4] + "...略"
            else:
                content = self.users[user_id].data['content']

            reply_message = f"確認發送此訊息?\n教師名稱: {self.users[user_id].name}\n組別: {self.users[user_id].office}\n傳送班級: {class_Str}\n廣播內容:\n {content}\n結束廣播時間: {self.users[user_id].data['finish_date']}\n廣播音效: {sound}"
            message = TemplateSendMessage(
                alt_text='Button template',
                template=ButtonsTemplate(
                    # 把廣播訊息重複在此
                    text=reply_message,
                    actions=[
                        PostbackTemplateAction(
                            label='YES 我已確認',
                            data='action=@confirm_yes'
                        ),
                        PostbackTemplateAction(
                            label='NO 訊息有誤',
                            data='action=@confirm_no'
                        ),
                        DatetimePickerTemplateAction(
                        label='調整廣播結束日期',
                        data='action=@FD',
                        mode='date',
                        initial= str(date.today() + timedelta(days=1))
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data='action=@cancel'
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            print(e)
            self.api.push_message(user_id, TextSendMessage(text="確認按鈕傳送錯誤，請再試一次或聯絡管理員 錯誤代碼: E0001")) # 按鈕發生錯誤
            self.users[user_id].status = "Fs"
            self.users[user_id].data = t.Template.get_dataTemplate() 
    # 單獨班級廣播
    def handle_Bs2_1(self, event, user_id, text):
        try:
            database_class_list = self.db.getClassCodeList()
        except exc.OperationalError as oe:
            self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
        except Exception as e:
            error = f"{errorText}-handle_Bs2_1-.getClassCodeList()\n{e}"
            print(error)
            self.addError(error)
            self.api.push_message(user_id, TextSendMessage(text=f"⚠️資料庫處理時發生問題，請再試一次或洽 {contactInfo}"))

        if text in database_class_list:
            self.users[user_id].data['classLs'] = []
            self.users[user_id].data['classStr'] = text
            self.users[user_id].data['des_grade'] = text[0:2]
            self.users[user_id].data['des_class'] = text[2]
            if self.users[user_id].status == "Bs2.1":
                self.users[user_id].status = "Bs3"
                self.reply_cancel(event, "請輸入廣播文字")
            else:
                self.users[user_id].status = "Cs"
                self.sendConfirm(event, user_id)
        else:
            reply_message = "請輸入在範圍內的班級!"
            self.reply_cancel(event, reply_message)

    # 群發廣播
    def handle_Bs2_2(self, event, user_id, text):
        canSend = True
        number_groups = re.findall(self.pattern, text) # 使用正則表達式解析(僅可判斷以空格或逗號隔開)
        print(f"number_groups {number_groups}")
        if number_groups != []:
            number_groups = t.arrangeGetClass(number_groups)
            for group in number_groups:
                if len(group) == 1:   # 判斷為年級或班級
                    if group == "0":
                        self.users[user_id].data['classStr'] = "全年級 "
                        self.users[user_id].data['des_class'] = None
                        self.users[user_id].data['des_grade'] = None
                        self.users[user_id].data['classLs'] = ["0"]
                        
                    elif group == "4" and "0" not in number_groups:
                        self.users[user_id].data['classStr']  += "高中部 "
                        self.users[user_id].data['classLs'].append(group)
                    elif group == "5" and "0" not in number_groups:
                        self.users[user_id].data['classStr'] += "國中部 "
                        self.users[user_id].data['classLs'].append(group)
                    elif group == "6" :
                        self.users[user_id].data['classStr'] += "其他教室 "
                        self.users[user_id].data['classLs'].append(group)

                    else:
                        if  group in self.config['personal']['grade_list']:
                            if int(group) < 4:
                                if '4' not in number_groups:
                                    self.users[user_id].data['classLs'].append(group)
                                    self.users[user_id].data['classStr'] += "高" + group + " " 
                            else:
                                if '5' not in number_groups:
                                    self.users[user_id].data['classLs'].append(group)
                                    self.users[user_id].data['classStr'] += "國"+group +" " 
                        else:
                            reply_message = "請輸入正確數字範圍"
                            self.reply_cancel(event, reply_message)
                            canSend = False
                            break
                elif len(group) == 3:
                    try:
                        database_class_list = self.db.getClassCodeList()
                    except exc.OperationalError as oe:
                        self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                        return
                    except Exception as e:
                        error = f"{errorText}-handle_Admin1-.getClassCodeList()\n{e}"
                        print(error)
                        self.addError(error)
                        self.api.push_message(user_id, TextSendMessage(text=f"⚠️資料庫處理時發生問題，請再試一次或洽 {contactInfo}"))
                        return
                    else:
                        if group in database_class_list:
                            if int(group[0:1]) < 4: # 區分國高中 
                                # print(group)
                                if str(int(group[0:2]) - 9) not in number_groups:
                                    self.users[user_id].data['classStr'] += group + " "
                                    self.users[user_id].data['classLs'].append(group)
                                elif "6" not in number_groups:
                                    self.users[user_id].data['classStr'] += group + " "
                                    self.users[user_id].data['classLs'].append(group)
                            else:
                                if group[0:1] not in number_groups:
                                    self.users[user_id].data['classStr'] += group + " "
                                    self.users[user_id].data['classLs'].append(group)
                                elif "6" not in number_groups:
                                    self.users[user_id].data['classStr'] += group + " "
                                    self.users[user_id].data['classLs'].append(group)

                        else:
                            reply_message = "請輸入正確班級"
                            self.reply_cancel(event, reply_message)
                            self.users[user_id].data['classStr'] = ""
                            self.users[user_id].data['classLs'] = []
                            canSend = False
                            break
                        print(f"str {self.users[user_id].data['classStr']}")
                else:
                    reply_message = "請輸入有效代碼"
                    self.reply_cancel(event, reply_message)
                    canSend = False 

            if canSend:
                print(f"Bs2.2:{self.users[user_id].data['classStr']}")
                self.users[user_id].data['classStr'] = t.format_class(self.users[user_id].data['classStr'], self.db)
                print(f"Bs2.2-formated {self.users[user_id].data['classStr']}")
                if self.users[user_id].status == "Bs2.2":
                    self.users[user_id].status = "Bs3"
                    self.reply_cancel(event, "請輸入廣播文字")
                else:
                    self.users[user_id].status = "Cs"
                    self.sendConfirm(event, user_id)
        else:
            reply_message = "請輸入有效代碼"
            self.reply_cancel(event, reply_message)



    
    # 廣播訊息3
    def handle_Bs3(self, event, user_id, text):
        textLen = len(text)
        if textLen > 90:
            reply_message = f"輸入字數請勿超過90字, 目前字數{len(text)}"
            self.reply_cancel(event, reply_message)
        elif text.count('\n') > 4:
            reply_message = "訊息請勿超過5行，目前行數" + str(text.count('\n')+1)
            self.reply_cancel(event, reply_message)
        else:

            self.users[user_id].data['content'] = text

            self.users[user_id].data['finish_date'] = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            if self.users[user_id].status == "Bs3":
                if ExamStatus:
                    self.users[user_id].status = "Cs"
                    self.sendConfirm(event, user_id)
                else:
                    self.users[user_id].status = "Bs4"
                    self.sound_select(event, user_id)
            else:
                self.users[user_id].status = "Cs"
                self.sendConfirm(event, user_id)

    # 聲音選擇樣板
    def sound_select(self, event, user_id):
        try:
            message = TemplateSendMessage(
                alt_text='Button template',
                template=ButtonsTemplate(
                    title="是否需要廣播提醒音效?",
                    text="若點選是，顯示時則會有提醒音效",
                    actions=[
                        PostbackTemplateAction(
                            label='是',
                            data='action=@sound_yes'
                        ),
                        PostbackTemplateAction(
                            label='否',
                            data='action=@sound_no'
                        ),
                        PostbackTemplateAction(
                            label='取消',
                            data='action=@cancel'
                        )
                    ]
                )
            )
            self.api.reply_message(event.reply_token, message)
        except Exception as e:
            print(e)
            self.api.push_message(user_id, TextSendMessage(text="確認按鈕傳送錯誤，請再試一次或聯絡管理員 錯誤代碼: E0001")) # 按鈕發生錯誤


  

    # 廣播訊息5 接收結束廣播時間
    def postback_Bs5(self, event, user_id):
        selected_date = event.postback.params['date']
        selected_date = date(int(selected_date[0:4]), int(selected_date[5:7]), int(selected_date[8:]))
        todayDate = date.today()
        # print((nowTime > com), (selected_date - todayDate))
        if (selected_date - todayDate).days == 0:
            selected_date = selected_date + timedelta(days=1)
            self.users[user_id].data['finish_date'] = selected_date.strftime("%Y-%m-%d")
            self.users[user_id].status = "Cs"
            self.sendConfirm(event, user_id)
        elif (selected_date - todayDate).days >= 0:
            self.users[user_id].data['finish_date'] = selected_date.strftime("%Y-%m-%d")
            self.users[user_id].status = "Cs"
            self.sendConfirm(event, user_id)
        else:
            todayDate = todayDate.strftime("%Y/%m/%d")
            self.api.reply_message(event.reply_token, TextSendMessage(text=f"⚠️請輸入{todayDate}以後的日期"))

    # 設置教師個人資訊
    def postback_Ss(self, event, user_id):
        try:
            teacher = self.db.getTeacher(user_id)
        except exc.OperationalError as oe:
            print(oe)
            self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
        except Exception as e:
            error = f"{errorText}-postbac_Ss-.getTeacher()\n{e}"
            print(error)
            self.addError(error)
            reply_message = f"⚠️尋找教師資訊失敗，請嘗試封鎖此 Line bot 再解封鎖以重新登入或洽{contactInfo}"
            self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
        else:
            if teacher:
                self.users[user_id].status = "Ss1"
                reply_message = f"您好 {teacher.name}\n您所在的組別:{teacher.office}\n重新設定教師個人資訊\n請輸入您的姓名"
                self.reply_cancel(event, reply_message)
            else:
                self.users[user_id].status = "FSs1"
                reply_message = "設定教師個人資訊\n請輸入您的姓名"
                self.reply_cancel(event, reply_message, False)


    # 設置個人資訊一
    def handle_Ss1(self, event, user_id, text):
        status = self.users[user_id].status
        if len(text) < 10:
            self.users[user_id].name = text
            reply = f"您好 {text} \n請輸入您所在的組別"
            if status == "Ss1":
                self.users[user_id].status = "Ss2"
                self.reply_cancel(event, reply)
            else:
                self.users[user_id].status = "FSs2"
                self.reply_cancel(event, reply, False)
        else:
            reply = f"名稱請勿超過20字，目前字數 {len(text)}"
            self.api.reply_message(event.reply_token, TextSendMessage(text=reply))

        

    # 設置個人資訊二
    def handle_Ss2(self, event, user_id, text):
        status = self.users[user_id].status
        self.users[user_id].office = text
        if len(text) <= 5:
            reply = f"您的名字為: {self.users[user_id].name}\n所在組別: {self.users[user_id].office}"
            if status == "FSs2":
                self.sendSettingConfirm(event, reply, True)
            else:
                self.sendSettingConfirm(event, reply, False)
        else:
            reply = f"組別請勿超過5字，目前字數{len(text)}"
            self.api.reply_message(event.reply_token, TextSendMessage(text=reply))

    # 個人資訊確認按鈕
    def sendSettingConfirm(self, event, text, isFisrt):
        #try:
            if isFisrt:
                message = TemplateSendMessage(
                    alt_text='Button template',
                    template=ButtonsTemplate(
                       title="請問確認是否輸入錯誤",
                        text=f"{text}",
                        actions=[
                            PostbackTemplateAction(
                                label='YES 我已確認',
                                data='action=@CofS_Y'
                            ),
                            PostbackTemplateAction(
                                label='NO 訊息有誤',
                                data='action=@CofS_N'
                            ),
                        ]
                    )
                )
                

            else:
                message = TemplateSendMessage(
                    alt_text='Button template',
                    template=ButtonsTemplate(
                        title="請問確認是否輸入錯誤",
                        text=f"{text}",
                        actions=[
                            PostbackTemplateAction(
                                label='YES 我已確認',
                                data='action=@CofS_Y'
                            ),
                            PostbackTemplateAction(
                                label='NO 訊息有誤',
                                data='action=@CofS_N'
                            ),
                            PostbackTemplateAction(
                                label="取消",
                                data="action=@cancel"
                            )
                        ]
                    )
                )
            
            self.api.reply_message(event.reply_token, message)


    
    
    # 個人資訊確認按鈕處理 User Setting
    def postback_US(self, event, user_id, t):
        if t == "CofS_Y":
            try: 
                isAdmin = self.db.isAdmin(user_id)
            except exc.OperationalError as oe:
                print(oe)
                self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
            except Exception as e:
                error = f"{errorText}-implementV2_9-poostback_US()-self.db.isAdmin()\n{e}"
                print(error)       
                self.addError(error)
                reply_message = f"⚠️資料庫錯誤，請再試一次或是洽 {contactInfo}"
                self.api.push_message(user_id, TextSendMessage(text=reply_message))

            else:
                if isAdmin:  # 管理員處理
                    info = {'name': self.users[user_id].name, "office": self.users[user_id].office, "verifyStat": 1}
                    try:
                        self.db.insertTeaInfor(user_id, info)
                    except exc.operationalError as oe:
                        self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️資料庫連線錯誤，請再試一次"))                
                    
                    except Exception as e:
                        error = f"{errorText}-postback_US()-self.db.insertTeaInfor()\n{e}"
                        print(error)
                        self.addError(error)
                        reply_message = "⚠️插入資料時發生錯誤，請再試一次"

                        if self.users[user_id].status == "FSs2":
                            self.users[user_id].status = "FSs1"
                            reply_message = "老師好, 請輸入您的名稱"
                            self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
                        else:
                            self.users[user_id].status = "Ss1"
                            self.postback_Ss(event, user_id)
                    else:    
                        reply_message = "✅已更新"
                        self.users[user_id].status = "Fs"
                        self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

                elif self.users[user_id].status == "FSs2" or self.users[user_id].status == "Ss2":  # 一般使用者處理       
                    info = {'name': self.users[user_id].name, "office": self.users[user_id].office, "verifyStat": 0}
                    try:
                        self.db.insertTeaInfor(user_id, info)
                    except exc.OperationalError as oe:
                        print(oe)
                        self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️資料庫連線錯誤，請再試一次"))
                    except Exception as e:
                        error = f"{errorText}-postback_US-.insertTeaInfor()\n{e}"
                        print(error)
                        self.addError(error)
                        self.api.push_message(user_id, TextSendMessage(text=f"⚠️資料庫處理時發生問題，請再試一次或洽 {contactInfo}"))
                        
                        if self.users[user_id].status == "FSs2":
                            self.users[user_id].status = "FSs1"
                        else:
                            self.users[user_id].status = "Fs"
                    else:             
                        if user_id not in self.Confirm_List:    
                            self.Confirm_List.append(user_id)
                            reply_message = f"🔴有新教師加入‼\n以下為尚未驗證之列表，請透過數字鍵來表示要許可之用戶，其他將會被拒絕 ex 1-4 7 表示1到4號和7號都會許可\n代認證列表:"
                            for i in range(len(self.Confirm_List)):
                                try:
                                    temp = self.db.getTeacher(self.Confirm_List[i])
                                    if temp:
                                        reply_message += f"\n▶️{i+1}) 教師: {temp.name} 組別: {temp.office}"
                                except exc.operationError as oe:
                                    print(oe)
                                    self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️資料庫連線錯誤，請在試一次"))
                                    return
                                except Exception as e:
                                    error = f"{errorText}-postback_US-.getTeacher()\n{e}"
                                    print(error)
                                    self.addError(error)
                                    self.push_message(user_id, TextSendMessage(text=f"⚠️資料庫處理時發生問題，請再試一次或洽 {contactInfo}"))
                                    return
                        try:
                            AdminList = self.db.findAdmin()
                        except exc.OperationalError as oe:
                            print(oe)
                            self.api.reply_message(event.reply_token, TextSendMessage(text=f"⚠️伺服器連線錯誤，請在試一次"))
                            if self.users[user_id].status == "FSs2":
                                self.users[user_id].status = "FSs1"
                            else:
                                self.users[user_id].status = "Fs"
                        except Exception as e:
                            print(f"*An Error in postback_US\n{e}")
                            self.addError(e)
                            reply_message = "⚠️尋找管理員時發生錯誤，請再試一次。"    
                            self.api.push_message(user_id, TextSendMessage(text=reply_message))
                            if self.users[user_id].status == "FSs2":
                                self.users[user_id].status = "FSs1"
                            else:
                                self.users[user_id].status = "Fs"
                            return
                        else:
                            if AdminList:
                                for Admin in AdminList:
                                    if Admin not in self.users:
                                        self.users[Admin] = Teacher(Admin, isAdm=1, status="ACs", preStatus="Fs")
                                    else:
                                        self.users[Admin].preStatus = self.users[Admin].status
                                        self.users[Admin].status = "ACs"
                                    self.api.push_message(
                                        Admin, TextSendMessage(text=reply_message))
                                reply = "✅已送交，等待管理員確認"
                                self.api.reply_message(event.reply_token, TextSendMessage(text=reply))
                                self.users[user_id].status = "Ss3"
                            else:
                                reply_message = "⚠️資料庫錯誤，沒有管理員在資料中\n請聯絡 # 9611資訊組"
                                name = input("請輸入管理員名稱> ")
                                office = input("請輸入管理員所在組別> ")
                                try:
                                    self.db.insertAdmin(user_id, {'name':name, 'office':office, 'verifyStat':1, 'isAdmin':1})
                                except exc.OperationalError as oe:
                                    print("資料庫連線問題，請再試一次")
                                    sys.exit()
                                except Exception as e:
                                    error = f"{errorText}-postback_US-.insertAdmin()\n{e}"
                                    print(error)
                                    self.addError(error)
                                    sys.exit()



        elif t == "CofS_N":
            try:
                isRegis = self.db.findTeacher(user_id)
                if self.users[user_id].status == "Ss2":
                    self.users[user_id].status = "Ss1" 
                    if isRegis:
                        reply_message = "重新設定教師個人資訊\n請輸入您的姓名>"
                        self.reply_cancel(event, reply_message)
                    else:
                        reply_message = "設定教師個人資訊\n請輸入您的姓名>"
                        self.reply_cancel(event, reply_message)

                elif self.users[user_id].status == "FSs2":
                    self.users[user_id].status = "FSs1"  
                    reply_message = "請輸入您的姓名>"
                    self.reply_cancel(event, reply_message, False)
            except exc.OperationalError as oe:
                print(oe)
                self.api.reply_message(event.reply_token, TextSendMessage(text=f"⚠️伺服器連線錯誤，請在試一次"))
            except Exception as e:
                error = f"{errorText}-postback_US-.findTeacher()\n{e}"
                print(error)
                self.addError(error)
                self.api.push_message(user_id, TextSendMessage(text=f"⚠️資料庫處理時發生問題，請再試一次或洽 {contactInfo}"))
                
    # 管理員許可1
    def handle_Admin1(self, event, user_id,text):
        result = re.findall(self.AdmConPattern, text)
    
        note = False
        reply_message = "已更新:"
        if result != None:
            for scope in result:
                print(scope)
                if "-" in scope:
                    if int(scope[0:1]) >= 1 and int(scope[2:3]) <= len(self.Confirm_List):
                        for i in range(int(scope[0:1]), int(scope[2:])+1, 1):
                            try:
                                reply_message += f"\n▶️ {self.db.getTeacher(self.Confirm_List[i-1], ['name'])[0]}✅"
                                ack = self.db.modifyVerifyStat(self.Confirm_List[i-1])

                            except exc.OperationalError as oe:
                                print(oe)
                                self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                                return 
                            except Exception as e:
                                error = f"{errorText}-handle_Admin1-.modifyVerifyStat()\n{e}"
                                print(error)
                                self.addError(error)
                                self.api.push_message(user_id, TextSendMessage(text=f"⚠️資料庫處理時發生問題，請再試一次或洽 {contactInfo}"))
                                return
                            else:
                                if ack == True:
                                    self.api.push_message(self.Confirm_List[i-1], TextSendMessage(text="✅管理員已認證，歡迎您加入"))
                                    self.users[self.Confirm_List[i-1]].status = "Fs"
                                    self.Confirm_List[i-1] = ""

                    else:
                        note = True
                        reply_message = "請輸入在範圍內的數字"
                        self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
                else:
                    # print(scope)
                    if int(scope) >= 1 and int(scope) <= len(self.Confirm_List):
                        try:
                            reply_message += f"\n▶️ {self.db.getTeacher(self.Confirm_List[int(scope) - 1], ['name'])[0]}✅"
                            ack = self.db.modifyVerifyStat(self.Confirm_List[int(scope) - 1])
                        except exc.OperationalError as oe:
                            print(oe)
                            self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️伺服器連線錯誤，請在試一次"))
                            return 
                        except Exception as e:
                            error = f"{errorText}-handle_Admin1-.modifyVerifyStat()\n{e}"
                            print(error)
                            self.addError(error)
                            self.api.push_message(user_id, TextSendMessage(text=f"⚠️資料庫處理時發生問題，請再試一次或洽 {contactInfo}"))
                            return
                        else:
                            if ack == True:
                                self.api.push_message(self.Confirm_List[int(scope)-1], TextSendMessage(text="管理員已認證，歡迎您加入"))
                                self.users[self.Confirm_List[int(scope)-1]].status = "Fs"
                                self.Confirm_List[int(scope)-1] = ""

                    else:
                        note = True
                        reply_message = "請輸入在範圍內的數字"
                        self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
                        
            if not note:
                for user in self.Confirm_List:
                    if user != "":
                        try:
                            reply_message += f"\n▶️ {self.db.getTeacher(user, ['name'])[0]}❌"

                            self.db.DelTeacherData(user)
                        except exc.OperationalError as oe:
                            print(oe)
                            self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️資料庫連線錯誤，請在試一次"))
                            return
                        except Exception as e:
                            error = f"{errorText}-handleAdmin1()-self.db.DelTeacherData()\n{e}"
                            print(error)
                            self.addError(error)
                            self.users[user_id].status = "ACs"
                            self.api.push_message(user_id, TextSendMessage(text="資料庫刪除錯誤，"))
                            return
                        else:
                            self.api.push_message(user, TextSendMessage(text="很抱歉，管理員已否決您的申請。"))


                self.Confirm_List = []
                # print(reply_message)
                self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
                self.users[user_id].status = "Fs"
                try:
                    name =  self.db.getTeacher(user_id).name
                except exc.OperationalError as oe:
                    print(oe)
                    name = "其他管理員"
                except Exception as e:
                    error = f"{errorText}-handler_Admin1-.getTeacher()\n{e}"
                    print(error)
                    self.addError(error)
                    name = "其他管理員"

                reply_message = f"{name} 已認證，您可繼續使用廣播功能"
                try:
                    AdminList = self.db.findAdmin()
                except Exception as e:
                    error = f"{errorText}-handler_Admin1-.getTeacher()\n{e}"
                    print(error)
                    self.addError(error)
                    return
                else:
                    if AdminList:
                        for Admin in AdminList:
                            if Admin not in self.users:
                                self.users[Admin] = Teacher(Admin, isAdm=1, status="Fs")
                                self.api.push_message(
                                Admin, TextSendMessage(text=reply_message))
                            else:
                                prestatus = self.users[Admin].preStatus
                                if prestatus != None and prestatus != "ACs":
                                    self.users[Admin].status = prestatus
                                else:
                                    self.users[Admin].status = "Fs"
                                print(f"Admin:{Admin} status:{self.users[Admin].status}")
                                if Admin != user_id:
                                    self.api.push_message(
                                    Admin, TextSendMessage(text=reply_message))

                                if self.users[Admin].status == "Bs1":
                                    message = TemplateSendMessage(
                                        alt_text='Button Template',
                                        template=ButtonsTemplate(
                                            title="請選擇發送類型",
                                            text="個別發送限定一個班級，群體發送可發送給多個班級",
                                            actions=[
                                                PostbackTemplateAction(
                                                    label='個別發送',
                                                    data='action=@select_class'
                                                ),
                                                PostbackTemplateAction(
                                                    label='群發年級',
                                                    data='action=@select_group'
                                                ),
                                                PostbackTemplateAction(
                                                    label='取消',
                                                    data='action=@cancel'
                                                )
                                            ]
                                        )
                                    )
                                    self.api.push_message(Admin, message)
                                elif self.users[Admin].status == "Ss1":
                                    reply_message = "重新設定教師個人資訊\n請輸入您的姓名"
                                    message = TemplateSendMessage(
                                        alt_text='Text-Cancel template',
                                        template=ButtonsTemplate(
                                            title=None,
                                            text= text,
                                            actions=[
                                                PostbackAction(
                                                    label='取消',
                                                    data='action=@cancel'
                                                )
                                            ]
                                        )
                                    )
                                    self.api.push_message(Admin, message)
                                    
                                # 個人資訊設定2
                                elif self.users[Admin].status == "Ss2":
                                    reply = f"您好 {self.users[Admin].name} \n請輸入您所在的組別"
                                    message = TemplateSendMessage(
                                        alt_text='Text-Cancel template',
                                        template=ButtonsTemplate(
                                            title=None,
                                            text= reply,
                                            actions=[
                                                PostbackAction(
                                                    label='取消',
                                                    data='action=@cancel'
                                                )
                                            ]
                                        )
                                    )
                                    self.api.push_message(Admin, message)
                                elif self.users[Admin].status == "Ss3":
                                    message = TemplateSendMessage(
                                        alt_text='Button template',
                                        template=ButtonsTemplate(
                                            # 把廣播訊息重複在此
                                            text=f"請問確認是否輸入錯誤\n名稱: {self.users[Admin].name}\n組別:{self.users[Admin].office}",
                                            actions=[
                                                PostbackTemplateAction(
                                                    label='YES 我已確認',
                                                    data='action=@CofS_Y'
                                                ),
                                                PostbackTemplateAction(
                                                    label='NO 訊息有誤',
                                                    data='action=@CofS_N'
                                                ),
                                                PostbackTemplateAction(
                                                    label="取消",
                                                    data="action=@cancel"
                                                )
                                            ]
                                        )
                                    )
                                # 廣播訊息 2.1
                                elif self.users[Admin].status == "Bs2.1":
                                    reply_message = "個別發送，請輸入要發送的班級 ex: 703"
                                    message = TemplateSendMessage(
                                        alt_text='Text-Cancel template',
                                        template=ButtonsTemplate(
                                            title=None,
                                            text= reply_message,
                                            actions=[
                                                PostbackAction(
                                                    label='取消',
                                                    data='action=@cancel'
                                                )
                                            ]
                                        )
                                    )
                                    self.api.push_message(Admin, message)
                                
                                # 廣播訊息 2.2
                                elif self.users[Admin].status == "Bs2.2":
                                    message = TemplateSendMessage(
                                        alt_text='Button Template',
                                        template=ButtonsTemplate(
                                            # 
                                            text=f"選擇群發年級!\n請輸入傳送班級(請輸入中文字後的代號)\n 全年級 0 \n 高一 1 \n 高二 2 \n 高三 3 \n 高中 4 \n 國中 5 \n 七年級 7 \n 八年級 8 \n 九年級 9\n 特定跳班級 班級三位數並用逗號或空格隔開",
                                            actions=[
                                                PostbackTemplateAction(
                                                    label='取消',
                                                    data='action=@cancel'
                                                )
                                            ]
                                        )
                                    )
                                    self.api.push_message(Admin, message)
                                    
                                # 廣播訊息 3
                                elif self.users[Admin].status == "Bs3":
                                    reply_message = "請輸入廣播訊息"
                                    message = TemplateSendMessage(
                                        alt_text='Text-Cancel template',
                                        template=ButtonsTemplate(
                                            title=None,
                                            text= reply_message,
                                            actions=[
                                                PostbackAction(
                                                    label='取消',
                                                    data='action=@cancel'
                                                )
                                            ]
                                        )
                                    )
                                    self.api.push_message(Admin, message)
                                elif self.users[Admin].status == "Cs":
                                    Textlen = self.count_chinese_characters(self.users[Admin].data['content']) * 3
                                    Textlen += (len(self.users[Admin].data['content']) - self.count_chinese_characters(self.users[Admin].data['content']))
                                    if  Textlen > 160:
                                        content = self.users[Admin].data['content'][0:20] + "\n"+"...以下省略"
                                    else:
                                        content = self.users[Admin].data['content']

                                    message = TemplateSendMessage(
                                        alt_text='Button template',
                                        template=ButtonsTemplate(
                                            # 把廣播訊息重複在此
                                            text=f"你確定要發送此則訊息嗎？\n(請檢察將送出的訊息是否正確)\n教師名稱: {self.users[Admin].name}\n組別: {self.users[Admin].office}\n傳送班級: {self.users[Admin].data['classStr']}\n廣播內容:\n  {content}\n結束廣播時間:{self.users[Admin].data['finish_date']}",
                                            actions=[
                                                PostbackTemplateAction(
                                                    label='YES 我已確認',
                                                    data='action=@confirm_yes'
                                                ),
                                                PostbackTemplateAction(
                                                    label='NO 訊息有誤',
                                                    data='action=@confirm_no'
                                                ),
                                                DatetimePickerTemplateAction(
                                                label='調整廣播結束日期',
                                                data='action=@FD',  
                                                mode='date'
                                                ),
                                                PostbackTemplateAction(
                                                    label='取消',
                                                    data='action=@cancel'
                                                )
                                            ]
                                        )
                                    )
                                    self.api.push_message(Admin, message)
                    else:
                        print("Error in findAdmin() There are no admin in database.")


            else:
                reply_message = "輸入錯誤, 請使用 ""-"" 來指定範圍，或是輸入特定數字"
                self.api.reply_message(
                event.reply_token, TextSendMessage(text=reply_message))


    # 空閒
    def handle_Fs(self, event, user_id, text):
        try:
            isAdmin = self.db.isAdmin(user_id)
        except exc.OperationalError as oe:
            print(oe)
            self.api.reply_message(event.reply_token, TextSendMessage(text="⚠️資料庫連線錯誤，請在試一次"))
        except Exception as e:
            error = f"{errorText}-handle_Fs()-self.db.isAdmin()\n{e}"
            print(error)
            self.addError(error)
            reply_message = "尋找錯誤，請再試一次或是洽 #9611資訊組"
            self.api.push_message(user_id, TextSendMessage(text=reply_message))
            
        else:
            if self.users[user_id].status != "Ss3":
                if text == "發送廣播":
                    self.postback_Bs(event, user_id)
                elif text == "重新設定個人資訊":
                    self.postback_Ss(event, user_id)
                elif text == "歷史訊息":
                    self.postback_Hs(event, user_id)
                elif text == "幫助":
                    self.postback_Help(event)
                elif not isAdmin:
                    self.SendButton(event, user_id)
                elif text == "@resetBot":
                    self.users[user_id].status = "Rs" # Reset status
                    message = TemplateSendMessage(
                        alt_text='Button template',
                        template=ButtonsTemplate(
                            # 重啟確認
                            text="⚠️⚠️你確認要重啟程式?正在執行的流程可能會遺失資料?",
                            actions=[
                                PostbackTemplateAction(
                                    label='是',
                                    data='action=@reset_yes'
                                ),
                                PostbackTemplateAction(
                                    label='否',
                                    data='action=@reset_no'
                                ),
                            ]
                        )
                    )
                    self.api.reply_message(event.reply_token, message)

                elif text == "@userList":
                    try:
                        AllTeacher = self.db.GetAllTeacherID() # 取得所有教師ID
                    except exc.OperationalError as oe:
                        print(oe)
                        self.api.reply_message(event.reply_toekn, TextSendMessage(text="⚠️資料庫連線錯誤，請再試一次"))
                    except Exception as e:
                        error = f"{errorText}-handle_Fs-self.db.GetAllTeacherID()\n{e}"
                        print(error)
                        self.addError(error)
                        reply_message = "資料庫取得錯誤，請再試一次或是洽 #9611資訊組"
                        self.api.push_message(user_id, TextSendMessage(text=reply_message))
                        
                    else: 
                        if AllTeacher:
                            reply_message = f"🔴以下是教師列表 共{len(AllTeacher)}位:"
                            for user in AllTeacher:
                                try:
                                    get = self.db.getTeacher(user) # 因透過資料庫取得教師ID，故不會有空值
                                    if get:
                                        if user != user_id:
                                            reply_message += "\n▶️ "+ get.name+" "+get.office
                                        else:
                                            reply_message += "\n▶️ "+get.name+" (您)"+" "+get.office
                                except Exception as e:
                                    error = f"{errorText}-handler_Fs()\n{e}"
                                    print(error)
                                    self.addError(error)
                                    reply_message = "資料庫錯誤，請再試一次或是查看錯誤訊息"
                                    break
                            self.api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
                elif text == "@delData":
                    self.users[user_id].status = "Ds" # Reset status

                    message = TemplateSendMessage(
                        alt_text='Button template',
                        template=ButtonsTemplate(
                            title="⚠️⚠️你確認要刪除所有資料庫中資料?",
                            text="點選是來刪除資料，點選否則取消",
                            actions=[
                                PostbackTemplateAction(
                                    label='是',
                                    data='action=@del_yes'
                                ),
                                PostbackTemplateAction(
                                    label='否',
                                    data='action=@del_no'
                                ),
                            ]
                        )
                    )
                    self.api.reply_message(event.reply_token, message)
                else:
                    self.SendButton_Adm(event, user_id)  

  
    

    
    # 歷史訊息按紐處理
    def postback_Hs(self, event, user_id):
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=URIAction(label="查看歷史訊息", uri=f"{self.webhook_url[:-8]}/realtimedata/{user_id}"))
        ])
        
        # 回應訊息，並附上 Quick Reply 按鈕
        reply_message = TextSendMessage(
            text="點擊按鈕查看歷史訊息",
            quick_reply=quick_reply
        )
        self.api.reply_message(event.reply_token, reply_message)

