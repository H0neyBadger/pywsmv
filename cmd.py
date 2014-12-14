import threading
from pywsmv import wsmv
import sys

host = "192.168.0.22"
url = "/wsman"
port="5985"
username = "honeybadger"
password = "H0neyBadger"

listener = wsmv (username,password,host,port,url)
cmd_id, shell_id = listener.run_cmd("cmd")
stdout, stderr, return_code, command_done = listener.read_response()
#print ("%s%s"%(stderr, stdout)),
#print ("stdout %s, stderr %s, return_code %s, command_done %s"%(stdout, stderr, return_code, command_done))

class send_cmd_thread(threading.Thread): 
    def __init__(self,username,password,host,port,url,shell_id,cmd_id):
        threading.Thread.__init__(self)
        self.controler = wsmv (username,password,host,port,url,shell_id,cmd_id)

    def run(self):
        while True :
            cmd = sys.stdin.readline()
            cmd_id, shell_id = self.controler.send_cmd("%s\r\n"%cmd.replace('\n',''))

cmd_thread = send_cmd_thread(username,password,host,port,url,shell_id,cmd_id)
cmd_thread.start()

while True :
    print("%s%s"%(stderr, stdout))
    stdout, stderr, return_code, command_done = listener.read_response()
    #print ("%s%s"%(stderr, stdout)),

winrm.close_shell()


