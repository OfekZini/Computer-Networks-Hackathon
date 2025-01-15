import socket
import struct
import threading
import time
from consts import*
from termcolor import colored

class Server:
    def __init__(self,server_ip = SERVER_IP, udp_offer_port=UDP_OFFER_PORT, udp_port=UDP_PORT , tcp_port = TCP_PORT):
        self.server_ip = self.get_ipv4_address()
        self.udp_port = udp_port
        self.udp_offer_port = udp_offer_port
        self.tcp_port = tcp_port
        self.magic_cookie = MAGIC_COOKIE
        self.offer_message_type = OFFER_MESSAGE_TYPE
        self.request_message_type = REQUEST_MESSAGE_TYPE
        self.payload_message_type = PAYLOAD_MESSAGE_TYPE

    def get_ipv4_address(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception as e:
            print(f"Error occurred: {e}")
            return None

    # Server code
    def udp_offers_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting
        server_socket.bind(("", self.udp_offer_port))

        print(colored(f"Server is broadcasting on UDP port {self.udp_offer_port}","light_blue"))

        while True:
            # Create the offer message
            offer_message = struct.pack('!IBHH', self.magic_cookie, self.offer_message_type, self.udp_port, self.tcp_port)

            # Send the offer message every 1 second
            server_socket.sendto(offer_message, ('<broadcast>', self.udp_offer_port))
            print("Sent offer message")
            time.sleep(broadcast_time)


    def requests_udp_listener(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((self.server_ip, self.udp_port))
        print(colored(f"Server listening to UDP on {self.server_ip}:{self.udp_port}","light_blue"))

        while True:
            data, addr = server_socket.recvfrom(13)
            print(colored(f"Received data from {addr}","light_blue"))
            client_thread = threading.Thread(target=self.handle_udp_client, args=(data, addr, server_socket))
            client_thread.start()

    def handle_udp_client(self, data, addr, server_socket):
        if len(data) < 13:
            print(colored(f"Incomplete data received from{addr}","red"))
            return

        magic_cookie, message_type, file_size = struct.unpack('!IBQ', data)

        if magic_cookie != self.magic_cookie:
            print(colored(f"Invalid magic cookie from {addr}","red"))
            return

        if message_type != self.request_message_type:
            print(colored(f"Invalid message type from {addr}","red"))
            return

        print(f"Received request from {addr}: Magic Cookie: {hex(magic_cookie)}, Message Type: {message_type}, File Size: {file_size} bytes")


        total_size = file_size
        bytes_sent = 0
        chunk_size = 1024
        total_segments = (total_size + chunk_size - 1) // chunk_size  # Ceiling division
        current_segment = 1
        data_chunk = b'0' * 1024

        while bytes_sent < total_size:
            if total_size - bytes_sent < len(data_chunk):
                data_chunk = b'0' * (total_size - bytes_sent)

            # payload_msg = struct.pack('!IB1024s', self.magic_cookie, self.payload_message_type, data_chunk)
            payload_msg = struct.pack(
                '!IBQQ1024s',  # Updated format
                self.magic_cookie,  # Magic cookie (4 bytes)
                self.payload_message_type,  # Message type (1 byte)
                total_segments,  # Total segment count (8 bytes)
                current_segment,  # Current segment count (8 bytes)
                data_chunk  # Payload (1024 bytes)
            )

            print(f"Sending chunk of size {len(data_chunk)} to {addr}")
            # server_socket.sendto(data_chunk, addr)
            server_socket.sendto(payload_msg, addr)
            bytes_sent += len(data_chunk)
            print(f"Sent {bytes_sent}/{total_size} bytes to {addr}")

    def requests_tcp_listener(self):
        request_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        request_server.bind((self.server_ip, self.tcp_port))
        request_server.listen(5)
        print(colored(f"Server listening to TCP on {self.server_ip}:{self.tcp_port}","light_blue"))

        while True:
            client_socket, addr = request_server.accept()
            print(colored("Connection from {addr} established.","light_blue"))

            # Create a new thread for each client
            client_thread = threading.Thread(target=self.handle_tcp_client, args=(client_socket,addr))
            client_thread.start()
            client_thread.join()

    def handle_tcp_client(self,client_socket , addr):
        with client_socket:
            print(colored(f"Connected by {addr}","light_blue"))

            # Receive the data in small chunks
            data = client_socket.recv(13)  # Total expected size is 13 bytes

            if len(data) < 13:
                print(colored("Incomplete data received","red"))
                return

            # Unpack the data
            magic_cookie, message_type, file_size = struct.unpack('!IBQ', data)

            # Validate magic cookie and message type
            if magic_cookie != self.magic_cookie:
                print(colored("Invalid magic cookie. Rejecting message.","red"))
                return

            if message_type != 0x3:
                print(colored("Invalid message type. Rejecting message.","red"))
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

            # payload_msg =  struct.pack('!IB',self.magic_cookie, self.payload_message_type) + data_chunk
            payload_msg = struct.pack('!IB1024s', self.magic_cookie, self.payload_message_type, data_chunk)
            conn.sendall(payload_msg)
            bytes_sent += len(data_chunk)

            # Optional: Break the loop if the string element is empty or None
            if not data_chunk:
                break

    def start(self):
        ### The Server Request Listener
        print(colored(f"Server started, listening on IP address{self.server_ip}","light_blue"))
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