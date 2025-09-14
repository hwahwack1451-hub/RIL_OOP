import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import json
import os
import psutil
import win32api
import time
from datetime import datetime
from pywinauto.application import Application
from pywinauto import timings

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

class DeviceController:
    def __init__(self):
        self.retry_count = 2

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
                    if proc_name:
                        for proc in psutil.process_iter():
                            if proc.name() == proc_name:
                                proc.kill()
                                self.log(device_name, f"Killed process {proc_name}")
                    if exe_path:
                        win32api.ShellExecute(0, 'open', exe_path, '', '', 1)
                        self.log(device_name, f"Started {exe_path}")
                        time.sleep(1)
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

class ServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("원격 장치 서버")
        self.running = False
        self.server_thread = None
        self.controller = DeviceController()
        self.create_ui()

    def create_ui(self):
        self.start_btn = tk.Button(self.root, text="서버 시작", command=self.start_server)
        self.start_btn.pack(padx=10, pady=5)

        self.stop_btn = tk.Button(self.root, text="서버 종료", command=self.stop_server, state="disabled")
        self.stop_btn.pack(padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.log_area.pack(padx=10, pady=5)
        self.log_area.config(state="disabled")

    def log(self, msg):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")

    def start_server(self):
        if self.running:
            return
        self.running = True
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.server_thread.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.log("서버 시작")

    def stop_server(self):
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.log("서버 종료 신호 전송")

    def run_server(self):
        HOST = '0.0.0.0'
        PORT = 5000
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            s.settimeout(1)  # accept 타임아웃
            while self.running:
                try:
                    conn, addr = s.accept()
                    threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    continue

    def handle_client(self, conn, addr):
        self.log(f"{addr} 연결됨")
        try:
            data = conn.recv(4096).decode()
            req = json.loads(data)
            action = req.get("action")
            device_info = req.get("device")
            if action == "restart_login":
                result = self.controller.restart_and_login(device_info)
                conn.send(json.dumps({"status": "ok", "result": result}).encode())
            else:
                conn.send(json.dumps({"status": "unknown_action"}).encode())
        except Exception as e:
            conn.send(json.dumps({"status": "error", "msg": str(e)}).encode())
        finally:
            conn.close()
            self.log(f"{addr} 연결 종료")

if __name__ == "__main__":
    root = tk.Tk()
    gui = ServerGUI(root)
    root.mainloop()
