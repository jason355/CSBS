
# version 2.9.9
import subprocess
import time

child_process = None  # 初始化全局變數


def start():
    global child_process
    child_process = subprocess.Popen(['python', file_name])
    child_process.wait()


file_name = "./LB3/appV2.9.9.py"   # input("輸入啟動檔案名稱> ")

if True:

    try:
        while True:
            start()
            time.sleep(1)
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        child_process.kill()
        exit()