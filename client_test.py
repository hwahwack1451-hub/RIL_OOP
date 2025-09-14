import socket

SERVER_IP = input("서버 IP 입력: ")  # 예: 192.168.0.10
PORT = 5000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        s.connect((SERVER_IP, PORT))
        print("[연결 성공]")
        msg = input("서버로 보낼 메시지 입력: ")
        s.send(msg.encode())
        data = s.recv(1024).decode()
        print(f"[서버 응답] {data}")
    except Exception as e:
        print(f"[오류] {e}")
