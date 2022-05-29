""" file_handler.py
This module contains implementation of file placement, transfer and search functionalities
"""

def transfer_files(self, new_node_key, new_node):
    ''' Transfer files to new node that joins the network '''

    predecessor_key = self.hasher(
        self.predecessor[0] + str(self.predecessor[1]))
    new_node_file_list = []

    # For each file that current node has, check whether the file should be relocated to the new node
    # The above decision is made based on the file's key
    #  All files that meet this condition are added to the list of files to be sent to the new node
    for filename in self.files:

        key = self.hasher(filename)
        if ((new_node_key > predecessor_key and key < new_node_key and key > predecessor_key) or
                (new_node_key < predecessor_key and not (key < predecessor_key and key > new_node_key))):

            new_node_file_list.append(filename)

    # Delete these files from current node's list of files after iteration
    for filename in new_node_file_list:
        self.files.remove(filename)

    # Send the list to the new node
    msg = self.format_msg("update_files", files_list=new_node_file_list)
    self.send_packet(new_node, msg)


def find_node(self, command: str, filename, initial_sender):
    ''' Search network for responsible node for the file '''

    key = self.hasher(filename)
    predecessor_key = self.hasher(
        self.predecessor[0] + str(self.predecessor[1]))

    # Cater to file placement functionality
    if command == "place_file":

        # Check all conditions to confirm current node is responsible for the given file
        if ((self.key > predecessor_key and key < self.key and key > predecessor_key) or
                (self.key < predecessor_key and not (key < predecessor_key and key > self.key))):

            return self.my_addr

        # If none of the conditions are met, forward search request to current node's successor
        else:
            msg = self.format_msg(
                "place_file_search", file=filename, initial_sender=initial_sender)
            self.send_packet(self.successor, msg)

    # Cater to file search functionality
    elif command == "find_file":

        # Check if current node has the file
        # Alternatively, this could have been checked using the conditions above
        # But checking in the files list reduces code complexity
        if filename in self.files:
            return self.my_addr

        # Case when the entire network has been searched and no node has the file
        elif filename not in self.files and self.successor == initial_sender:
            return "file not found"

        # Forward search request to current node's successor
        else:
            msg = self.format_msg(
                "find_file_search", file=filename, initial_sender=initial_sender)
            self.send_packet(self.successor, msg)

def place_file(self, filename):
    ''' Assign file to the correct node in the network '''

    # Find node responsible for file
    addr = self.find_node("place_file", filename, self.my_addr)

    # If the current node is responsible, update its files list
    if addr == self.my_addr:

        self.files.append(filename)

    else:

        # Wait until the lookup is complete and address of responsible node is received
        addr = self.placefile_queue.get()

        # Send the file to responsible node which will then save it
        msg = self.format_msg("save_file", file=filename)
        self.send_packet(addr, msg)

def find_file(self, filename):
    '''
    Check whether file is available on the network
    Return name of file if file is present, else return None
    '''

    addr = self.find_node("find_file", filename, self.my_addr)

    # File is with the current node
    if addr == self.my_addr:
        return filename

    else:
        # Get the address of node that has file
        addr = self.searchfile_queue.get()

        # If file not available on network, return None
        if addr is None:
            return None

        # File exists on network, return its name
        else:
            return filename
