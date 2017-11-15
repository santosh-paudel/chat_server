"""Socket programming - client side script """
import socket
HOST = 'localhost'
PORT = 5000
BUFSIZE = 1024
SERVER = 'localhost'

def client():
    """Connect to server. Send a message. close the connection"""
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_addr = (HOST, PORT)
    client_sock.connect(socket_addr)

    try:
        while True:
            message = input("Enter a message: ")
            #all the messages sent and received through sockets have
            #to be bytes object (not unicode string)
            client_sock.send(message.encode('utf-8'))
            if message == 'exit':
                break
            data = client_sock.recv(BUFSIZE).decode('utf-8')
            print(data)
    except KeyboardInterrupt:
        print("Exited by User")

    client_sock.shutdown(2)
    client_sock.close()


if __name__ == '__main__':
    client()
