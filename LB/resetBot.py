# version 3.0.3
import subprocess
import time
import os
from pathlib import Path
import json

child_process = None  # 初始化全局變數


relative_path = ".\\appV3.0.3.py"
script_dir = os.path.dirname(os.path.abspath(__file__))
absolute_path = os.path.join(script_dir, relative_path)
absolute_path = str(Path(absolute_path))


with open(".\\config.json","r", encoding="utf-8") as f:
    config = json.load(f)


with open(".\\config.json","w", encoding="utf-8") as f:
    config["Dynamic"]["initial_start"] = True
    f.write(json.dumps(config, indent = 4))

def start():
    global child_process
    child_process = subprocess.Popen(['python', absolute_path])
    child_process.wait()



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