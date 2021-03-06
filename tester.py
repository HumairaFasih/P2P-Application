from main_DHT import Node
import time
import os
import sys
import uuid
import shutil  

def generate_files(files):

    for f in files:
        file = open(f,"w")
        lowercase_str = uuid.uuid4().hex  
        file.write(lowercase_str.upper())
        file.close()

def remove_files(file):

    for f in files:
        os.remove(f)

def initiate(p):

    print("\n \t \u001b[36m --* Testing Initialization *-- \u001b[0m")
    nodes = []

    try:
        n1 = Node("localhost", p[0])
        nodes.append(n1)
        n2 = Node("localhost", p[1])
        nodes.append(n2)
        n3 = Node("localhost", p[2])
        nodes.append(n3)
        n4 = Node("localhost", p[3])
        nodes.append(n4)
        n5 = Node("localhost", p[4])
        nodes.append(n5)

    except Exception as e:
        print ("RunTime Error in node initialization! Following exception occurred:")
        print (e)
        return

    if nodes[0].successor == ("localhost",p[0]) and nodes[0].predecessor == ("localhost",p[0]):
        print ("\nInitialization Successful!")
    else:
        print ("Wrong initialization!")

    print("\n \u001b[1m Initialization testing completed. \u001b[0m")
    return nodes

def test_join(nodes,p):

    print("\n \t \u001b[36m --* Testing Join Functionality *--  \u001b[0m \n")
    print ("Case 1: Checking for corner case of 1 node.")
    nodes[0].join("")
    time.sleep(2)

    if nodes[0].successor == ("localhost",p[0]) and nodes[0].predecessor == ("localhost",p[0]):
        print ("Case 1 passed. \t")
    else:
        print ("Case 1 failed. \t")

    print("Case 2: Checking for corner case of 2 nodes.")
    nodes[1].join(("localhost", p[0]))
    time.sleep(2)

    if nodes[1].successor == ("localhost",p[0]) and nodes[1].predecessor == ("localhost",p[0]) and nodes[0].successor == ("localhost",p[1]) and nodes[0].predecessor == ("localhost",p[1]):
        print ("Case 2 passed. \t")

    else:
        print ("Case 2 failed. \t")

    print ("Case 3: Checking for general case.")
    nodes[2].join(("localhost", p[0]))
    time.sleep(2)
    nodes[3].join(("localhost", p[0]))
    time.sleep(2)
    nodes[4].join(("localhost", p[1]))
    time.sleep(2)
    nodes.sort(key=lambda x: x.key, reverse=False)
    correct = True

    for i in range(len(nodes)):
        if nodes[i].successor == None:
            correct = False

        elif nodes[i].successor[1] == nodes[(i+1) % len(nodes)].port and nodes[i].predecessor[1] == nodes[i-1].port:
            continue
        else:
            correct = False

    if correct:
        print ("Case 3 passed. \t")
        
    else:
        print ("Case 3 failed. \t(0)")

    print("\n \u001b[1m Join testing completed. \u001b[0m")
    return nodes

def test_place_and_search(nodes, files):

    print("\n \t \u001b[36m--* Testing File Placement and File Search *--  \u001b[0m \n")
    print ("Placing files on network")
    fileHashes = []

    for i in range(len(files)):
        fileHashes.append(nodes[0].hasher(files[i]))
        nodes[0].place_file(files[i])

    time.sleep(1)
    print("\n\t \u001b[4m Testing File Placement \u001b[0m")
    correct = True

    for i in range(len(files)):
        for j in range(len(nodes)):

            if ((fileHashes[i] <= nodes[j].key and fileHashes[i] > nodes[j-1].key) or
                           (fileHashes[i] > nodes[-1].key and j == 0)):

                if files[i] not in nodes[j].files:
                    correct = False
    if correct:
        print ("\nAll files placed successfully! \t")
    else:
        print ("\nSome or all files placed incorrectly. \t")

    print("\n\t \u001b[4m Testing File Search \u001b[0m")
    remove_files(files)
    time.sleep(4)
    print ("\nChecking for a file placed on network DHT...")

    if nodes[0].find_file(files[0]) == None:
        print ("Could not retrieve a file placed on network DHT")
        print ("File Search failed. \t")

    print ("Checking for files not placed originally...")

    if nodes[0].find_file("absent.txt") != None:
        print ("File retrieved against a key that was not placed on network DHT.")
        print ("File Search failed. \t")

    print ("\nAll files retrieved successfully! \t")
    print("\n \u001b[1m File Placement and File Search testing completed. \u001b[0m")

