pywsmv
======

Python Winrm / PSSession PoC

This project is a PoC, I would like to recreate Enter-PSSession in python.
Some part of these scripts comes directly from the project 
https://github.com/diyan/pywinrm

Current features:
* Run windows cmd in interactive sessions (http://msdn.microsoft.com/en-us/library/cc251732.aspx)
* Basic auth
* http 

On server enable settigns:
```
winrm set winrm/config/service/auth @{Basic="true"}
winrm set winrm/config/service @{AllowUnencrypted="true"}
```

Then edit test.py or cmd.py and add your credentials 
* cmd.py run interactive command (python threads enable)
* test.py simple winrm sessions 


Powershell session isn’t available yet.  It depend if I’m able to finish my PoC.
(http://msdn.microsoft.com/en-us/library/dd357801.aspx)


