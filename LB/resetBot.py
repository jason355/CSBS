# version 3.0.5
import subprocess
import time
import os
from pathlib import Path
import json
import logging
import threading

child_process = None  # 初始化全局變數

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("linebot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("--- RESETBOT START ---")

relative_path = ".\\appV3.0.5.py"
script_dir = os.path.dirname(os.path.abspath(__file__))
absolute_path = os.path.join(script_dir, relative_path)
absolute_path = str(Path(absolute_path))


with open(".\\config.json","r", encoding="utf-8") as f:
    config = json.load(f)


with open(".\\config.json","w", encoding="utf-8") as f:
    config["Dynamic"]["initial_start"] = True
    f.write(json.dumps(config, indent = 4))


def read_stdout(pipe):
    for line in pipe:
        if "Traceback" in line or "Error" in line or "Exception" in line:
            logging.error("[CHILD STDERR] %s", line.strip())
        else:
            logging.info("[CHILD STDOUT] %s", line.strip())

def read_stderr(pipe):
    for line in pipe:
        if "Traceback" in line or "Error" in line or "Exception" in line:
            logging.error("[CHILD STDERR] %s", line.strip())
        else:
            logging.info("[CHILD STDOUT] %s", line.strip())

def start():
    global child_process
    child_process = subprocess.Popen(
        ['python', absolute_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    logging.info("--- CHILD START ---")
    # Start reading stdout and stderr concurrently
    t1 = threading.Thread(target=read_stdout, args=(child_process.stdout,))
    t2 = threading.Thread(target=read_stderr, args=(child_process.stderr,))
    t1.start()
    t2.start()

    child_process.wait()
    t1.join()
    t2.join()
    logging.info("Child process finished.")


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