def test_file_rehashing(nodes, files, sp):

    print("\n \t  \u001b[36m --* Testing File Rehashing *--  \u001b[0m \n")
    ps = [sp+0, sp+1, sp+2]
    print ("New nodes joining network...")

    for p in ps:
        n1 = Node("localhost", p)
        n1.join((nodes[0].host, nodes[0].port))
        nodes.append(n1)
        time.sleep(2)
        
    nodes.sort(key=lambda x: x.key, reverse=False)
    correct = True
    print ("\nChecking if files rehashed correctly...")

    for i in range(len(files)):
        for j in range(len(nodes)):
            if nodes[j].hasher(files[i]) <= nodes[j].key and nodes[j].hasher(files[i]) > nodes[j-1].key or nodes[j].hasher(files[i]) > nodes[-1].key and i == 0:
                if files[i] not in nodes[j].files:
                    correct = False
    if correct:
        print ("\nAll files rehashed successfully! \t")
    else:
        print ("Some or all files have been rehashed incorrectly. \t")
        return nodes

    print("\n \u001b[1m File Rehashing testing completed. \u001b[0m")
    return nodes 

        
def test_leave(nodes, files):

    print("\n\t  \u001b[36m--* Testing Leave *--  \u001b[0m\n")
    ind = 0

    for i in range(len(nodes)):
        if files[0] in nodes[i].files:
            ind = i

    print ("Calling leave function on a node...")
    nodes[ind].leave()
    time.sleep(2)
    del nodes[ind]
    correct = True
    print ("Checking for successor and predecessor updation...\n")

    for i in range(len(nodes)):
        if nodes[i].successor == None:
            correct = False
        elif nodes[i].successor[1] == nodes[(i+1) % len(nodes)].port and nodes[i].predecessor[1] == nodes[i-1].port:
            continue
        else:
            correct = False

    if correct:
        print ("Successor and Predecessor updated successfully for all nodes!\t")
    else:
        print ("Wrong successor and predecessor returned.\t")
        return nodes 

    print ("\nChecking for file transfer...\n")

    if files[0] in nodes[ind % len(nodes)].files:
        print ("Files transferred correctly!\t")
    else:
        print ("Files updated incorrectly. \t(0)")
        return nodes

    print("\n \u001b[1m Leave testing completed. \u001b[0m")
    return nodes 

def kill(nodes):

    for n in nodes:
        n.kill()

def test_failure_tolerance(nodes, files):

    print("\n\t  \u001b[36m --* Testing Failure Tolerance *--  \u001b[0m \n")
    ind = 0

    for i in range(len(nodes)):
        if files[0] in nodes[i].files:
            ind = i

    print ("Killing a node...")
    nodes[ind].kill()
    time.sleep(3)
    del nodes[ind]
    correct = True

    for i in range(len(nodes)):
        if nodes[i].successor == None:
            correct = False
        elif nodes[i].successor[1] == nodes[(i+1) % len(nodes)].port and nodes[i].predecessor[1] == nodes[i-1].port:
            continue
        else:
            correct = False

    if correct:
        print ("\nSuccessor and Predecessor updated successfully for all nodes!\t")
    else:
        fail_var = "Wrong successor and predecessor returned.\t(0)"
        print(f"\033[96m {fail_var}\033[00m")
        return nodes

    print ("Checking for file transfer...\n")

    if files[0] in nodes[ind % len(nodes)].files:
        print ("Files placed at right node after failure!\t")
    else:
        fail_var = "Files recovery failed. \t(0)"
        print(f"\033[96m {fail_var}\033[00m")
        return nodes 

    print("\n \u001b[1m Failure Tolerance testing completed. \u001b[0m \n")
    return nodes 


def printN(nodes):

    print ("\nPrinting all nodes.")
    for n in nodes:
        print (n.host, n.port, n.key)
        print (n.successor, n.predecessor)
        print (n.backUpFiles)
        print (n.files)
        print ([n.hasher(x) for x in n.files])
        print ("--------------------------------------------")

try:
    start_port = int(sys.argv[1])
except:
    print ("Run this script file as 'python tester.py <port>' (1000 < port < 65500).")
    os._exit(1)

p = [start_port+0, start_port+1, start_port+2, start_port+3, start_port+4]
files = ["dummy.txt", "dummy2.txt","dummy3.txt","dummy4.txt","dummy5.txt","dummy6.txt","dummy7.txt","dummy8.txt"]


nodes = initiate(p)
nodes  = test_join(nodes, p)
generate_files(files)
test_place_and_search(nodes, files)
nodes = test_file_rehashing(nodes, files, start_port+5)
nodes = test_leave(nodes, files)
nodes = test_failure_tolerance(nodes, files)

path = "./"
files = os.listdir(path)

for f in files:
    if "dummy" in f:
        os.remove(os.path.join(path, f))
    if "localhost" in f:
        shutil.rmtree(os.path.join(path, f))
os._exit(1)
