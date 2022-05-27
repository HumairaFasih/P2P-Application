""" helpers.py
This module contains helper functions to implement core functionalities.
"""

from json import dumps
import hashlib
import socket

def hasher(self, key) -> int:
        '''
        Get the hashed value/key for any node/file
        Usage:
            For a node: self.hasher(node.host + str(node.port))
            For a file: self.hasher(file)
        '''
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.N

def format_msg(self, command: str, **kwargs) -> dict:
    ''' Format the information to be sent in a packet in JSON notation '''

    msg = {"command": command}
    msg.update(**kwargs)
    return msg
    
def send_packet(self, dest_addr, msg):
    ''' Initiate connection with the intended node and send packet '''

    soc = socket.socket()
    with soc as open_socket:
        open_socket.connect(dest_addr)
        open_socket.send(dumps(msg).encode('utf-8'))