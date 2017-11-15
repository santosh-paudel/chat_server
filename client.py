"""Socket programming - client side script """
import socket
HOST = '172.17.139.164'
PORT = 5000
BUFSIZE = 1024

def client():
    """Connect to server. Send a message. close the connection"""
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_addr = (HOST, PORT)
    client_sock.connect(socket_addr)

    try:
        while True:
            message = input("Message: ")
            #all the messages sent and received through sockets have
            #to be bytes object (not unicode string)
            client_sock.send(message.encode('utf-8'))
            if message == 'logout':
                raise KeyboardInterrupt
            response = client_sock.recv(BUFSIZE).decode('utf-8')

            #if the message is online
            #display the response in specific format
            if message == 'online':
                user_list = response.split(',')
                for user in user_list:
                    print(user)

            else:
                print(response)
    except KeyboardInterrupt:
        print("Exited by User")

    client_sock.shutdown(2)
    client_sock.close()


if __name__ == '__main__':
    client()