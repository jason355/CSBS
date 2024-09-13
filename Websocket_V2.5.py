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

# Please set up internet information here
ip = "192.168.56.1"
port = 8000
line_bot_server_url = "https://d8b6-140-119-99-80.ngrok-free.app/return"
# Please set up internet information here

# create client data dict       format: client_data[ws] {"classCode", "className", "returned_id"}
client_data = {}

#create monitor data dict
monitor_data = {}

try:
    # access environment variable to get db password
    database_pass = os.getenv("dbv1p")
    # create database engine
    engine = create_engine(f"mysql+mysqlconnector://root:{database_pass}@localhost/dbV1", pool_size=50)

    # create model base class
    Base = declarative_base()

    # create model class
    class DataAccess(Base):
        __tablename__ = 'data'
        id = Column(Integer, primary_key=True)
        name = Column(String(15))
        #lineID = Column(String(45))
        #hash = Column(String(40))
        content = Column(String(300))
        is_new = Column(Integer)
        time = Column(String(25))
        office = Column(String(5))
        des_grade = Column(String(2))
        des_class = Column(String(1))
        finish_date = Column(String(10))
        sound = Column(Integer)

    class ClassAccess(Base):
        __tablename__ = 'class_list'
        id = Column(Integer, primary_key=True)
        classCode = Column(String(3))
        className = Column(String(10))

    # create session
    Session = sessionmaker(bind=engine)

    # create database table
    Base.metadata.create_all(engine)
except SQLAlchemyError as e:
    print("Error setting up DAL :", e)


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


async def handle_message(ws):
    try:
        # create a message list of every client's message
        msg = {}
        while True:
            # receive the class number which sent by client
            try:
                received_message = json.loads(await asyncio.wait_for(ws.recv(), timeout=5.0))  # Set the expired time to 5s
                if not received_message.get("header") == "M1":
                    print("Received : ", received_message)
            except asyncio.TimeoutError:
                continue
            except websockets.exceptions.ConnectionClosedError as e:
                print("WebSocket connection closed: ", e)
                await ws.close()
                break
            except websockets.exceptions.ConnectionClosedOK as e:
                await ws.close()
                break
            except Exception as e:
                print(f"Other error: {e}")
                await ws.close()
                break
            # class connect to server
            if received_message.get("header") == "A0":
                try:
                    # check if the class has already existed in client_data
                    for key in client_data:
                        if client_data[key].get("classCode") == received_message.get("classCode"):
                            To_cli_msg = {
                                "header": "S0",
                                "result": False
                            }
                            await send(ws, To_cli_msg, 0, "S0", 0)
                            await ws.close()
                            break
                    client_data[ws] = {
                        "classCode": received_message.get("classCode"),
                        "className": received_message.get("className"),
                        "returned_id": None
                    }
                    client_info = client_data[ws]
                    print(f"\n*added new class*\nclass code : {client_info['classCode']}\nclass name : {client_info['className']}")
                    # check if the class has already existed in database, if not, add it to database
                    try:
                        # create database session
                        db_session = Session()
                        try:
                            # fetch datas
                            check = db_session.query(ClassAccess).filter_by(classCode=client_data[ws].get("classCode")).all()
                            # if that is a new class
                            if not check:
                                data_to_insert = ClassAccess(classCode=client_data[ws].get("classCode"), className=client_data[ws].get("className"))
                                db_session.add(data_to_insert)
                                db_session.commit()
                        except Error as e:
                            print("Error fetching datas :", e)
                    except Error as e:
                        print("Error creating database session :", e)
                    finally:
                        # when the processing of a single data is ended, close the session
                        db_session.close()
                    # return to client that if the adding was successful or not
                    To_cli_msg = {
                        "header": "S0",
                        "result": True
                    }
                    await send(ws, To_cli_msg, 0, "S0", 0)
                except Exception as e:
                    print("Error in A0 section:", e)
            elif received_message.get("header") == "A2":
                client_data[ws]["returned_id"] = received_message.get("id")
            elif received_message.get("header") == "M1":
                monitor_data[ws] = received_message.get("ping")
                if check_funcs():
                    message = {
                        "header" : "S2",
                        "ping" : monitor_data[ws]
                    }
                else:
                    message = {
                        "header" : "S2",
                        "ping" : "failed"
                    }
                message = json.dumps(message, ensure_ascii=False)
                try:
                    # send message
                    await ws.send(message)
                except Error as e:
                    print("Error sending message to monitor : ", e)
        # while disconnected, delete the data of the client
        if ws in client_data:
            del client_data[ws]
    except Exception as e:
        print("Error in handle_message:", e)


