import socket
import struct
import threading
import time
from consts import*
from termcolor import colored


class Client:
    def __init__(self, udp_port=UDP_OFFER_PORT, tcp_port=TCP_PORT):
        self.magic_cookie = MAGIC_COOKIE # get cookie from consts
        self.offer_message_type = OFFER_MESSAGE_TYPE # get offer type from consts
        self.request_message_type = REQUEST_MESSAGE_TYPE # get request type from consts
        self.payload_message_type = PAYLOAD_MESSAGE_TYPE # get payload from consts
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.file_size = 0
        self.tcp_connections = 0
        self.udp_connections = 0

    def get_user_input(self):
        # Get user inputs
        self.file_size = int(input(colored("Enter the file size (in bits): ","green")))
        self.tcp_connections = int(input(colored("Enter the number of TCP connections: ",'green')))
        self.udp_connections = int(input(colored("Enter the number of UDP connections: ","green")))

    # offer listener
    def offer_listener(self):
        print(colored("Client started, listening for offer requests...", "green"))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # init a UDP packet socket
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.bind(("", self.udp_port))

        print(colored(f"Client is listening on UDP port {self.udp_port}","cyan"))

        while True:
            data, addr = client_socket.recvfrom(1024)
            print(f"Received data from {addr} {data}")
            print(colored(f"Received offer from {addr}","green"))

            # Unpack the received message
            if len(data) >= 9:
                magic_cookie, message_type, udp_port, tcp_port = struct.unpack('!IBHH', data[:9])

                if magic_cookie != self.magic_cookie:
                    print(colored(f"Invalid magic cookie from {addr}", "red"))
                    return

                if message_type != self.offer_message_type:
                    print(colored(f"Invalid message type from {addr}, Not offer message", "red"))
                    return

                # if statement is a bit redundant, but it worked first so I don't want the change it
                if self.magic_cookie == magic_cookie and message_type == self.offer_message_type:
                    # get IP and ports from socket to send to the requests function
                    server_ip_address = addr[0]
                    server_tcp_port = tcp_port
                    server_udp_port = udp_port
                    self.start_requests(server_ip_address, server_tcp_port, server_udp_port)

    def start_requests(self, server_ip_address, server_tcp_port, server_udp_port):
        print(colored("Client started, listening for offer requests...","green"))
        threads = []
        # Create threads for TCP connections
        for i in range(self.tcp_connections): # init a thread for each TCP connection
            thread = threading.Thread(target=self.receive_file_over_tcp, args=(i,server_ip_address, server_tcp_port))
            threads.append(thread)
            thread.start()

        # Create threads for UDP connections
        for i in range(self.udp_connections): # init a thread for each UDP connection
            thread = threading.Thread(target=self.receive_file_over_udp, args=(i,server_ip_address, server_udp_port))
            threads.append(thread)
            thread.start()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()
        print(colored("All transfers complete, listening to offer requests","green"))

    def receive_file_over_tcp(self, conn_num,host='localhost', port=4500, ):

        request_message = struct.pack('!IBQ', self.magic_cookie, self.request_message_type, self.file_size)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_client_socket:
            tcp_client_socket.connect((host, port))
            tcp_client_socket.sendall(request_message) # send request message
            print("Sent request message over TCP")

            header_size = struct.calcsize('!IB1024s')  # Size of the header of payload packet

            file_size = self.file_size
            print(f"Receiving file of size: {file_size} bytes") # Print for testing
            start_time = time.time()

            with open('received_file_tcp.txt', 'wb') as f:
                total_received = 0
                while total_received < file_size: # while we are still receiving the file
                    header = b"" # init header
                    while len(header) < header_size:
                        chunk = tcp_client_socket.recv(header_size - len(header)) # receive just the data chunk.
                        if not chunk: # if datac
                            print("Connection closed unexpectedly.")
                            return
                        header += chunk
                    # header = tcp_client_socket.recv(header_size)
                    # if file_size - total_received < 1024: # if we are not in the last packet
                    #     if len(header) < header_size:
                    #         print(colored("Error: Incomplete header received. Terminating connection.","red"))
                    #         break

                    try:
                        magic_cookie, message_type, data_chunk = struct.unpack('!IB1024s', header)
                        data_chunk = data_chunk.decode('utf-8').rstrip('\x00') # return data to bytes if something was wrong in the way
                    except struct.error:
                        print(colored("Error unpacking header: {e}","red"))
                        break
                    # if not data_chunk:
                    #     break

                    # header = data_chunk[:header_size]
                    # magic_cookie, message_type = struct.unpack('!IB', header)

                    if magic_cookie != self.magic_cookie: # validate cookie
                        print(f"my cookie: {self.magic_cookie}")
                        print(f"magic cookie: {magic_cookie}")
                        print("Invalid cookie received. Terminating connection.")
                        break

                    if message_type != self.payload_message_type: # validate message type
                        print("Invalid message received. Terminating connection.")
                        break

                    payload = data_chunk.encode('utf-8') #encode datachunk to string
                    f.write(payload) # write data to file, this slows downs the speedtest, but because chunk size is only 1024, writing is quiet fast
                    total_received += len(payload)

            end_time = time.time()
            total_time = end_time - start_time
            print(colored(
                f"TCP transfer #{conn_num + 1} finished, total time: {total_time} seconds, total speed:{file_size / total_time} bits/second","light_blue"))
            # print(f"File received successfully in {total_time:.2f} seconds")

    def receive_file_over_udp(self, conn_num ,host='localhost', port=4500):
        # build a request message
        request_message = struct.pack('!IBQ', self.magic_cookie, self.request_message_type, self.file_size)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_client_socket:
            # Send the request message to the server
            udp_client_socket.sendto(request_message, (host, port))
            print(f"Request sent to {host}:{port}") # print for my self need to be deleted

            total_bytes_received = 0 # init size received
            header_size = struct.calcsize('!IB1024s')  # Size of the header
            start_time = time.time()

            with open('received_file_udp.txt', 'wb') as f:
                while total_bytes_received < self.file_size:
                    udp_client_socket.settimeout(1)  # Set timeout for receiving data
                    try:
                        # Receive data from the server
                        # data, server_addr = udp_client_socket.recvfrom(1024)
                        header = udp_client_socket.recv(header_size)
                        magic_cookie, message_type, data_chunk = struct.unpack('!IB1024s', header) #unpack header
                        data_chunk = data_chunk.decode('utf-8').rstrip('\x00') # decode string by len

                        # header = data[:header_size]
                        # magic_cookie, message_type = struct.unpack('!IB', header)

                        if magic_cookie != self.magic_cookie: # validate cookie
                            print("Invalid header received. Terminating connection.")
                            break
                        if message_type != self.payload_message_type: # validate type
                            print("Invalid payload received. Terminating connection.")
                            break

                        payload = data_chunk.encode('utf-8') # encode string
                        f.write(payload)
                        total_bytes_received += len(payload)

                    except socket.timeout:
                        print(colored("No response received. Exiting.","red")) # a print for my self, maybe delete it...
                        break

            stop_time = time.time()
            total_time = stop_time - start_time
            percentage_received = total_bytes_received / self.file_size * 100

            print(colored(
                f"UDP transfer #{conn_num + 1} finished, total time: {total_time} seconds, total speed: {self.file_size / total_time} bits/second, percentage of packets received successfully: {percentage_received}%","light_magenta"))


            # print(f"File received successfully in {total_time:.2f} seconds")
            # print(f"Total bytes received: {total_bytes_received}/{self.file_size}")

    def start(self):
        self.get_user_input() # init user and get num of connections
        self.offer_listener() # start listening process


if __name__ == "__main__":
    client = Client()
    client.start()
