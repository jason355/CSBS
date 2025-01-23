# version 3.0.2

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, DateTime, update, SmallInteger, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func
import os


Base = declarative_base()
class tea_infor(Base):
    __tablename__ = "tea_infor"
    id = Column(Integer, primary_key=True)
    lineID = Column(String(45))
    name = Column(String(20))
    office = Column(String(20))
    isAdmin = Column(Boolean, default=False)
    verifyStat = Column(SmallInteger, default=0)

class Data(Base):
    __tablename__ = "data"
    id = Column(Integer, primary_key=True)
    name = Column(String(40))
    lineID = Column(String(45))
    hash = Column(String(40))
    content = Column(Text)
    is_new = Column(Integer, default=1)
    office = Column(String(5))
    time = Column(DateTime, default=func.now())
    finish_date = Column(String(10))
    des_grade = Column(String(3))
    des_class = Column(String(1))
    sound = Column(Integer)

class class_list(Base):
    __tablename__ = "class_list"
    id = Column(Integer, primary_key=True)
    classCode = Column(String(3))
    className = Column(String(10))





class mydatabase:
    def __init__(self):
        try:
            # 取得資料庫密碼
            self.database_pass = os.getenv(key="dbv1p")
            engine = create_engine(
                f"mysql+mysqlconnector://root:{self.database_pass}@localhost/dbv1", pool_size=50)
            Base.metadata.create_all(engine)
            self.Session = sessionmaker(bind=engine)

            

        except SQLAlchemyError as e:
            raise RuntimeError(f"Error 1020: From __init__() {e}")

    # 取得班級代碼列表
    def getClassCodeList(self, startid = 1):
        try:
            with self.Session() as session:
                get = session.query(class_list).filter(class_list.id >= startid).all()
                return [ row.classCode for row in get]
        except Exception as e:
            raise RuntimeError(f"Error 1019: From getClassCodeList() {e}")
        
    # 取得班級名稱列表
    def getClassNameList(self, startid = 1):
        try:
            with self.Session() as session:
                get = session.query(class_list).filter(class_list.id >= startid).all()
                return [ row.className for row in get]
        except Exception as e:
            raise RuntimeError(f"Error 1018: From getClassNameList() {e}")
        
        
    def getClassDic(self, startid = 1):
        try:
            data = {}
            with self.Session() as session:
                get = session.query(class_list).filter(class_list.id >= startid).all()
                for row in get:
                    data[row.classCode] = row.className
                return data
        except Exception as e:
            raise RuntimeError(f"Error 1017: From getClassDic() {e}")
        



    # 取得教師資訊
    def getTeacher(self, lineId, columns=[]):
        try:
            with self.Session() as session:
                teacher = session.query(tea_infor).filter(tea_infor.lineID == lineId).one_or_none()
                
                if teacher:
                    if columns == []:
                        return teacher
                    else:
                        data = []
                        for column in columns:
                            data.append(getattr(teacher, column))
                        return data
                return False
        except Exception as e:
            raise RuntimeError(f"Error 1016: From getTeacher() {e}")

    def findTeacher(self, lineId):
        try:
            with self.Session() as session:
                find_teacher = session.query(tea_infor).filter(
                    tea_infor.lineID == lineId).one_or_none()
                if find_teacher:
                    return True
                else:
                    return False
        except Exception as e:
            raise RuntimeError(f"Error 1015: From findTeacher() {e}")

    # 使用教師名稱取得教師資訊
    def getID(self, name):
        try: 
            with self.Session() as session:
                findID = session.query(tea_infor).filter(
                    tea_infor.name == name).one_or_none()
                if findID:
                    return findID
                else:
                    return False
        except Exception as e:   
            raise RuntimeError(f"Error 1014: From getID() {e}")
        



    # 插入教師資訊
    def insertTeaInfor(self, lineId, map = {}):
        try:
            with self.Session() as session:
                if not self.findTeacher(lineId):
                    session = self.Session()
                    new_data = tea_infor(
                        lineID=lineId, name=map['name'], office=map['office'], verifyStat=map['verifyStat'])
                    session.add(new_data)
                    session.commit()
                    return True
                else:
                    session = self.Session()
                    new_data = update(tea_infor).where(tea_infor.lineID == lineId).values(
                        name=map['name'], office=map['office'], verifyStat=map['verifyStat'])
                    session.execute(new_data)
                    session.commit()
                    
                    return True

        except Exception as e:
            raise RuntimeError(f"Error 1013: From insertTeaInfor() {e}")



    # 插入首位管理員
    def insertAdmin(self, lineId, map={}):
        try:
            with self.Session() as session:
                if not self.findTeacher(lineId):
                    new_data = tea_infor(
                        lineID=lineId, name=map['name'], office=map['office'], verifyStat=map['verifyStat'], isAdmin=map['isAdmin'])
                    session.add(new_data)
                    session.commit()
                    return True
                else:
                    new = update(tea_infor).where(
                                tea_infor.lineID == lineId).values(isAdmin=1)
                    session.execute(new)
                    session.commit()
                    return True
        except Exception as e:
            raise RuntimeError(f"Error 1012: From insertAdmin() {e}")

    # 插入廣播訊息
    def insertData(self, map):
        try:
            with self.Session() as session:
                if map is None:
                    return False

                new_data = Data(name=map['name'], lineID=map['lineID'], hash=map['hash'],content=map['content'], office=map['office'], time=map['time'],
                                des_grade=map['des_grade'], des_class= map['des_class'], finish_date = map['finish_date'], sound=map['sound'])
                session.add(new_data)
                session.commit()
                return True
        except Exception as e:
            raise RuntimeError(f"Error 1011: From insertData() {e}")
            

    def getHistoryData(self, lineId):
        try:
            with self.Session() as session:
                data = session.query(Data).filter(Data.lineID == lineId).all()
                result = []
                for item in data:
                    result.append(item)
                return result
        except Exception as e:
            raise RuntimeError(f"Error 1010: From getHistoryData() {e}")

    # 尋找管理員
    def findAdmin(self):
        try:
            with self.Session() as session:
                find_Admin = session.query(tea_infor).filter(
                    tea_infor.isAdmin == 1).all()
                data = []
                for Admin in find_Admin:
                    data.append(Admin.lineID)
                if data != []:
                    return data
                else:
                    return False
        except Exception as e:
            raise RuntimeError(f"Error 1009: From findAdmin() {e}")


    # 判斷是否為管理員
    def isAdmin(self, lineId):
        try:
            with self.Session() as session:
                admin = session.query(tea_infor).filter(tea_infor.lineID == lineId).one_or_none()
                if admin == None:
                    return None
                else:
                    return admin.isAdmin
        except Exception as e:
            raise RuntimeError(f"Error 1008: From isAdmin() {e}")
        

    # 確認使用者使否認證
    def verified(self, lineId):
        try:
            with self.Session() as session:
                check_teacher = session.query(tea_infor.verifyStat).filter(
                    tea_infor.lineID == lineId).one_or_none()
                if check_teacher:
                    return True
                else:
                    return False
        except Exception as e:
            raise RuntimeError(f"Error 1007: From verified() {e}")


    # 修改使用者認證設定
    def modifyVerifyStat(self, lineId):
        try:
            with self.Session() as session:
                user = session.query(tea_infor).filter(tea_infor.lineID == lineId).one_or_none()
                if user:
                    if not user.verifyStat:
                        new = update(tea_infor).where(
                            tea_infor.lineID == lineId).values(verifyStat=1)
                        session.execute(new)
                        session.commit()
                        return True
                    else:
                        return "Uped"
                else:
                    return False
        except Exception as e:
            raise RuntimeError(f"Error 1006: From modifyVerifyStat() {e}")


    # 取得所有未驗證帳號
    def findUnVerify(self):
        try:
            with self.Session() as session:
                getList = session.query(tea_infor).filter(tea_infor.verifyStat == 0).all()
                if len(getList) != 0:
                    return getList
                else:
                    return False
        except Exception as e:
            raise RuntimeError(f"Error 1005: From findUnVerify() {e}")

    # 取得所有教室lineId
    def GetAllTeacherID(self):
        try:
            with self.Session() as session:
                teachers = [name for (name,) in session.query(tea_infor.lineID).filter(tea_infor.verifyStat == 1).all()]
                if len(teachers) != 0:
                    return teachers
                else:
                    return False
        except Exception as e:
            raise RuntimeError(f"Error 1004: From GetALLTeacherID() {e}")


    # 刪除教師資訊
    def DelTeacherData(self, lineId):
        try:
            with self.Session() as session:
                user_t_del = session.query(tea_infor).filter(tea_infor.lineID == lineId).one_or_none()
                if user_t_del:
                    session.delete(user_t_del)
                    session.commit()
                    return True
                else:
                    return False
        except Exception as e:
            raise RuntimeError(f"Error 1003: From DelTeacherData() {e}")


    # 刪除整個Data資料庫中資料
    def DelDataAll(self):
        try:
            with self.Session() as session:
                rows = session.query(Data).delete()
                session.commit()
                return rows
        except Exception as e:
            raise RuntimeError(f"Error 1002: From DelDataAll() {e}")

    # 插入所有班級
    def insertClass(self, Class):
        try:
            with self.Session() as session:
                for i in range (33):
                    new_data = class_list(classCode = Class[i], className = Class[i] + "班")
                    session.add(new_data)
                session.commit()
                
        except Exception as e:
            raise RuntimeError(f"Error 1001: From insertClass() {e}")


    # 教師取得廣播即時資訊
    def get_sended_data(self, lineId):
        try:
            with self.Session() as session:
                data1 = session.query(Data).filter(Data.lineID == lineId, Data.is_new==1).order_by(desc(Data.time)).limit(400)
                data0 = session.query(Data).filter(Data.lineID == lineId, Data.is_new==0).order_by(desc(Data.time)).limit(100)
                data = data1.union(data0)
            return data
                
        except Exception as e:
            raise RuntimeError(f"Error 1000: From get_sended_data() {e}")
        
