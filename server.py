import socket
import struct
import threading
import time

class Server:
    def __init__(self,server_ip = '0.0.0.0', udp_offer_port=12345, udp_port=4444 , tcp_port = 54321):
        self.server_ip = server_ip
        self.udp_port = udp_port
        self.udp_offer_port = udp_offer_port
        self.tcp_port = tcp_port
        self.magic_cookie = 0xabcddcba
        self.offer_message_type = 0x2
        self.request_message_type = 0x3


    # Server code
    def udp_offers_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting
        server_socket.bind(("", self.udp_offer_port))

        print(f"Server is listening on UDP port {self.udp_port}")

        while True:
            # Create the offer message
            offer_message = struct.pack('!IBHH', self.magic_cookie, self.offer_message_type, self.udp_port, self.tcp_port)

            # Send the offer message every 1 second
            server_socket.sendto(offer_message, ('<broadcast>', self.udp_offer_port))
            print("Sent offer message")
            time.sleep(3)


    def requests_udp_listener(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.server_ip, self.udp_port))
        print(f"Server listening to UDP on {self.server_ip}:{self.udp_port}")

        while True:
            data, addr = server_socket.recvfrom(13)
            print(f"Received data from {addr}")
            client_thread = threading.Thread(target=self.handle_udp_client, args=(data, addr, server_socket))
            client_thread.start()

    def handle_udp_client(self, data, addr, server_socket):
        if len(data) < 13:
            print("Incomplete data received from", addr)
            return

        magic_cookie, message_type, file_size = struct.unpack('!IBQ', data)

        if magic_cookie != self.magic_cookie:
            print("Invalid magic cookie from", addr)
            return

        if message_type != self.request_message_type:
            print("Invalid message type from", addr)
            return

        print(f"Received request from {addr}: Magic Cookie: {hex(magic_cookie)}, Message Type: {message_type}, File Size: {file_size} bytes")

        total_size = file_size
        bytes_sent = 0
        data_chunk = b'0' * 1024

        while bytes_sent < total_size:
            if total_size - bytes_sent < len(data_chunk):
                data_chunk = b'0' * (total_size - bytes_sent)


            print(f"Sending chunk of size {len(data_chunk)} to {addr}")
            server_socket.sendto(data_chunk, addr)
            bytes_sent += len(data_chunk)
            print(f"Sent {bytes_sent}/{total_size} bytes to {addr}")

    def requests_tcp_listener(self):
        request_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        request_server.bind((self.server_ip, self.tcp_port))
        request_server.listen(5)
        print(f"Server listening to TCP on {self.server_ip}:{self.tcp_port}")

        while True:
            client_socket, addr = request_server.accept()
            print(f"Connection from {addr} established.")

            # Create a new thread for each client
            client_thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket,addr))
            client_thread.start()
            client_thread.join()

    def handle_tcp_client(self,client_socket , addr):
        with client_socket:
            print(f"Connected by {addr}")

            # Receive the data in small chunks
            data = client_socket.recv(13)  # Total expected size is 13 bytes

            if len(data) < 13:
                print("Incomplete data received")
                return

            # Unpack the data
            magic_cookie, message_type, file_size = struct.unpack('!IBQ', data)

            # Validate magic cookie and message type
            if magic_cookie != 0xabcddcba:
                print("Invalid magic cookie. Rejecting message.")
                return

            if message_type != 0x3:
                print("Invalid message type. Rejecting message.")
                return

            print(
                f"Received request: Magic Cookie: {hex(magic_cookie)}, Message Type: {message_type}, File Size: {file_size} bytes")
            self.send_large_data_over_tcp(conn=client_socket , file_size=file_size)


    def send_large_data_over_tcp(self, conn, file_size):
        total_size =  file_size
        bytes_sent = 0
        data_chunk = b'0' * 1024
        chunk_size = len(data_chunk)

        # start_time = time.time()
        while bytes_sent < total_size:
            if total_size - bytes_sent < chunk_size :
                # Adjust the final chunk to not exceed the 1 GB limit
                data_chunk = b'0' * (total_size - bytes_sent)

            conn.sendall(data_chunk)
            print(f"sent data chunk {bytes_sent}")
            bytes_sent += len(data_chunk)

            # Optional: Break the loop if the string element is empty or None
            if not data_chunk:
                break

        def handle_udp_client(self, client_socket, addr):
            with client_socket:
                print(f"Connected by {addr}")

                # Receive the data in small chunks
                data = client_socket.recv(13)  # Total expected size is 13 bytes

                if len(data) < 13:
                    print("Incomplete data received")
                    return

                # Unpack the data
                magic_cookie, message_type, file_size = struct.unpack('!IBQ', data)

                # Validate magic cookie and message type
                if magic_cookie != 0xabcddcba:
                    print("Invalid magic cookie. Rejecting message.")
                    return

                if message_type != 0x3:
                    print("Invalid message type. Rejecting message.")
                    return

                print(
                    f"Received request: Magic Cookie: {hex(magic_cookie)}, Message Type: {message_type}, File Size: {file_size} bytes")
                self.send_large_data_over_tcp(conn=client_socket, file_size=file_size)


    def start(self):
        ### The Server Request Listener
        tcp_request_server_thread = threading.Thread(target=self.requests_tcp_listener)
        tcp_request_server_thread.start()
        time.sleep(1)  # Give the server time to start

        udp_request_server_thread = threading.Thread(target=self.requests_udp_listener)
        udp_request_server_thread.start()
        time.sleep(1)  # Give the server time to start

        # The Offers publisher
        offer_server_thread = threading.Thread(target=self.udp_offers_server)
        offer_server_thread.start()
        time.sleep(1)  # Give the server time to start

        tcp_request_server_thread.join()
        udp_request_server_thread.join()
        offer_server_thread.join()


if __name__ == "__main__":
    server = Server()
    server.start()