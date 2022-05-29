"""" connection_handler.py
This module handles incoming requests from other nodes to connect, and handles packets sent by them.
"""

from json import dumps, loads
import socket
import threading

# Called on the node that's joining the network
def listener(self):
    '''
    Accept connection made by other nodes.
    For every inbound connection a new thread is initiated in the form of handle_connection function.
    '''

    listener = socket.socket()
    listener.bind((self.host, self.port))
    listener.listen(10)

    while not self.stop:

        client, addr = listener.accept()
        threading.Thread(target=self.handle_connection,
                            args=(client, addr)).start()

    print("Shutting down node:", self.host, self.port)

    try:
        listener.shutdown(2)
        listener.close()
    except:
        listener.close()

def handle_connection(self, client, addr):
    ''' Handle each inbound connection, called as a thread from the listener '''

    msg = loads(client.recv(4096).decode('utf-8'))

    # Packet msgs related to node joining and file transfer functionality
    if msg["command"] == "place_node":

        self.place_node(msg["key"], tuple(msg["new_node_addr"]))

    elif msg["command"] == "update_both":

        self.predecessor = tuple(msg["predecessor"])
        self.successor = tuple(msg["successor"])

    elif msg["command"] == "update_predecessor_and_files":

        self.transfer_files(msg["new_node_key"], tuple(msg["predecessor"]))
        self.predecessor = tuple(msg["predecessor"])

    elif msg["command"] == "update_files":

        self.files.extend(msg["files_list"])

    # Packet msgs related to file placement functionality
    elif msg["command"] == "place_file_search":

        var = self.find_node(
            "place_file", msg["file"], tuple(msg["initial_sender"]))
        initial_sender = tuple(msg["initial_sender"])

        if var is not None:
            msg = self.format_msg("fileplace_response", resp_node=var)
            self.send_packet(initial_sender, msg)

    elif msg["command"] == "fileplace_response":

        self.placefile_queue.put(tuple(msg["resp_node"]))

    elif msg["command"] == "save_file":

        self.files.append(msg["file"])

    # Packet msgs related to file search functionality
    elif msg["command"] == "find_file_search":

        var = self.find_node(
            "find_file", msg["file"], tuple(msg["initial_sender"]))
        initial_sender = tuple(msg["initial_sender"])

        if var == "file not found":
            msg = self.format_msg("file_not_found")
            self.send_packet(initial_sender, msg)

        elif var is not None:
            msg = self.format_msg("filesearch_response", resp_node=var)
            self.send_packet(initial_sender, msg)

    elif msg["command"] == "filesearch_response":

        self.searchfile_queue.put(tuple(msg["resp_node"]))

    elif msg["command"] == "file_not_found":

        self.searchfile_queue.put(None)

    # Packet msgs related to node leave functionality
    elif msg["command"] == "update_successor":

        self.successor = tuple(msg["successor"])

    elif msg["command"] == "update_predecessor_on_leave":

        self.predecessor = tuple(msg["predecessor"])
        self.files.extend(msg["files_list"])

    # Packet msgs related to failure tolerance functionality
    elif msg["command"] == "send_files_and_successor":

        msg = {"successor": self.successor, "files": self.files}
        client.send(dumps(msg).encode('utf-8'))

    elif msg['command'] == "node_failure":

        self.predecessor = tuple(msg["new_predecessor"])
        self.files = msg["backup_files"]

    else:
        pass
