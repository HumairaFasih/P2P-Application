
from queue import Queue
import threading

class Node:

    from helpers import hasher, send_packet, format_msg
    from connection_handler import listener, handle_connection
    from join import join, place_node, two_node_join, general_join, forward_request
    from disconnect import handle_failure, leave
    from file_handler import transfer_files, find_node, place_file, find_file

    def __init__(self, host, port):

        self.stop = False
        self.stop_ping = False
        self.host = host
        self.port = port
        self.M = 16
        self.N = 2**self.M
        self.key = self.hasher(host + str(port))
        self.my_addr = (host, port)
        self.successor = self.my_addr
        self.predecessor = self.my_addr
        self.failure_successor = self.my_addr
        self.placefile_queue = Queue()
        self.searchfile_queue = Queue()
        self.files = []
        self.backup_files = []

        # Initiate threads
        threading.Thread(target=self.listener).start()
        threading.Thread(target=self.handle_failure).start()
    
    def kill(self):
        ''' Used in testing '''

        self.stop = True
