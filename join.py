""" join.py
This module handles all functionality required to successfully allow a node to join the network. 
"""

# Called on the node that's joining the network
def join(self, joining_addr):
    ''' Handle a node joining the network '''

    # Case when first node joins network (No updates needed)
    if joining_addr == "":
        return

    # General case
    else:

        # Send packet with the address and key associated with new node to the known node
        # This packet is received, parsed and processed in handleConnection function
        msg = self.format_msg(
            "place_node", new_node_addr=self.my_addr, key=self.key)
        self.send_packet(joining_addr, msg)


def place_node(self, key, new_node_addr):
    ''' Find appropriate location for new node and add it to network '''

    # Case when only two nodes exist in the network
    if self.successor == self.my_addr and self.predecessor == self.my_addr:

        self.two_node_join(new_node_addr)

        # Update current node's state variables
        self.successor = self.predecessor = new_node_addr

    # General case
    else:

        successor_key = self.hasher(
            self.successor[0] + str(self.successor[1]))

        # Check all conditions to confirm that new node should be current node's successor
        if ((self.key < successor_key and self.key <= key < successor_key) or
                (self.key > successor_key and not (successor_key <= key < self.key))):

            self.general_join(new_node_addr)
            self.successor = new_node_addr

        # If none of the conditions are met, forward search request to current node's successor
        else:
            self.forward_request(key, new_node_addr)


def two_node_join(self, new_node_addr):
    '''
    Handles creation and sending of appropriate packet on join
    Network state: Only one node exists in network
    '''

    # Send join info to the new node
    msg = self.format_msg(
        "update_both", predecessor=self.my_addr, successor=self.my_addr)
    self.send_packet(new_node_addr, msg)


def general_join(self, new_node_addr):
    '''
    Handles creation and sending of appropriate packets on join
    Network state: More than two nodes exist in network
    '''

    # Send join info to the new node
    msg = self.format_msg(
        "update_both", predecessor=self.my_addr, successor=self.successor)
    self.send_packet(new_node_addr, msg)

    # Send join info to successor
    # (Successor needs to update its predecessor to new_node)
    new_key = self.hasher(new_node_addr[0] + str(new_node_addr[1]))
    msg = self.format_msg("update_predecessor_and_files",
                          predecessor=new_node_addr, new_node_key=new_key)
    self.send_packet(self.successor, msg)


def forward_request(self, key, new_node_addr):
    ''' Forward search request to successor '''

    msg = self.format_msg(
        "place_node", new_node_addr=new_node_addr, key=key)
    self.send_packet(self.successor, msg)
