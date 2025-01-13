import socket
import struct
import threading
import time

##MAGIC_COOKIE = 0xabcddcba
##OFFER_MESSAGE_TYPE = 0x2
##UDP_PORT = 12345
##TCP_PORT = 54321

class Client:
    def __init__(self,udp_port=12345,tcp_port = 54321):
        self.magic_cookie = 0xabcddcba
        self.offer_message_type = 0x2
        self.request_message_type = 0x3

        self.udp_port = udp_port
        self.tcp_port  = tcp_port
        self.magic_cookie = 0xabcddcba
        self.offer_message_type = 0x2

    # offer listener
    def offer_listener(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.bind(("", self.udp_port))

        print(f"Client is listening on UDP port {self.udp_port}")

        while True:
            data, addr = client_socket.recvfrom(1024)
            print(f"Received data from {addr}")

            # Unpack the received message
            if len(data) >= 9:
                magic_cookie, message_type, udp_port, tcp_port = struct.unpack('!IBHH', data[:9])

                if self.magic_cookie == self.magic_cookie and message_type == self.offer_message_type:
                    server_ip_address = addr[0]
                    server_tcp_port = tcp_port
                    server_udp_port = udp_port
                    print(f"Received an offer from the server IP address {server_ip_address}")
                    print(f"Received valid offer message: UDP Port: {server_udp_port}, TCP Port: {server_tcp_port}")

                else:
                    print("Invalid message received")
            else:
              print("Incomplete message received")


    def startup(self,server_host,server_port):
        ### send request to the server
        # Send a request message using TCP
        file_size = 1024  # Example file size in bytes
        request_message = struct.pack('!IBQ', self.magic_cookie, self.request_message_type, file_size)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_client_socket:
            tcp_client_socket.connect((server_host, server_port))
            tcp_client_socket.sendall(request_message)
            print("Sent request message over TCP")

    def receive_file_over_tcp(self, host='localhost', port=4500):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))
            print(f"Connected to server {host}:{port}")

            file_size = int(client_socket.recv(1024).decode())
            print(f"Receiving file of size: {file_size} bytes")
            start_time = time.time()

            with open('received_file', 'wb') as f:
                total_received = 0
                while total_received < file_size:
                    data = client_socket.recv(500)
                    if not data:
                        break
                    f.write(data)
                    total_received += len(data)

            end_time = time.time()
            total_time = end_time - start_time

            print(f"File received successfully in {total_time:.2f} seconds")


if __name__ == "__main__":
    client = Client()
    offer_thread = threading.Thread(target=client.offer_listener())
    offer_thread.start()
    time.sleep(1)
    offer_thread.join()
  ###  receive_file()