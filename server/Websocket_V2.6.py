import asyncio
import json
import os
import websockets
import requests
from mysql.connector import Error
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import weakref
from contextlib import contextmanager
import gc

# 請於此設定伺服器和 Line Bot 相關的連接信息
ip = "192.168.88.1"
port = 80
line_bot_server_url = "https://d8b6-140-119-99-80.ngrok-free.app/return"

# 使用 WeakKeyDictionary 儲存客戶端與監控數據，減少記憶體使用
client_data = weakref.WeakKeyDictionary()
monitor_data = weakref.WeakKeyDictionary()

try:
    # 從環境變數中獲取資料庫密碼
    database_pass = os.getenv("dbv1p")
    # 建立資料庫引擎，連接到 MySQL 資料庫
    engine = create_engine(f"mysql+mysqlconnector://root:{database_pass}@localhost/dbV1", pool_size=50)

    # 定義基礎類，並繼承自 SQLAlchemy 的 Base 類
    Base = declarative_base()

    # 定義 DataAccess 資料表模型，用於存取資料庫中的數據
    class DataAccess(Base):
        __tablename__ = 'data'
        id = Column(Integer, primary_key=True)
        name = Column(String(15))
        content = Column(String(300))
        is_new = Column(Integer)
        time = Column(String(25))
        office = Column(String(5))
        des_grade = Column(String(2))
        des_class = Column(String(1))
        finish_date = Column(String(10))
        sound = Column(Integer)

    # 定義 ClassAccess 資料表模型，用於儲存班級資訊
    class ClassAccess(Base):
        __tablename__ = 'class_list'
        id = Column(Integer, primary_key=True)
        classCode = Column(String(3))
        className = Column(String(10))

    # 建立資料庫會話
    Session = sessionmaker(bind=engine)

    # 建立資料表
    Base.metadata.create_all(engine)
except SQLAlchemyError as e:
    print("Error setting up DAL :", e)

# 檢查必要功能是否可用
def check_funcs():
    try:
        check_one = send_message_to_user(None, None, None, 1)
        check_two = send(None, None, None, None, 1)
        check_three = send_message_to_line_bot(None, None, None, None, 1)
        check_four = New_data_added(1)
        if check_one and check_two and check_three and check_four:
            return True
        else:
            return False
    except Exception as e:
        print("Error in check_funcs:", e)
        return False

# 創建上下文管理器以安全地處理資料庫會話
@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

# 實現分頁查詢，用來批次處理大量資料
def paginate(query, page_size=100):
    offset = 0
    while True:
        batch = query.limit(page_size).offset(offset).all()
        if not batch:
            break
        yield from batch
        offset += page_size

# 處理來自 WebSocket 的訊息，並根據不同的訊息類型作出相應的處理
async def handle_message(ws):
    try:
        while True:
            try:
                # 設定 5 秒超時來接收訊息
                received_message = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))
                if not received_message.get("header") == "M1":
                    print("Received : ", received_message)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosedError as e:
                print("WebSocket connection closed: ", e)
                break
            except websockets.exceptions.ConnectionClosedOK:
                break
            except Exception as e:
                print(f"Other error: {e}")
                break

            # 根據訊息標頭進行不同處理
            if received_message.get("header") == "A0":
                await handle_a0_message(ws, received_message)
            elif received_message.get("header") == "A2":
                client_data[ws]["returned_id"] = received_message.get("id")
            elif received_message.get("header") == "M1":
                await handle_m1_message(ws, received_message)
    except Exception as e:
        print("Error in handle_message:", e)
    finally:
        # 當 WebSocket 關閉時清理對應的客戶端數據
        if ws in client_data:
            del client_data[ws]
        if ws in monitor_data:
            del monitor_data[ws]

# 處理 A0 類型的訊息，將班級數據新增到資料庫中
async def handle_a0_message(ws, received_message):
    try:
        for key in client_data:
            if client_data[key].get("classCode") == received_message.get("classCode"):
                To_cli_msg = {"header": "S0", "result": False}
                await send(ws, To_cli_msg, 0, "S0", 0)
                await ws.close()
                return

        # 將收到的班級信息存入 client_data
        client_data[ws] = {
            "classCode": received_message.get("classCode"),
            "className": received_message.get("className"),
            "returned_id": None
        }
        
        with session_scope() as db_session:
            check = db_session.query(ClassAccess).filter_by(classCode=client_data[ws].get("classCode")).all()
            if not check:
                data_to_insert = ClassAccess(classCode=client_data[ws].get("classCode"), className=client_data[ws].get("className"))
                db_session.add(data_to_insert)

        To_cli_msg = {"header": "S0", "result": True}
        await send(ws, To_cli_msg, 0, "S0", 0)
    except Exception as e:
        print("Error in handle_a0_message:", e)

