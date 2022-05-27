""" network_join_handler.py
This file handles all functionality required to successfully allow a user to join the network. 
"""

# Called on the user that's joining the network
def join(self, joining_addr):
    ''' Handle a user joining the network '''

    # Case when first user joins network (No updates needed)
    if joining_addr == "":
        return

    # General case
    else:

        # Sending packet with the address and key associated with new user to the known user
        # This packet is received, parsed and processed in handleConnection function
        msg = self.format_msg(
            "place_user", new_user_addr=self.my_addr, key=self.key)
        self.send_packet(joining_addr, msg)


def place_user(self, key, new_user_addr):
    ''' Find appropriate location for new user and add it to network '''

    # Case when only two users exist in the network
    if self.successor == self.my_addr and self.predecessor == self.my_addr:

        self.two_user_join(new_user_addr)

        # Updating current user's state variables
        self.successor = self.predecessor = new_user_addr

    # General case
    else:

        successor_key = self.hasher(
            self.successor[0] + str(self.successor[1]))

        # Checking all conditions to confirm that new user should be current user's successor
        if ((self.key < successor_key and self.key <= key < successor_key) or
                (self.key > successor_key and not (successor_key <= key < self.key))):

            self.general_join(new_user_addr)
            self.successor = new_user_addr

        # If none of the conditions are met, the search request is forwarded to current user's successor
        else:
            self.forward_search_request(key, new_user_addr)


def two_user_join(self, new_user_addr):
    '''
    Handles creation and sending of appropriate packet on join
    Network state: Only one user exists in network
    '''

    # Sending join info to the new user
    msg = self.format_msg(
        "update_both", predecessor=self.my_addr, successor=self.my_addr)
    self.send_packet(new_user_addr, msg)


def general_join(self, new_user_addr):
    '''
    Handles creation and sending of appropriate packets on join
    Network state: More than two users exist in network
    '''

    # Sending join info to the new user
    msg = self.format_msg(
        "update_both", predecessor=self.my_addr, successor=self.successor)
    self.send_packet(new_user_addr, msg)

    # Sending join info to successor
    # (Successor needs to update its predecessor to new_user)
    new_key = self.hasher(new_user_addr[0] + str(new_user_addr[1]))
    msg = self.format_msg("update_predecessor_and_files",
                          predecessor=new_user_addr, new_user_key=new_key)
    self.send_packet(self.successor, msg)


def forward_search_request(self, key, new_user_addr):
    ''' Forward search request to successor '''

    msg = self.format_msg(
        "place_user", new_user_addr=new_user_addr, key=key)
    self.send_packet(self.successor, msg)


def transfer_files(self, new_user_key, new_user):
    ''' Transfer files to new user that joins the network '''

    predecessor_key = self.hasher(
        self.predecessor[0] + str(self.predecessor[1]))
    new_user_file_list = []

    # For each file that current user has, check whether the file should be relocated to the new user
    # The above decision is made based on the file's key
    #  All files that meet this condition are added to the list of files to be sent to the new user
    for filename in self.files:

        key = self.hasher(filename)
        if ((new_user_key > predecessor_key and key < new_user_key and key > predecessor_key) or
                (new_user_key < predecessor_key and not (key < predecessor_key and key > new_user_key))):

            new_user_file_list.append(filename)

    # Delete these files from current user's list of files after iteration
    for filename in new_user_file_list:
        self.files.remove(filename)

    # Send the list to the new user
    msg = self.format_msg("update_files", files_list=new_user_file_list)
    self.send_packet(new_user, msg)
