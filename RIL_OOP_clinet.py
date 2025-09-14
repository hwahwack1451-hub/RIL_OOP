import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import socket, json, os

DEVICE_FILE = "devices.json"

class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("원격 장치 관리")
        self.devices = []
        self.load_devices()
        self.create_ui()

    def load_devices(self):
        if os.path.exists(DEVICE_FILE):
            with open(DEVICE_FILE, "r", encoding="utf-8") as f:
                self.devices = json.load(f)
        else:
            self.devices = []

    def save_devices(self):
        with open(DEVICE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.devices, f, indent=2)

    def create_ui(self):
        frame = ttk.Frame(self.root)
        frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(frame, columns=("IP", "Interfaces"), show="headings")
        self.tree.heading("IP", text="IP")
        self.tree.heading("Interfaces", text="Interfaces (Titles)")
        self.tree.pack(fill="both", expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="추가", command=self.add_device).pack(side="left")
        ttk.Button(btn_frame, text="삭제", command=self.delete_device).pack(side="left")
        ttk.Button(btn_frame, text="재시작/로그인", command=self.restart_login).pack(side="right")

        self.refresh_tree()

    def refresh_tree(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for d in self.devices:
            titles = ", ".join([i["title"] for i in d.get("interfaces", [])])
            self.tree.insert("", "end", values=(d["ip"], titles))

    def add_device(self):
        name = simpledialog.askstring("장치명", "장치명을 입력하세요")
        ip = simpledialog.askstring("IP", "IP를 입력하세요")
        interface_count = simpledialog.askinteger("인터페이스 수", "등록할 인터페이스 갯수", minvalue=1)
        interfaces = []
        for i in range(interface_count):
            title = simpledialog.askstring(f"인터페이스 {i+1} 타이틀", "인터페이스 창 제목 입력")
            exe_path = simpledialog.askstring(f"인터페이스 {i+1} 경로", "실행 파일 경로 입력")
            proc_name = simpledialog.askstring(f"인터페이스 {i+1} 프로세스명", "프로세스 이름 입력")
            interfaces.append({"title": title, "exe_path": exe_path, "proc_name": proc_name})
        if name and ip and interfaces:
            self.devices.append({"name": name, "ip": ip, "interfaces": interfaces})
            self.save_devices()
            self.refresh_tree()

    def delete_device(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = self.tree.index(selected[0])
        del self.devices[idx]
        self.save_devices()
        self.refresh_tree()

    def restart_login(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "장치를 선택하세요")
            return
        idx = self.tree.index(selected[0])
        device = self.devices[idx]
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((device["ip"], 5000))
                msg = json.dumps({"action":"restart_login", "device":device})
                s.send(msg.encode())
                resp = json.loads(s.recv(4096).decode())
                results = resp.get("result", {})
                msg_text = "\n".join([f"{k}: {v}" for k, v in results.items()])
                messagebox.showinfo("결과", f"{device['name']}:\n{msg_text}")
        except Exception as e:
            messagebox.showerror("오류", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()
