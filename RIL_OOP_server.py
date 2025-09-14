import socket, threading, json, os, psutil, win32api, time
from datetime import datetime
from pywinauto.application import Application
from pywinauto import timings

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

class DeviceController:
    def __init__(self):
        self.retry_count = 2  # 실패 시 재시도

    def log(self, device_name, msg):
        log_file = os.path.join(LOG_DIR, f"{device_name}_{datetime.now().strftime('%Y%m%d')}.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        print(msg)

    def restart_and_login(self, device_info, user_id="test_id", user_pw="test_pw"):
        device_name = device_info.get("name", "UnknownDevice")
        interfaces = device_info.get("interfaces", [])
        results = {}
        for iface in interfaces:
            title = iface.get("title")
            exe_path = iface.get("exe_path")
            proc_name = iface.get("proc_name")
            attempt = 0
            result = "int_failed"
            while attempt <= self.retry_count:
                try:
                    # 프로세스 종료
                    if proc_name:
                        for proc in psutil.process_iter():
                            if proc.name() == proc_name:
                                proc.kill()
                                self.log(device_name, f"Killed process {proc_name}")

                    # 프로그램 실행
                    if exe_path:
                        win32api.ShellExecute(0, 'open', exe_path, '', '', 1)
                        self.log(device_name, f"Started {exe_path}")
                        time.sleep(1)

                    # pywinauto 연결
                    app = Application(backend="uia")
                    timings.wait_until_passes(10, 0.5, lambda: app.connect(title_re=f".*{title}.*"))
                    dlg = app.window()
                    dlg.set_focus()
                    if '사용자 변경' in dlg.window_text():
                        dlg['사용자 변경'].select()
                    dlg.Edit2.set_focus()
                    dlg.Edit2.type_keys(user_id, set_foreground=False)
                    dlg.Edit2.type_keys("{ENTER}", set_foreground=False)
                    dlg.Edit0.set_focus()
                    dlg.Edit0.type_keys(user_pw, set_foreground=False)
                    dlg.Edit0.type_keys("{ENTER}", set_foreground=False)
                    if '초기화' in dlg.window_text():
                        dlg['초기화'].click()
                    result = "int_success"
                    self.log(device_name, f"{title} login success")
                    break
                except Exception as e:
                    attempt += 1
                    self.log(device_name, f"{title} attempt {attempt} failed: {e}")
                    time.sleep(1)
            results[title] = result
        return results

HOST = '0.0.0.0'
PORT = 5000
controller = DeviceController()

def handle_client(conn, addr):
    try:
        data = conn.recv(4096).decode()
        req = json.loads(data)
        action = req.get("action")
        device_info = req.get("device")
        if action == "restart_login":
            result = controller.restart_and_login(device_info)
            conn.send(json.dumps({"status": "ok", "result": result}).encode())
        else:
            conn.send(json.dumps({"status": "unknown_action"}).encode())
    except Exception as e:
        conn.send(json.dumps({"status": "error", "msg": str(e)}).encode())
    finally:
        conn.close()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
