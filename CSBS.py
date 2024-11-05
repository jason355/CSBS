import subprocess
import time


ngrok_command = "ngrok http 5000"
script1 = "./LB/resetBot.py"
script2 = "./server/monitor.py"
process = subprocess.Popen(ngrok_command, creationflags=subprocess.CREATE_NEW_CONSOLE)

time.sleep(2)

command1 = f"python {script1}"
process1 = subprocess.Popen(command1, creationflags=subprocess.CREATE_NEW_CONSOLE)

command2 = f"python {script2}"
process2 = subprocess.Popen(command2, creationflags=subprocess.CREATE_NEW_CONSOLE)