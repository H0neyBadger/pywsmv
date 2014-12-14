
from pywsmv import wsmv

host = "192.168.0.22"
url = "/wsman"
port="5985"
username = "honeybadger"
password = "H0neyBadger"

winrm = wsmv (username,password,host,port,url)
cmd_id, shell_id = winrm.run_cmd("cmd")
stdout, stderr, return_code, command_done = winrm.read_response()
print ("stdout %s, stderr %s, return_code %s, command_done %s"%(stdout, stderr, return_code, command_done))

cmd_id, shell_id = winrm.send_cmd("set test='ok'\r\n")
stdout, stderr, return_code, command_done = winrm.read_response()
print ("stdout %s, stderr %s, return_code %s, command_done %s"%(stdout, stderr, return_code, command_done))

cmd_id, shell_id = winrm.send_cmd("echo %test%\r\n")
stdout, stderr, return_code, command_done = winrm.read_response()
print ("stdout %s, stderr %s, return_code %s, command_done %s"%(stdout, stderr, return_code, command_done))

winrm.close_shell()
