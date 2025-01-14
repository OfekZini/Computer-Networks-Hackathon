import socket
import struct
import threading
import time


class Client:
    def __init__(self, udp_port=12345, tcp_port=82):
        self.magic_cookie = 0xabcddcba
        self.offer_message_type = 0x2
        self.request_message_type = 0x3
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.magic_cookie = 0xabcddcba
        self.file_size = 0
        self.tcp_connections = 0
        self.udp_connections = 0

    def get_user_input(self):
        # Get user inputs
        self.file_size = int(input("Enter the file size (in MB): "))
        self.tcp_connections = int(input("Enter the number of TCP connections: "))
        self.udp_connections = int(input("Enter the number of UDP connections: "))

    # offer listener
    def offer_listener(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.bind(("", self.udp_port))

        print(f"Client is listening on UDP port {self.udp_port}")

        while True:
            data, addr = client_socket.recvfrom(1024)
            print(f"Received data from {addr} {data}")

            # Unpack the received message
            if len(data) >= 9:
                magic_cookie, message_type, udp_port, tcp_port = struct.unpack('!IBHH', data[:9])

                if self.magic_cookie == magic_cookie and message_type == self.offer_message_type:
                    server_ip_address = addr[0]
                    server_tcp_port = tcp_port
                    server_udp_port = udp_port
                    print(f"Received an offer from the server IP address {server_ip_address}")
                    print(f"Received valid offer message: UDP Port: {server_udp_port}, TCP Port: {server_tcp_port}")
                    self.start_requests(server_ip_address, server_tcp_port, server_udp_port)
                else:
                    print("Invalid message received")
            else:
                print("Incomplete message received")

    def start_requests(self, server_ip_address, server_tcp_port, server_udp_port):
        threads = []
        # Create threads for TCP connections
        for i in range(self.tcp_connections):
            thread = threading.Thread(target=self.receive_file_over_tcp, args=(server_ip_address, server_tcp_port))
            threads.append(thread)
            thread.start()

        # Create threads for UDP connections
        for i in range(self.udp_connections):
            thread = threading.Thread(target=self.receive_file_over_udp, args=(server_ip_address, server_udp_port))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

    def receive_file_over_tcp(self, host='localhost', port=4500):

       ### request_file_size = self.file_size + '\n'
        request_message = struct.pack('!IBQ', self.magic_cookie, self.request_message_type, self.file_size)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_client_socket:
            tcp_client_socket.connect((host, port))
          ###  tcp_client_socket.sendall(request_file_size)

            tcp_client_socket.sendall(request_message)
            print("Sent request message over TCP")

            # file_size = int(tcp_client_socket.recv(1024).decode())
            file_size = self.file_size
            print(f"Receiving file of size: {file_size} bytes")
            start_time = time.time()

            with open('received_file', 'wb') as f:
                total_received = 0
                while total_received < file_size:
                    # print("receiving file chunk")
                    data = tcp_client_socket.recv(1024)
                    if not data:
                        break
                    f.write(data)
                    total_received += len(data)

            end_time = time.time()
            total_time = end_time - start_time

            print(f"File received successfully in {total_time:.2f} seconds")

    def receive_file_over_udp(self, host='localhost', port=4500):
        request_message = struct.pack('!IBQ', self.magic_cookie, self.request_message_type, self.file_size)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_client_socket:
            # Send the request message to the server
            udp_client_socket.sendto(request_message, (host, port))
            print(f"Request sent to {host}:{port}")

            total_bytes_received = 0
            start_time = time.time()

            while total_bytes_received < self.file_size:
                udp_client_socket.settimeout(1)  # Set timeout for receiving data
                try:
                    # Receive data from the server
                    data, server_addr = udp_client_socket.recvfrom(1024)
                    total_bytes_received += len(data)
                except socket.timeout:
                    print("No response received. Exiting.")
                    break

            stop_time = time.time()
            total_time = stop_time - start_time

            print(f"File received successfully in {total_time:.2f} seconds")
            print(f"Total bytes received: {total_bytes_received}/{self.file_size}")

        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_client_socket:
        #     tcp_client_socket.connect((host, port))
        #     tcp_client_socket.sendall(request_message)
        #     print("Sent request message over TCP")

    def start(self):
        self.get_user_input()
        self.offer_listener()


if __name__ == "__main__":
    client = Client()
    client.start()
