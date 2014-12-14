
from httplib import HTTPConnection
from base64 import b64decode, b64encode

import logging
logging.getLogger(__name__)

class protocol:
    connection = None
    auth = None

    def __init__(self, username, password, host="127.0.0.1", port="5985", url="/wsman"):
        self.url = url
        self.headers= auth(username,password).get_headers()
        self.connection = HTTPConnection(host,port)

    def post(self,body):
        self.connection.request("POST", self.url, body=body, headers=self.headers)
        response = self.connection.getresponse()
        return response.read()

class auth:

    def __init__(self, username, password, methode="Basic"):
        if not username or not password :
            logger.error("empty username or password")
            exit(1)
        userAndPass = b64encode("%s:%s"%(username,password))
        self.headers = {
                    'Connection': 'Keep-Alive',
                    'Content-Type': 'application/soap+xml;charset=UTF-8',
                    'Authorization' : 'Basic %s' %  userAndPass,
                    'User-Agent': 'Python WinRM Client'
                    }

    def get_headers(self):
        return self.headers

