import socket
import struct
import threading
import time

class Client:
    """
    A simple Client class to handle communication with a server using UDP for offers and TCP for file transfer.

    Attributes:
        udp_port (int): The UDP port on which the client listens for server offers.
        tcp_port (int): The TCP port used for file transfer.
        magic_cookie (int): A unique identifier used to validate messages from the server.
        offer_message_type (int): The type identifier for offer messages.
        request_message_type (int): The type identifier for request messages.
    """

    def __init__(self, udp_port=12345, tcp_port=54321):
        self.magic_cookie = 0xabcddcba  # Unique identifier for message validation
        self.offer_message_type = 0x2  # Message type for server offers
        self.request_message_type = 0x3  # Message type for file requests
        self.udp_port = udp_port  # UDP port for receiving offers
        self.tcp_port = tcp_port  # TCP port for sending requests and receiving files

    def offer_listener(self):
        """
        Listens for server broadcast offers over UDP and validates the received messages.
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting
        client_socket.bind(("", self.udp_port))  # Bind to the specified UDP port

        print(f"Client is listening on UDP port {self.udp_port}")

        while True:
            data, addr = client_socket.recvfrom(1024)  # Receive data from the server
            print(f"Received data from {addr}")

            # Unpack and validate the received message
            if len(data) >= 9:  # Ensure the message is of the expected length
                magic_cookie, message_type, udp_port, tcp_port = struct.unpack('!IBHH', data[:9])

                if magic_cookie == self.magic_cookie and message_type == self.offer_message_type:
                    server_ip_address = addr[0]
                    print(f"Received an offer from the server IP address {server_ip_address}")
                    print(f"Received valid offer message: UDP Port: {udp_port}, TCP Port: {tcp_port}")

                else:
                    print("Invalid message received")
            else:
                print("Incomplete message received")

    def startup(self, server_host, server_port):
        """
        Sends a request message to the server over TCP to initiate file transfer.

        Args:
            server_host (str): The server's hostname or IP address.
            server_port (int): The server's TCP port number.
        """
        file_size = 1024  # Example file size in bytes (this would usually be dynamic or predefined)
        request_message = struct.pack('!IBQ', self.magic_cookie, self.request_message_type, file_size)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_client_socket:
            tcp_client_socket.connect((server_host, server_port))  # Connect to the server
            tcp_client_socket.sendall(request_message)  # Send the request message
            print("Sent request message over TCP")

    def receive_file_over_tcp(self, host='localhost', port=4500):
        """
        Connects to the server over TCP to receive a file.

        Args:
            host (str): The server's hostname or IP address (default is 'localhost').
            port (int): The server's TCP port number (default is 4500).
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((host, port))  # Connect to the server
            print(f"Connected to server {host}:{port}")

            file_size = int(client_socket.recv(1024).decode())  # Receive the file size
            print(f"Receiving file of size: {file_size} bytes")
            start_time = time.time()

            with open('received_file', 'wb') as f:  # Open a file to save the received data
                total_received = 0
                while total_received < file_size:
                    data = client_socket.recv(500)  # Receive chunks of data
                    if not data:
                        break
                    f.write(data)  # Write the data to the file
                    total_received += len(data)

            end_time = time.time()
            total_time = end_time - start_time

            print(f"File received successfully in {total_time:.2f} seconds")

if __name__ == "__main__":
    client = Client()

    # Start the offer listener in a separate thread
    offer_thread = threading.Thread(target=client.offer_listener)
    offer_thread.start()

    time.sleep(1)  # Give the listener some time to start

    # Example usage (update with the actual server host and ports)
    # client.startup("server_host", server_port)
    # client.receive_file_over_tcp("server_host", server_port)

    offer_thread.join()