async def send_message_to_user(message, id, dest, check):
    try:
        if check == 1 : return True
        # Traverse every data
        for ws, cls_infor in client_data.items():
            # if it's the correct class, start sending process
            if int(cls_infor["classCode"]) == int(dest):
                # produce for-cli-data
                data={
                    "header": "S1",
                    "message": message 
                }
                return await send(ws, data, id, "S1", 0)
    except Exception as e:
        print("Error in send_message_to_user:", e)


async def send(ws, message, id, header, check):
    try:
        if check == 1 : return True
        # convert message to JSON string
        message = json.dumps(message, ensure_ascii=False)
        try:
            # send message
            await ws.send(message)
        except Error as e:
            print("Error sending message to user : ", e)
        break_at = 0
        # waiting 60s for the client's return value to finish the sending process
        if header == "S1":
            while break_at < 600:
                if ws in client_data:
                    # check if the returned_id exists and is not None
                    if client_data[ws]["returned_id"] is not None and int(client_data[ws]["returned_id"]) == int(id):
                        print("data sending success, id : ", id)
                        # if client did return the value, return "u"
                        return "s"
                await asyncio.sleep(0.1)
                break_at += 1
            # if client didn't return the value, return "u"
            return "u"
        else:
            return "s"
    except Exception as e:
        print("Error in send:", e)


def send_message_to_line_bot(time, name, cls, content, check):
    try:
        if check == 1 : return True
        # setting the information of http sending
        data = {"time": time, "name": name, "cls": cls, "content": content}
        try:
            # post the data on the url
            response = requests.post(line_bot_server_url, json=data)
            response.raise_for_status()
            print("Message sent successfully to Line Bot Server")
        except requests.exceptions.RequestException as e:
            print("Failed to send message to Line Bot Server. Error:", e)
    except Exception as e:
        print("Error in send_message_to_line_bot:", e)


async def New_data_added(check):
    try:
        if check == 1 : return True
        # detect new datas duplicately
        while True:
            try:
                # create database session
                db_session = Session()
                try:
                    # fetch datas
                    check = db_session.query(DataAccess).filter_by(is_new=1).all()
                    # if there are new datas
                    if check:
                        # access every single data
                        for datas in check:
                            # produce for-cli-data
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
                            # declare check variable
                            sent = None
                            # modify the format of sending destination
                            if datas.des_grade[1] == "7" or datas.des_grade[1] == "8" or datas.des_grade[1] == "9":
                                dest = datas.des_grade[1] + datas.des_grade[0] + datas.des_class
                            else:
                                dest = datas.des_grade + datas.des_class
                            # check if the class in the client_data
                            try:
                                for key in client_data:
                                    if int(client_data[key]["classCode"]) == int(dest):
                                        # send message
                                        sent = await send_message_to_user(record, str(datas.id), dest, 0)
                            except Error as e:
                                print("Error occured : ", e)
                            # check if sending unsuccessful
                            if sent == "u":
                                print("data sending time exceeded, ID = ", datas.id)
                                # send message to linebot to inform the teacher the sending was failed
                                try:
                                    send_message_to_line_bot(datas.time.strftime("%Y-%m-%d %H:%M:%S"), datas.name, dest, datas.content, 0)
                                except Error as e:
                                    print("Error Sending message to linebot :", e)
                            # anyhow, set the status of the message to old message
                            if sent:
                                try:
                                    # update the data's status and commit to database
                                    db_session.query(DataAccess).filter_by(id=datas.id).update({"is_new": 0})
                                    db_session.commit()
                                except Error as e:
                                    print("Error updating data :", e)
                except Error as e:
                    print("Error fetching datas :", e)
            except Error as e:
                print("Error creating database session :", e)
            finally:
                # when the processing of a single data is ended, close the session to avoid server's overload
                db_session.close()
                # create interval between the duplicated detection
                await asyncio.sleep(1)
    except Exception as e:
        print("Error in New_data_added:", e)


async def start_server():
    try:
        # start the server
        server = await websockets.serve(handle_message, ip, port)
        print('WebSocket server started')
        # create duplicated detection
        asyncio.create_task(New_data_added(0))
        await server.wait_closed()
    except Exception as e:
        print("Error in start_server:", e)


if __name__ == '__main__':
    # start server
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server())
