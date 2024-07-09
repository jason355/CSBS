import subprocess
import time





child_process = None  # 初始化全局變數


def start():
    global child_process
    child_process = subprocess.Popen(['python', file_name])
    child_process.wait()

should_start_process = input("start?(y/n): ").lower() == 'y'

file_name = "appV2.9.4.py"   # input("輸入啟動檔案名稱> ")

if should_start_process:

    try:
        while True:
            start()
            time.sleep(1)
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        child_process.kill()
        exit()