
import time
import socket 
import threading
import os
import hashlib

from json import dumps, loads
from queue import Queue

class Node:
    def __init__(self, host, port):

       
        self.stop = False
        self.stop_ping = False
        self.host = host
        self.port = port
        self.M = 16
        self.N = 2**self.M
        self.key = self.hasher(host+str(port))
        self.my_address = (host, port)
        self.successor = self.my_address
        self.predecessor = self.my_address
        self.failure_successor = self.my_address
        self.queue_put = Queue()
        self.queue_get = Queue()
        self.files = []
        self.backUpFiles = []
        
        # Initiate threads
        threading.Thread(target = self.listener).start()
        threading.Thread(target = self.handle_failure).start()

    def hasher(self, key):
        '''
        Gets the hashed value/key for any node/file
        Usage:
            For a node: self.hasher(node.host+str(node.port))
            For a file: self.hasher(file)
        '''
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % self.N

    def handleConnection(self, client, addr):
        '''
        Handled each inbound connection, called as a thread from the listener.
        '''

        msg = loads(client.recv(4096).decode('utf-8'))
        
        # packet msgs related to join and transfer files functionality
        if msg["command"] == "lookup_join":

            self.lookup_join(msg["key"], tuple(msg["new_node_addr"]))

        elif msg["command"] == "update_both":

            self.predecessor = tuple(msg["predecessor"])
            self.successor = tuple(msg["successor"])

        elif msg["command"] == "update_predecessor_and_files":

            self.transfer_files(msg["new_node_key"], tuple(msg["predecessor"]))
            self.predecessor = tuple(msg["predecessor"])
        
        elif msg["command"] == "update_files":

            self.files.extend(msg["files_list"])

        # packet msgs related to put functionality
        elif msg["command"] == "lookup_put":

            var = self.lookup_putget("put", msg["file"], tuple(msg["initial_sender"]))
            initial_sender = tuple(msg["initial_sender"])

            if var is not None:
                msg = {"command": "lookup_put_response", "resp_node": var}
                self.send_packet(initial_sender, msg)

        elif msg["command"] == "lookup_put_response":

            self.queue_put.put(tuple(msg["resp_node"]))

        elif msg["command"] == "save_file":

            self.files.append(msg["file"])
        
        # packet msgs related to get functionality
        elif msg["command"] == "lookup_get":

            var = self.lookup_putget("get", msg["file"], tuple(msg["initial_sender"]))
            initial_sender = tuple(msg["initial_sender"])

            if var == "file not found":
                msg = {"command": "file_not_found"}
                self.send_packet(initial_sender, msg)

            elif var is not None:
                msg = {"command": "lookup_get_response", "resp_node": var}
                self.send_packet(initial_sender, msg)

        elif msg["command"] == "lookup_get_response":

            self.queue_get.put(tuple(msg["resp_node"]))

        elif msg["command"] == "file_not_found":

            self.queue_get.put(None)
        
        # packet msgs related to leave functionality
        elif msg["command"] == "update_successor":

            self.successor = tuple(msg["successor"])
         
        elif msg["command"] == "update_predecessor_on_leave":

            self.predecessor = tuple(msg["predecessor"])
            self.files.extend(msg["files_list"])
        
        # packet msgs related to failure tolerance
        elif msg["command"] == "send_files_and_successor":

            msg = {"successor": self.successor, "files": self.files}
            client.send(dumps(msg).encode('utf-8'))

        elif msg['command'] == "node_failure":

            self.predecessor = tuple(msg["new_predecessor"])
            self.files = msg["backUp_files"]

        else:
            pass

    def listener(self):
        '''
        Function that accepts connection made by other nodes.
        For every inbound connection a new thread is initiated in the form of handleConnection function.
        '''
        listener = socket.socket()
        listener.bind((self.host, self.port))
        listener.listen(10)
        while not self.stop:
            client, addr = listener.accept()
            threading.Thread(target = self.handleConnection, args = (client, addr)).start()
        print ("Shutting down node:", self.host, self.port)
        try:
            listener.shutdown(2)
            listener.close()
        except:
            listener.close()

    # Called on the node that's joining
    def join(self, joiningAddr):
        '''
        Handles the logic of a node joining the DHT.
        '''
        # if first node being added to DHT, nothing needs to be updated
        if joiningAddr == "":
            return

        else:
            
            # send packet with new node's address and key to the known node (packet is received in handleConnection)
            msg_to_send = {"command": "lookup_join", "new_node_addr": self.my_address, "key": self.key}
            self.send_packet(joiningAddr, msg_to_send)
            
    def lookup_join(self, key, new_node_addr):
        '''
        Finds the location for the new node in the DHT 
        '''

        # Case when only two nodes exist in the DHT
        if self.successor == self.my_address and self.predecessor == self.my_address:
            
            self.handle_twoNode_join(new_node_addr)

            # Updating current node's state variables
            self.successor = self.predecessor = new_node_addr

        # General case
        else:
            
            successor_key = self.hasher(self.successor[0] + str(self.successor[1]))
            
            # catering to all conditions to confirm that new node should be current node's successor
            if ((self.key < successor_key and self.key <= key < successor_key) or 
                  (self.key > successor_key and not (successor_key <= key < self.key))):

                self.handle_general_join(new_node_addr)
                self.successor = new_node_addr

            # Otherwise, forward the lookup request to my successor
            else:
                self.fwd_lookup_request(key, new_node_addr)

    def handle_twoNode_join(self, new_node_addr):
        '''
        Sends required packet when only one node exists in DHT and a new node joins
        '''

        # Sending join info to the new node
        msg_to_send = {"command": "update_both", "predecessor": self.my_address, "successor": self.my_address}
        self.send_packet(new_node_addr, msg_to_send)


    def handle_general_join(self, new_node_addr):
        '''
        Sends required packets when more than two nodes exist in DHT and a new node joins
        '''

        # send join info to the new node
        msg_to_send = {"command": "update_both", "predecessor": self.my_address, "successor": self.successor}
        self.send_packet(new_node_addr, msg_to_send)

        # send join info to successor (successor needs to update its predecessor to new_node)
        new_node_key = self.hasher(new_node_addr[0]+str(new_node_addr[1]))
        msg_to_send = {"command": "update_predecessor_and_files", "predecessor": new_node_addr, "new_node_key": new_node_key}
        self.send_packet(self.successor, msg_to_send)

    def fwd_lookup_request(self, key, new_node_addr):
        '''
        Handles the msg to be sent to successor to request lookup for new node
        '''

        msg_to_send = {"command": "lookup_join", "new_node_addr": new_node_addr, "key": key}
        self.send_packet(self.successor, msg_to_send)

    def send_packet(self, dest_addr, msg):
        '''
        Initiates connection with the intended node and sends packet
        '''
        soc = socket.socket()
        with soc as open_socket:
            open_socket.connect(dest_addr)
            open_socket.send(dumps(msg).encode('utf-8'))	

    def lookup_putget(self, lookup_type: str, fileName, initial_sender):
        '''
        Searches DHT for responsible node for the file
        '''
        
        key = self.hasher(fileName)
        predecessor_key = self.hasher(self.predecessor[0] + str(self.predecessor[1]))
        
        # Caters to put functionality
        if lookup_type == "put":

            # check whether all conditions are met to ensure that current node is responsible for the given fileName
            if ((self.key > predecessor_key and key < self.key and key > predecessor_key) or
                (self.key < predecessor_key and not (key < predecessor_key and key > self.key))):
                
                    return self.my_address

            # Otherwise request current node's successor to search 
            else:
                msg = {"command": "lookup_put", "file": fileName, "initial_sender": initial_sender}
                self.send_packet(self.successor, msg)
        
        
        # caters to get functionality
        elif lookup_type == "get":

            # Alternatively, could have been checked using the conditions above. 
            # But checking in the files list reduces the complexity of code
            if fileName in self.files:
                return self.my_address
            
            # case when the entire DHT has been searched and file not found
            if fileName not in self.files and self.successor == initial_sender:
                return "file not found"
                
            else:
                msg = {"command": "lookup_get", "file": fileName, "initial_sender": initial_sender}
                self.send_packet(self.successor, msg)


    def put(self, fileName):
        '''
        Places the file at the required node
        '''

        # Find node responsible for file
        addr = self.lookup_putget("put", fileName, self.my_address)
        
        # if the current node is responsible, just add fileName to its files list
        if addr == self.my_address:
            
            # put the file in my files list
            self.files.append(fileName)

        else:

            # wait until the lookup is complete and address of responsible node is received
            addr = self.queue_put.get()

            # send the fileName to that node, that node will then save the file (functionality in handleConnection)
            msg = {"command": "save_file", "file": fileName}
            self.send_packet(addr, msg)
    
    def get(self, fileName):
        '''
        This function finds whether any node has the file given by fileName.
        Returns fileName if it exists in the DHT, else returns None. 
        '''
        
        addr = self.lookup_putget("get", fileName, self.my_address)

        if addr == self.my_address:
            return fileName

        else:
            # get the address of node that has file 
            addr = self.queue_get.get()
             
            # file doesnt exist in network so return None
            if addr is None:
                return None
            else:
                # file exists in network, return its name
                return fileName

    def transfer_files(self, new_node_key, new_node):
        '''
        Transfers the files to new node that joins the network
        '''
        
        predecessor_key = self.hasher(self.predecessor[0] + str(self.predecessor[1]))
        new_node_file_list = []

        for filename in self.files:

            key = self.hasher(filename)
            if ((new_node_key > predecessor_key and key < new_node_key and key > predecessor_key) or
                    (new_node_key < predecessor_key and not (key < predecessor_key and key > new_node_key))):

                new_node_file_list.append(filename)

        # need to delete these files from my own self.files after iteration
        for filename in new_node_file_list:
            self.files.remove(filename)
    
        # send the list to the new node
        msg = {"command": "update_files", "files_list": new_node_file_list}
        self.send_packet(new_node, msg)
    
    def handle_failure(self):
        '''
        Handles the scenario of a node randomly failing in the network
        '''

        while not self.stop:
            if self.successor[1] != self.port:
                
                # create a socket object 
                open_socket = socket.socket()
                time.sleep(0.5)
                
                # try to connect to the successor and ask for its files and successor
                try:
                    open_socket.connect(self.successor)
                    ping_msg = {"command": "send_files_and_successor", "dest_addr": self.my_address}
                    open_socket.send(dumps(ping_msg).encode('utf-8'))
                
                # if connection fails, means the node being pinged (i.e the successor) has left the network
                except ConnectionError:
                    
                    # cater to case when only one node left in DHT after the failure event
                    if self.failure_successor == self.my_address:

                        self.predecessor = self.successor = self.my_address
                        self.files.extend(self.backUpFiles)
                        open_socket.close()
                    
                    # general case
                    else:
                        
                        msg = {"command": "node_failure", "backUp_files": self.backUpFiles, "new_predecessor": self.my_address}
                        self.successor = self.failure_successor
                        self.send_packet(self.failure_successor, msg)
                        continue
                        
                # store the received files in the backUp files and update the backup/failure successor 
                ping_response = loads(open_socket.recv(4096).decode('utf-8'))
                self.failure_successor = tuple(ping_response["successor"])
                self.backUpFiles= ping_response["files"]
            
    def leave(self):
        '''
        Handles a node leaving the network. 
        '''
        # communicate to predecessor about leaving DHT
        msg = {"command": "update_successor", "successor": self.successor}
        self.send_packet(self.predecessor, msg)
        
        # communicate to successor about leaving DHT and send all my files to it
        msg = {"command": "update_predecessor_on_leave", "predecessor": self.predecessor, "files_list": self.files}
        self.send_packet(self.successor, msg)
        
        # close the listener thread
        self.stop = True
