"""Socket programming - Server side script"""

#pylint: disable = too-many-branches
#pylint: disable = global-statement

import queue
import select
import socket
HOST = ''
PORT = 5000
BUFSIZE = 1024
ADDR = (HOST, PORT)

#use a global dictionary to map each client's ip to their Name
USER_NAMES = {}
USER_VERIFIED = {} #0 = user is not verified 1 = user has been asked for verification
                   #2 = user is verified
ONLINE = [] #list of online users
USER_SOCKETS = {} #map each user names to their assigned socket
CHAT_SESSION = {}


def listen():
    """Use non blocking sockets to check for client_sockets
    """

    global USER_NAMES #because it needs to be changed if there's a new user
    global USER_VERIFIED #use this to keep track of which users have been asked for their names
    global ONLINE
    global USER_SOCKETS

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setblocking(0)

    #Bind the socket to ADDR (specified above)
    server_socket.bind(ADDR)
    server_socket.listen(5)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    #list of objects that will be checked for incoming data that
    #needs to be read
    inputs = [server_socket]

    #list of sockets to which we expect to write
    outputs = []

    #outgoing message queue
    message_queues = {}

    while inputs:
        #select returns three tuples
        #read_from will have a list of socket objects from which new data will be read
        #write_to will havee a list of socket objects to which data will be written to
        #exceptions contains a list of sockets objects that threw exceptions
        #   exceptions sockets should be explictly closed
        read_from, write_to, exceptions = select.select(inputs, outputs, inputs)

        for sock in read_from:
            if sock is server_socket:
                client_socket, client_address = sock.accept()
                # client_address[0] = client_address[0]
                print("New client", client_address[0])

                #check if the user already exists
                #if not set, their ip in USER_NAMES to 0
                if not USER_NAMES.get(client_address[0]):
                    print("Connected to %s", client_address)
                    USER_VERIFIED[client_address[0]] = 0
                else:
                    print("Connected to %s", USER_NAMES[client_address[0]])


                client_socket.setblocking(0)
                inputs.append(client_socket)
                message_queues[client_socket] = queue.Queue()
            else:
                data = sock.recv(BUFSIZE).decode('utf-8')
                if data:
                    print("Data received from %s: %s" %(sock.getpeername(), data))

                    #If the user doesn't exist, ask them for their name
                    #do so by putting the message in their  message_queue
                    #client_address[0] contains their ip
                    if USER_VERIFIED[client_address[0]] == 0:
                        message = "You seem new! What's your Name ?"
                        message_queues[sock].put(message)

                        #this means, the user has been asked for thier name
                        #next response from the same user is their name
                        #in that case, turn it to 2
                        USER_VERIFIED[client_address[0]] = 1

                    elif USER_VERIFIED.get(client_address[0]) == 1:
                        #this means, user just sent their name
                        USER_NAMES[client_address[0]] = data
                        #Also store the associated socket, key will be the user's ip
                        USER_SOCKETS[USER_NAMES[client_address[0]]] = sock

                        #This means, the user is verified (has a name)
                        USER_VERIFIED[client_address[0]] = 2
                        #Mark user as online
                        ONLINE.append(client_address[0])

                        #Send them back hello message
                        message = "Hi " + data
                        message_queues[sock].put(message)


                    elif data == 'online':
                        message = ''
                        for each_user in ONLINE:
                            message += USER_NAMES[each_user] + ','
                        message_queues[sock].put(message)

                    elif data == 'logout':
                        #Don't receive anymore messages from the user
                        #The socket related to the users will be cleaned up
                        #when there's no data coming from them
                        ONLINE.remove(client_address[0])
                        inputs.remove(sock)

                    elif 'talk' in data:
                        receiver = data.split(' ')[-1]
                        # sender = USER_NAMES[client_address[0]]
                        CHAT_SESSION[USER_NAMES[client_address[0]]] = receiver
                        CHAT_SESSION[receiver] = USER_NAMES[client_address[0]]
                        message = 'Chat session active: '
                        message_queues[sock].put(message)
                        print(CHAT_SESSION[receiver],'wants to talk to',CHAT_SESSION[USER_NAMES[client_address[0]]])

                    else:
                        #If non of above apply, the user is probably
                        #sending a message to another user
                        # sender = USER_NAMES[client_address[0]]
                        if USER_NAMES[client_address[0]] in CHAT_SESSION:
                            # receiver = CHAT_SESSION[USER_NAMES[client_address[0]]]
                            # receiver_socket = USER_SOCKETS[receiver]
                            if not message_queues.get(USER_SOCKETS[CHAT_SESSION[USER_NAMES[client_address[0]]]]):
                                message_queues[USER_SOCKETS[CHAT_SESSION[USER_NAMES[client_address[0]]]]] = queue.Queue()
                            message_queues[USER_SOCKETS[receiver]].put(USER_NAMES[client_address[0]] + ": " + data)
                            message_queues[sock].put('sent')
                        else:
                            message_queues[sock].put(data)

                    #Add output channel for response
                    if sock not in outputs:
                        outputs.append(sock)
                else:
                    #If there's no data in sock.recv, it means the
                    #socket to the client is closed
                    if sock in outputs:
                        outputs.remove(sock)
                    inputs.remove(sock)
                    sock.close()

                    #Remove message from queue
                    del message_queues[sock]

        #use helper functions to write to sockets and handle exceptions
        write_to_socket(write_to, outputs, message_queues)

        handle_socket_exceptions(exceptions, inputs, outputs, message_queues)


def write_to_socket(write_to, outputs, message_queues):
    """
        write_to: tuple of socket objects to write to (subset of outputs)
        outputs: list of sockets that we expect to write to (not necessarily all sockets)
        message_queues: queue of message of each sockets that need to be sent
        given above paramets, write to each socket from write_to tuple
    """
    for sock in write_to:
        try:
            next_msg = message_queues[sock].get_nowait()
        except queue.Empty:
            #No message is waiting in the queue for this socket
            #So remove the socket from outputs
            outputs.remove(sock)
        else:
            sock.send(next_msg.encode('utf-8'))


def handle_socket_exceptions(exceptions, inputs, outputs, message_queues):
    """exceptions: tuples of sucket objects that threw exceptions
       inputs: list of sockets that we expect to read from
       outputs: list of sockets that we expect to write to
       message_queues: messages of sockets associated with the sockets
                       in exception.
       Handle all the excpetions"""
    for sock in exceptions:
        print("Exceptions from ", sock.getpeername())
        #Remove the faulty socket from inputs and outputs list
        #and close the client_socket
        inputs.remove(sock)
        if sock in outputs:
            outputs.remove(sock)
        sock.close()

        #Delete the message
        del message_queues[sock]



if __name__ == '__main__':
    listen()
