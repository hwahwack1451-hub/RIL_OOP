import socket
import threading

HOST = '0.0.0.0'  # 모든 IP 허용
PORT = 5000

def handle_client(conn, addr):
    print(f"[연결됨] {addr}")
    try:
        data = conn.recv(1024).decode()
        print(f"[수신] {data}")
        conn.send(f"서버에서 수신: {data}".encode())
    except Exception as e:
        print(f"[오류] {e}")
    finally:
        conn.close()
        print(f"[연결 종료] {addr}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"[서버 시작] {HOST}:{PORT}에서 대기 중...")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
