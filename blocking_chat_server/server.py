"""Socket programming - Server side script"""
import socket
HOST = ''
PORT = 5000
BUFSIZE = 1024
ADDR = (HOST, PORT)

def listen():
    """Listen and respond to incoming requests
       from clients"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(ADDR)
    server_socket.listen(5)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # server_socket.setblocking(0)

    while True:
        print("Server is waiting for connection")
        client_sock, addr = server_socket.accept()
        print("Connected to ", addr)

        while True:
            data = client_sock.recv(BUFSIZE).decode('utf-8')
            if not data:
                break
            if data == 'exit':
                break
            print(data)
            try:
                client_sock.send(('Message Received: %s' %data).encode('utf-8'))
            except KeyboardInterrupt:
                print("Exited by user")
        client_sock.shutdown(2)
        client_sock.close()
    server_socket.close()




if __name__ == '__main__':
    listen()
