
# version 3.0.0
import subprocess
import time
import os
from pathlib import Path
child_process = None  # 初始化全局變數

relative_path = ".\\appV3.0.0.py"
script_dir = os.path.dirname(os.path.abspath(__file__))
absolute_path = os.path.join(script_dir, relative_path)
absolute_path = str(Path(absolute_path))



def start(absolute_path):
    global child_process
    child_process = subprocess.Popen(['python', absolute_path])
    child_process.wait()



if True:

    try:
        while True:
            start(absolute_path)
            time.sleep(1)
    except Exception as e:
        print(e)
    except KeyboardInterrupt:
        child_process.kill()
        exit()