# 處理 M1 類型的訊息，並檢查伺服器的狀態
async def handle_m1_message(ws, received_message):
    monitor_data[ws] = received_message.get("ping")
    if check_funcs():
        message = {"header": "S2", "ping": monitor_data[ws]}
    else:
        message = {"header": "S2", "ping": "failed"}
    await send(ws, message, 0, "S2", 0)

# 監控資料庫中新數據的加入，並發送訊息給各班級
async def New_data_added(check):
    if check == 1: return True
    loop_count = 0
    while True:
        try:
            with session_scope() as db_session:
                query = db_session.query(DataAccess).filter_by(is_new=1)
                for datas in paginate(query):
                    record = {
                        "id": datas.id,
                        "name": datas.name,
                        "class": datas.des_grade + datas.des_class,
                        "content": datas.content,
                        "is_new": datas.is_new,
                        "time": datas.time.strftime("%Y-%m-%d %H:%M:%S"),
                        "office": datas.office,
                        "finish_date": datas.finish_date,
                        "sound": datas.sound
                    }
                    dest = format_destination(datas.des_grade, datas.des_class)
                    sent = await send_message_to_user(record, str(datas.id), dest, 0)
                    
                    if sent == "u":
                        print("data sending time exceeded, ID = ", datas.id)
                        send_message_to_line_bot(datas.time.strftime("%Y-%m-%d %H:%M:%S"), datas.name, dest, datas.content, 0)
                    
                    if sent:
                        db_session.query(DataAccess).filter_by(id=datas.id).update({"is_new": 0})
        except Exception as e:
            print("Error in New_data_added:", e)
        
        # 定期進行垃圾回收，避免記憶體洩漏
        loop_count += 1
        if loop_count % 100 == 0:
            gc.collect()
        
        await asyncio.sleep(1)

# 格式化目標班級
def format_destination(des_grade, des_class):
    if des_grade[1] in ["7", "8", "9"]:
        return des_grade[1] + des_grade[0] + des_class
    return des_grade + des_class

# 發送訊息至目標班級
async def send_message_to_user(message, id, dest, check):
    try:
        if check == 1 : return True
        # 遍歷客戶端數據
        for ws, cls_infor in client_data.items():
            # 檢查是否為對應的班級
            if int(cls_infor["classCode"]) == int(dest):
                # 準備發送的數據
                data={ "header": "S1", "message": message }
                return await send(ws, data, id, "S1", 0)
    except Exception as e:
        print("Error in send_message_to_user:", e)

# 發送訊息的輔助函數
async def send(ws, message, id, header, check):
    try:
        if check == 1 : return True
        message = json.dumps(message, ensure_ascii=False)
        try:
            await ws.send(message)
        except Error as e:
            print("Error sending message to user : ", e)
        
        break_at = 0
        if header == "S1":
            while break_at < 600:
                if ws in client_data and client_data[ws]["returned_id"] == int(id):
                    print("data sending success, id : ", id)
                    return "s"
                await asyncio.sleep(0.1)
                break_at += 1
            return "u"
        else:
            return "s"
    except Exception as e:
        print("Error in send:", e)

# 當未成功發送，發送錯誤訊息到 Line Bot 伺服器
def send_message_to_line_bot(time, name, cls, content, check):
    try:
        if check == 1 : return True
        data = {"time": time, "name": name, "cls": cls, "content": content}
        try:
            response = requests.post(line_bot_server_url, json=data)
            response.raise_for_status()
            print("Message sent successfully to Line Bot Server")
        except requests.exceptions.RequestException as e:
            print("Failed to send message to Line Bot Server. Error:", e)
    except Exception as e:
        print("Error in send_message_to_line_bot:", e)

# 啟動 WebSocket 伺服器
async def start_server():
    try:
        server = await websockets.serve(handle_message, ip, port)
        print('WebSocket server started')
        # 啟動監聽新資料的任務
        asyncio.create_task(New_data_added(0))
        await server.wait_closed()
    except Exception as e:
        print("Error in start_server:", e)

# 主程式入口
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server())