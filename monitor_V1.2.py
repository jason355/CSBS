import asyncio
import websockets
import subprocess
import json
import datetime
import os
import signal
import time
import schedule

async def check_server(uri):
    ping_message = "hello server"
    try:
        async with websockets.connect(uri) as websocket:
            ping = {
                "header": "M1",
                "ping": ping_message
            }
            ping = json.dumps(ping, ensure_ascii=False)
            
            try:
                await websocket.send(ping)
            except Exception as send_error:
                print(f"Error sending ping: {send_error}")
                return False

            try:
                response = await websocket.recv()
                response = json.loads(response)
                if response.get("ping") == ping_message:
                    return True
            except Exception as recv_error:
                print(f"Error receiving response: {recv_error}")
                return False
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        return False

def cleanup_old_process():
    try:
        print("Cleaning up old processes...")
        process_name = r"C:\\Users\\yuxia\\SWBS\\server\\py-server demo\\V2.5\\Websocket_V2.5.py"
        
        # 使用 wmic 檢查正在執行的 Python 進程，並將路徑進行適當轉義
        tasklist_output = subprocess.check_output(
            'wmic process where "CommandLine like \'%python%\' and CommandLine like \'%%{}%%\'" get ProcessId,CommandLine'.format(process_name),
            shell=True
        ).decode()

        # 輸出檢查結果
        print("Tasklist output:", tasklist_output)

        # 提取進程 ID，並檢查是否有對應的進程
        pids = [int(pid) for pid in tasklist_output.split() if pid.isdigit()]

        if pids:
            for pid in pids:
                print(f"Found running process with PID: {pid}, attempting to terminate...")
                subprocess.call(["taskkill", "/F", "/PID", str(pid)])
            print("Process terminated successfully.")
        else:
            print(f"No running process found for: {process_name}.")
    except Exception as e:
        print(f"Failed to clean up old processes: {e}")


def restart_server(command):
    try:
        print("Restarting server...")
        subprocess.Popen(f'start cmd /c {command}', shell=True)
        print("Server restart command issued successfully\n", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(5)
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart server: {e}")

async def monitor_server(uri, check_interval, restart_command):
    retry_count = 0
    max_retry_interval = 300
    max_retry_reached_count = 0
    
    while True:
        server_running = await check_server(uri)

        if not server_running:
            restart_server(restart_command)
            retry_count += 1
            retry_interval = min(check_interval * (2 ** retry_count), max_retry_interval)
            
            if retry_interval == max_retry_interval:
                max_retry_reached_count += 1
                if max_retry_reached_count >= 2:
                    print("Warning: Server has reached max retry interval twice.")
            
            print(f"Server restart attempt {retry_count}, next attempt in {retry_interval} seconds.")
        else:
            retry_count = 0
            retry_interval = check_interval
            max_retry_reached_count = 0

        try:
            await asyncio.sleep(retry_interval)
        except asyncio.CancelledError:
            print("Monitoring task cancelled.")
            break

async def run_schedule():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

def schedule_restart(restart_command):
    schedule.every().day.at("18:59").do(cleanup_old_process)

if __name__ == "__main__":
    websocket_uri = "ws://192.168.56.1:8000"
    check_interval = 1
    restart_command = r'python "C:\Users\yuxia\SWBS\server\py-server demo\V2.5\Websocket_V2.5.py"'

    schedule_restart(restart_command)

    loop = asyncio.get_event_loop()
    tasks = [
        monitor_server(websocket_uri, check_interval, restart_command),
        run_schedule()
    ]
    loop.run_until_complete(asyncio.gather(*tasks))
