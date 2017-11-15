"""Socket programming - Server side script"""
import queue
import select
import socket
HOST = ''
PORT = 5000
BUFSIZE = 1024
ADDR = (HOST, PORT)

def listen():
    """Use non blocking sockets to check for client_sockets
    """

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setblocking(0)

    #Bind the socket to ADDR (specified above)
    server_socket.bind(ADDR)
    server_socket.listen(5)
    # server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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
        read_from, write_from, exceptions = select.select(inputs, outputs, inputs)

        for sock in read_from:
            if sock is server_socket:
                client_socket, client_address = sock.accept()
                print("Connected to %s", client_address)
                client_socket.setblocking(0)
                inputs.append(client_socket)
                message_queues[client_socket] = queue.Queue()
            else:
                data = sock.recv(BUFSIZE).decode('utf-8')
                if data:
                    #A read_from client socket has data
                    print("Data received from %s: %s" %(sock.getpeername(), data))
                    message_queues[sock].put(data)

                    #Add output channel for response
                    if sock not in outputs:
                        outputs.append(sock)
                else:
                    #Entry result means closed client_sockets
                    if sock in outputs:
                        outputs.remove(sock)
                    inputs.remove(sock)
                    sock.close()

                    #Remove message from queue
                    del message_queues[sock]

        #send message to all output sockets
        for sock in write_from:
            try:
                next_msg = message_queues[sock].get_nowait()
            except queue.Empty:
                #No message is waiting in the queue for this socket
                #So remove the socket from outputs
                outputs.remove(sock)
            else:
                sock.send(next_msg.encode('utf-8'))

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
