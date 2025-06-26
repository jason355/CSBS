import asyncio
import websockets
import subprocess
import json
import datetime
import os
import signal
import time
import schedule

# 檢查 WebSocket 伺服器狀態的異步函數
async def check_server(uri):
    ping_message = "hello server"  # 定義 ping 訊息
    try:
        async with websockets.connect(uri) as websocket:
            ping = {
                "header": "M1",
                "ping": ping_message
            }
            ping = json.dumps(ping, ensure_ascii=False)  # 將訊息轉為 JSON 格式
            
            try:
                # 傳送 ping 訊息至伺服器
                await websocket.send(ping)
            except Exception as send_error:
                print(f"Error sending ping: {send_error}")
                return False

            try:
                # 接收伺服器回應並解析
                response = await websocket.recv()
                response = json.loads(response)
                if response.get("ping") == ping_message:
                    return True  # 伺服器回應正常
            except Exception as recv_error:
                print(f"Error receiving response: {recv_error}")
                return False
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        return False

# 清理舊的 Python 進程
def cleanup_old_process():
    try:
        print("Cleaning up old processes...")
        process_name = r"H:\My Drive\SWBS_Mother\upload\Server\websocket_v2.6.py"
        
        # 使用 wmic 來檢查執行中的 Python 進程
        tasklist_output = subprocess.check_output(
            'wmic process where "CommandLine like \'%python%\' and CommandLine like \'%%{}%%\'" get ProcessId,CommandLine'.format(process_name),
            shell=True
        ).decode()

        print("Tasklist output:", tasklist_output)  # 輸出檢查結果

        # 提取進程 ID 並終止對應的進程
        pids = [int(pid) for pid in tasklist_output.split() if pid.isdigit()]

        if pids:
            for pid in pids:
                print(f"Found running process with PID: {pid}, attempting to terminate...")
                subprocess.call(["taskkill", "/F", "/PID", str(pid)])  # 終止進程
            print("Process terminated successfully.")
        else:
            print(f"No running process found for: {process_name}.")
    except Exception as e:
        print(f"Failed to clean up old processes: {e}")

# 重新啟動伺服器的功能
def restart_server(command):
    try:
        print("Restarting server...")
        # 執行重啟伺服器的命令
        subprocess.Popen(f'start cmd /c {command}', shell=True)
        print("Server restart command issued successfully\n", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        time.sleep(5)  # 等待 5 秒
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart server: {e}")

# 持續監控伺服器狀態
async def monitor_server(uri, check_interval, restart_command):
    retry_count = 0
    max_retry_interval = 300  # 最大重試時間間隔
    max_retry_reached_count = 0
    
    while True:
        server_running = await check_server(uri)

        if not server_running:
            restart_server(restart_command)
            retry_count += 1
            retry_interval = min(check_interval * (2 ** retry_count), max_retry_interval)  # 使用指數回退機制增加間隔
            
            if retry_interval == max_retry_interval:
                max_retry_reached_count += 1
                if max_retry_reached_count >= 2:
                    print("Warning: Server has reached max retry interval twice.")  # 發出警告
            
            print(f"Server restart attempt {retry_count}, next attempt in {retry_interval} seconds.")
        else:
            retry_count = 0  # 如果伺服器正常，重置重試計數
            retry_interval = check_interval
            max_retry_reached_count = 0

        try:
            await asyncio.sleep(retry_interval)
        except asyncio.CancelledError:
            print("Monitoring task cancelled.")  # 當監控任務被取消時退出
            break

# 運行排程
async def run_schedule():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

# 排定伺服器重啟時間
def schedule_restart(restart_command):
    schedule.every().day.at("18:59").do(cleanup_old_process)  # 每日 18:59 執行清理操作

if __name__ == "__main__":
    websocket_uri = "ws://192.168.88.1:80"
    check_interval = 1  # 設定檢查伺服器狀態的時間間隔
    restart_command = r'python "H:\My Drive\SWBS_Mother\upload\Server\websocket_v2.6.py"'

    schedule_restart(restart_command)

    # 使用 asyncio 來並行運行伺服器監控與排程
    loop = asyncio.get_event_loop()
    tasks = [
        monitor_server(websocket_uri, check_interval, restart_command),
        run_schedule()
    ]
    loop.run_until_complete(asyncio.gather(*tasks))