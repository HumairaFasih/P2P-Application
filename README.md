
# Distributed Peer-to-Peer Networked Application
## About
This project is an implementation of a Distributed P2P Networked Application. The users in the network are represented as nodes, and are able to communicate with each other concurrently. The app uses Thread-based parallelism and Python's socket API to implement the design of the network model. <br>
Users and files are identified by keys obtained through a hash function, and each file is associated with a certain user.
Files are rehashed and assigned to relevant users when a user joins or leaves the network - users may also fail randomly while on the network. <br> <br>
 
The full application functionality is tested via system tests to ensure it works as intended. 

## Usage

To run the tests on your local machine's CLI, clone the repository and run the tester.py with the following command:

On MacOS:   
(To avoid use of MacOS built-in python 2.7 interpretor)
```
python3 tester.py <port>
```
On Windows:
```
python tester.py <port>
```
<b> Note: </b> It works with a restricted set of port numbers. <br> 
Ensure the port number falls within the range: 1000 < port < 65500 <br>





