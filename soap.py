import xmltodict
from uuid import uuid4
from base64 import b64decode, b64encode

import xml.etree.ElementTree as ET

import logging
logger = logging.getLogger(__name__)

class soap_wsmv:

    def __init__(self):
        logger.debug("init soap fuctions")

    def Create(self, i_stream='stdin', o_stream='stdout stderr',
                   working_directory=None, env_vars=None, noprofile=False,
                   codepage=437, lifetime=None, idle_timeout=None):
        
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',  # NOQA
            action='http://schemas.xmlsoap.org/ws/2004/09/transfer/Create')}
        
        header = rq['env:Envelope']['env:Header']
        header['w:OptionSet'] = {
            'w:Option': [
                {
                    '@Name': 'WINRS_NOPROFILE',
                    '#text': str(noprofile).upper()  # TODO remove str call
                },
                {
                    '@Name': 'WINRS_CODEPAGE',
                    '#text': str(codepage)  # TODO remove str call
                }
            ]
        }

        shell = rq['env:Envelope'].setdefault(
            'env:Body', {}).setdefault('rsp:Shell', {})
        shell['rsp:InputStreams'] = i_stream
        shell['rsp:OutputStreams'] = o_stream

        if working_directory:
            # TODO ensure that rsp:WorkingDirectory should be nested within
            # rsp:Shell
            shell['rsp:WorkingDirectory'] = working_directory
            # TODO: research Lifetime a bit more:
            # http://msdn.microsoft.com/en-us/library/cc251546(v=PROT.13).aspx
            # if lifetime:
            #    shell['rsp:Lifetime'] = iso8601_duration.sec_to_dur(lifetime)
            # TODO: make it so the input is given in milliseconds and converted
            # to xs:duration
        if idle_timeout:
            shell['rsp:IdleTimeOut'] = idle_timeout
        if env_vars:
            env = shell.setdefault('rsp:Environment', {})
            for key, value in env_vars.items():
                env['rsp:Variable'] = {'@Name': key, '#text': value}

        return xmltodict.unparse(rq)

    def CreateResponse(self,response):
        root = ET.fromstring(response)
        shell_id = next(node for node in root.findall('.//*')
                    if node.get('Name') == 'ShellId').text
        return shell_id


    def Command(self, shell_id, command, arguments=(), \
                    console_mode_stdin=True, skip_cmd_shell=False):
        """
        Run a command on a machine with an open shell
        @param string shell_id: The shell id on the remote machine.
         See #open_shell
        @param string command: The command to run on the remote machine
        @param iterable of string arguments: An array of arguments for this
         command
        @param bool console_mode_stdin: (default: True)
        @param bool skip_cmd_shell: (default: False)
        @return: The CommandId from the SOAP response.
         This is the ID we need to query in order to get output.
        @rtype string
        """
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',  # NOQA
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Command',  # NOQA
            shell_id=shell_id)}
        header = rq['env:Envelope']['env:Header']
        header['w:OptionSet'] = {
            'w:Option': [
                {
                    '@Name': 'WINRS_CONSOLEMODE_STDIN',
                    '#text': str(console_mode_stdin).upper()
                },
                {
                    '@Name': 'WINRS_SKIP_CMD_SHELL',
                    '#text': str(skip_cmd_shell).upper()
                }
            ]
        }
        cmd_line = rq['env:Envelope'].setdefault('env:Body', {})\
            .setdefault('rsp:CommandLine', {})
        cmd_line['rsp:Command'] = {'#text': command}
        if arguments:
            cmd_line['rsp:Arguments'] = ' '.join(arguments)

        return xmltodict.unparse(rq)

    def CommandResponse(self, response):
        root = ET.fromstring(response)
        CommandId = next(node for node in root.findall('.//*')
                          if node.tag.endswith('CommandId')).text
        return CommandId

    def Send(self, shell_id, command_id, command):
        
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',  # NOQA
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Send',  # NOQA
            shell_id=shell_id)}
        header = rq['env:Envelope']['env:Header']

        cmd_line = rq['env:Envelope'].setdefault('env:Body', {})\
            .setdefault('rsp:Send',{}) \
            .setdefault('rsp:Stream', {
                        "@Name":"stdin",
                        "@CommandId":command_id,
                        '#text': b64encode(command)
                        })
        #cmd_line['rsp:Stream'] = {'#text': b64encode(command)}
        return xmltodict.unparse(rq)

    def SendResponse(self, response):
        root = ET.fromstring(response)
        relates_to = next(node for node in root.findall('.//*')
                          if node.tag.endswith('RelatesTo')).text
        # TODO change assert into user-friendly exception
        #assert relates_to.replace('uuid:', '') == message_id
        return relates_to.replace('uuid:', '')

    def Receive(self, shell_id, command_id):
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',  # NOQA
            action='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/Receive',  # NOQA
            shell_id=shell_id)}

        stream = rq['env:Envelope'].setdefault(
            'env:Body', {}).setdefault('rsp:Receive', {})\
            .setdefault('rsp:DesiredStream', {})
        stream['@CommandId'] = command_id
        stream['#text'] = 'stdout stderr'
        return xmltodict.unparse(rq)

    def ReceiveResponse(self, response):
        root = ET.fromstring(response)
        stream_nodes = [node for node in root.findall('.//*')
                        if node.tag.endswith('Stream')]
        stdout = stderr = ''
        
        for stream_node in stream_nodes:
            if stream_node.text:
                if stream_node.attrib['Name'] == 'stdout':
                    stdout += str(b64decode(
                        stream_node.text.encode('ascii')))
                elif stream_node.attrib['Name'] == 'stderr':
                    stderr += str(b64decode(
                        stream_node.text.encode('ascii')))

        # We may need to get additional output if the stream has not finished.
        # The CommandState will change from Running to Done like so:
        # @example
        #   from...
        #   <rsp:CommandState CommandId="..." State="http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Running"/>  # NOQA
        #   to...
        #   <rsp:CommandState CommandId="..." State="http://schemas.microsoft.com/wbem/wsman/1/windows/shell/CommandState/Done">  # NOQA
        #     <rsp:ExitCode>0</rsp:ExitCode>
        #   </rsp:CommandState>
        command_done = len([node for node in root.findall('.//*')
                           if node.get('State', '').endswith(
                            'CommandState/Done')]) == 1
        try :
            return_code = int(next(node for node in root.findall('.//*')if node.tag.endswith('ExitCode')).text)
        except :
            return_code = None
        return stdout,stderr,return_code,command_done


    def Delete(self, shell_id):
        """
        Close the shell
        @param string shell_id: The shell id on the remote machine.
         See #open_shell
        @returns This should have more error checking but it just returns true
         for now.
        @rtype bool
        """
        rq = {'env:Envelope': self._get_soap_header(
            resource_uri='http://schemas.microsoft.com/wbem/wsman/1/windows/shell/cmd',  # NOQA
            action='http://schemas.xmlsoap.org/ws/2004/09/transfer/Delete',
            shell_id=shell_id)}

        # SOAP message requires empty env:Body
        rq['env:Envelope'].setdefault('env:Body', {})

        return xmltodict.unparse(rq)

    def DeleteResponse(self,response):
        root = ET.fromstring(response)
        relates_to = next(node for node in root.findall('.//*')
                          if node.tag.endswith('RelatesTo')).text
        # TODO change assert into user-friendly exception
        #assert relates_to.replace('uuid:', '') == message_id
        return relates_to.replace('uuid:', '')

    def _get_soap_header(self, action=None, resource_uri=None, shell_id=None, message_id=None):
        if not message_id:
            message_id = str(uuid4()).upper()
        header = {
            '@xmlns:xsd': 'http://www.w3.org/2001/XMLSchema',
            '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            '@xmlns:env': 'http://www.w3.org/2003/05/soap-envelope',

            '@xmlns:a': 'http://schemas.xmlsoap.org/ws/2004/08/addressing',
            '@xmlns:b': 'http://schemas.dmtf.org/wbem/wsman/1/cimbinding.xsd',
            '@xmlns:n': 'http://schemas.xmlsoap.org/ws/2004/09/enumeration',
            '@xmlns:x': 'http://schemas.xmlsoap.org/ws/2004/09/transfer',
            '@xmlns:w': 'http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd',
            '@xmlns:p': 'http://schemas.microsoft.com/wbem/wsman/1/wsman.xsd',
            '@xmlns:rsp': 'http://schemas.microsoft.com/wbem/wsman/1/windows/shell',  # NOQA
            '@xmlns:cfg': 'http://schemas.microsoft.com/wbem/wsman/1/config',

            'env:Header': {
                'a:To': 'http://windows-host:5985/wsman',
                'a:ReplyTo': {
                    'a:Address': {
                        '@mustUnderstand': 'true',
                        '#text': 'http://schemas.xmlsoap.org/ws/2004/08/addressing/role/anonymous'  # NOQA
                    }
                },
                'w:MaxEnvelopeSize': {
                    '@mustUnderstand': 'true',
                    '#text': '153600'
                },
                'a:MessageID': 'uuid:%s'%message_id,
                'w:Locale': {
                    '@mustUnderstand': 'false',
                    '@xml:lang': 'en-US'
                },
                'p:DataLocale': {
                    '@mustUnderstand': 'false',
                    '@xml:lang': 'en-US'
                },
                # TODO: research this a bit http://msdn.microsoft.com/en-us/library/cc251561(v=PROT.13).aspx  # NOQA
                # 'cfg:MaxTimeoutms': 600
                'w:OperationTimeout': 'PT60S',
                'w:ResourceURI': {
                    '@mustUnderstand': 'true',
                    '#text': resource_uri
                },
                'a:Action': {
                    '@mustUnderstand': 'true',
                    '#text': action
                }
            }
        }
        if shell_id:
            header['env:Header']['w:SelectorSet'] = {
                'w:Selector': {
                    '@Name': 'ShellId',
                    '#text': shell_id
                }
            }
        return header

