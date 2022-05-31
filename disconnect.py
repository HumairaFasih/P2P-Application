
""" disconnect.py
This module implements all functionality for node disconnection from the network.
(Informed and Random Disconnection).
"""

from json import dumps, loads
import socket
import time

def handle_failure(self):
    ''' Handle the scenario of random node failure/disconnection in the network '''

    while not self.stop:
        if self.successor[1] != self.port:

            # Create a socket object
            open_socket = socket.socket()
            time.sleep(0.5)

            # Try to connect to the successor and ask for its files and successor
            try:
                open_socket.connect(self.successor)
                ping_msg = self.format_msg(
                    "send_files_and_successor", dest_addr=self.my_addr)
                open_socket.send(dumps(ping_msg).encode('utf-8'))

            # If connection fails, it signifies the node being pinged (i.e the successor) has left the network
            except ConnectionError:

                # Cater to case when only one node left in network after the failure event
                if self.failure_successor == self.my_addr:

                    self.predecessor = self.successor = self.my_addr
                    self.files.extend(self.backup_files)
                    open_socket.close()

                # General case
                else:

                    msg = self.format_msg("node_failure", backup_files=self.backup_files,
                            new_predecessor=self.my_addr)
                    self.successor = self.failure_successor
                    self.send_packet(self.failure_successor, msg)
                    continue

            # Store the received files as backup files and update the backup/failure successor
            ping_response = loads(open_socket.recv(4096).decode('utf-8'))
            self.failure_successor = tuple(ping_response["successor"])
            self.backup_files = ping_response["files"]

def leave(self):
    ''' Handle a node leaving the network gracefully '''

    # Communicate to predecessor about leaving network
    msg = self.format_msg("update_successor", successor=self.successor)
    self.send_packet(self.predecessor, msg)

    # Communicate to successor about leaving network and send all my files to it
    msg = self.format_msg("update_predecessor_on_leave",
                            predecessor=self.predecessor, files_list=self.files)
    self.send_packet(self.successor, msg)

    # Close the listener thread
    self.stop = True
