import subprocess
import time
import os

# 取得目前腳本所在資料夾
base_dir = os.path.dirname(os.path.abspath(__file__))
print(base_dir)

ngrok_command = "ngrok http 5000"
ngrok_process = subprocess.Popen(ngrok_command, creationflags=subprocess.CREATE_NEW_CONSOLE)

time.sleep(2)

linebot = os.path.join(base_dir, "LB", "resetBot.py")
linebot = "resetBot.py"
linebot_cwd = os.path.join(base_dir, "LB")
linebot_cmd = f"python {linebot}"
linebot_process = subprocess.Popen(args=linebot_cmd, cwd=linebot_cwd, creationflags=subprocess.CREATE_NEW_CONSOLE)


# 取得在Server 資料夾中的 monitor_Vxx.py
server_cwd = os.path.join(base_dir, "server")
prefix = "monitor_V" # 設定前綴
file = [f for f in os.listdir(server_cwd) if f.startswith(prefix)]
if len(file) != 1:
    raise ValueError(f"found more than one file start with '{prefix}'")
else:
    server = file[0]

server_cmd = f"python {server}"
server_process = subprocess.Popen(server_cmd, cwd=server_cwd, creationflags=subprocess.CREATE_NEW_CONSOLE)