from http import protocol
from soap import soap_wsmv

import logging
logger = logging.getLogger(__name__)

class wsmv :
    ShellId = None
    CommandId = None

    def __init__(self, username, password, host='127.0.0.1', port='5985', uri='/wsman', ShellId = None, CommandId = None):
        logger.debug('init http/https connection')
        self.connection = protocol(username, password, host, port, uri)
       
        self.ShellId = ShellId
        self.CommandId = CommandId
 
        logger.debug('load soap functions')
        self.soap = soap_wsmv()
        
        if not ShellId :
            logger.debug('init winrs shell')
            self.__initshell()

    def __initshell(self):
        soaprq = self.soap.Create()
        soapresp = self.connection.post(soaprq)
        self.ShellId = self.soap.CreateResponse(soapresp)
        logger.info("Shell opened : ShellId=%s "%self.ShellId)
        return self.ShellId

    def run_cmd(self, command, arguments=()):
        soaprq = self.soap.Command(self.ShellId, command, arguments)
        soapresp = self.connection.post(soaprq)
        self.CommandId = self.soap.CommandResponse(soapresp)
        logger.info("Command executed : CommandId=%s "%self.CommandId)
        return self.CommandId, self.ShellId

    def send_cmd(self, command):
        soaprq = self.soap.Send(self.ShellId, self.CommandId, command)
        soapresp = self.connection.post(soaprq)
        MessageID = self.soap.SendResponse(soapresp)
        logger.info("Session command sent : MessageID=%s : %s "%(MessageID,command))
        return self.CommandId, self.ShellId
  
    def read_response(self):
        soaprq = self.soap.Receive(self.ShellId, self.CommandId)
        soapresp = self.connection.post(soaprq)
        stdout, stderr, return_code, command_done = self.soap.ReceiveResponse(soapresp)
        if stdout and stdout is not "":
            logger.debug("Read Response stdout %s:"%repr(stdout))
        if stderr and stderr is not "":
            logger.error("Read Response [return %s] stderr %s:"%(return_code, repr(stderr)))
        logger.info("Read Response return_code %s, command_done %s"%(return_code, command_done))

        return stdout, stderr, return_code, command_done

    def close_shell(self):
        soaprq = self.soap.Delete(self.ShellId)
        soapresp = self.connection.post(soaprq)
        self.MessageID = self.soap.DeleteResponse(soapresp)
        logger.info("Session Shell closed : ShellId=%s "%self.ShellId)
        return 0

 
