import mynetlib
import IAL
import sys, os
import ctypes, time
from PIL import Image
import pystray, psutil
from pystray import MenuItem as item
import multiprocessing
from multiprocessing import Queue, freeze_support
import socket
from pywinauto.application import Application
from pywinauto import timings

mp = multiprocessing.Process

PI = "PIAgent.exe"

def ErrorLog(error: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("RIL_server_Log_" + str(time.strftime("%y.%m.%d")) + ".txt", "a", encoding='utf-8') as f:
        f.write(f"[{current_time}] - {error}\n")

def TaskKill(prg):
    PROCNAME = prg
    for proc in psutil.process_iter():
        if proc.name() == PROCNAME:
            proc.kill()

def restartscript():
    time.sleep(5)
    ErrorLog('restartprg')
    os.execl(sys.executable, sys.executable, *sys.argv)    

def make_trayicon():
    def empty_menu():
        pass
    def quit_ial():
        icon.stop()
    image = Image.open("chunsik1.ico")        
    menu = (item('<인터페이스 원격로그인 프로그램 서버(인터페이스 PC에 설치)>', empty_menu),
            item('프로그램 종료', quit_ial))
    icon = pystray.Icon("인터페이스 원격로그인 프로그램 서버", image, "인터페이스 PC에 설치", menu)
    icon.run()
    
def wakeup():
    while True:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)  # set back to normal
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # prevent
        time.sleep(1500)

def do_work_server(client, addr):
    print('client :', addr)
    #print(addr[0])
    serverip = socket.gethostbyname(socket.gethostname())
    print(serverip)
    cmd_r = mynetlib.my_recv(1024, client)
    # cmd_rr = cmd_r.decode('utf-8')
    print(cmd_r)
    #print(cmd_r[0], cmd_r[1],cmd_r[2])
    a = cmd_r[0]
    b = cmd_r[1]
    c = cmd_r[2]
    #cmd_s = [a,b]
    #mynetlib.my_send(cmd_s,client)
    if c == 'INT':
        IAL.StartTask(a,b)
    if c == 'OC':
        IAL.StartTaskOS(a,b)        
    if c == 'AU':
        IAL.StartTaskAU(a,b)    
    if c == 'Nova':
        IAL.StartTaskNovaPrime(a,b)     
    if c == 'ST2':
        IAL.StartTaskST2(a,b)                   
    if c == 'R':
        if IAL.int_result == "int_success":
            INTSUCCESS = (serverip, "int_success")           
            print(INTSUCCESS)
            ErrorLog(INTSUCCESS)
            ErrorLog(a +'/'+ b)
            mynetlib.my_send(INTSUCCESS,client)
            print('sent')
            #time.sleep(3)
            mynetlib.my_send("",client)     
            IAL.int_result = ""            
        if IAL.int_result == "int_failed":
            INTFAILED2 = (serverip, "int_failed") 
            print(INTFAILED2)
            ErrorLog(INTFAILED2)
            mynetlib.my_send(INTFAILED2,client)
            #time.sleep(3)
            mynetlib.my_send("",client)  
            IAL.int_result = ""                        
            
def run_server2():
    TaskKill(PI)
    while True:    
        mynetlib.run_server(2023, do_work_server,1)
#run_server2()
if __name__ == "__main__":
    freeze_support() #windows에서 multiprocessing 사용할 때 반드시 필요!!!!!!!!!!!!!
    start_time = time.perf_counter()    
    qpesss = Queue()
    p0 = mp(target = make_trayicon)
    p1 = mp(target = run_server2)
    p2 = mp(target = wakeup)
    p0.start(),
    p1.start(),
    p2.start(),
    p0.join(),
    p1.terminate()
    p2.terminate()

    while True:
        if p0.is_alive() == False: #p0 종료시 나머지도 종료
            ErrorLog("tray종료 - 프로그램 종료")
            print("tray종료 - 프로그램 종료")
            p1.terminate(),p2.terminate()
            finish_time = time.perf_counter()
            ErrorLog(f"Program finished in {(finish_time - start_time):.3f} seconds")
            sys.exit()
        else:
            if p1.is_alive() == False: #p2 or p3 종료시
                ErrorLog("server종료 - 프로그램 재시작")
                print("server종료 - 프로그램 재시작")
                p0.terminate(), p2.terminate()
                restartscript()
            elif p2.is_alive() == False:
                ErrorLog("wakeup종료 - 프로그램 재시작")
                print("wakeup종료 - 프로그램 재시작")
                p0.terminate(), p1.terminate()
                restartscript()
        time.sleep(1)
#pyinstaller -w -F --uac-admin --icon=chunsik1.ico --exclude pandas, --exclude numpy, --exclude pillow RIL_server231116-2.py
# 
# RIL_server.py \\10.2.151.177\cobas앞 공유폴더\코드모음
#cd socker_server_include_UA_osmo_AU