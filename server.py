import socket
import struct
import threading
import time

MAGIC_COOKIE = 0xabcddcba
OFFER_MESSAGE_TYPE = 0x2
UDP_PORT = 12345
TCP_PORT = 54321

def udp_server():
    """
    Starts a UDP server that broadcasts offer messages to clients at regular intervals.

    The offer message contains a magic cookie, message type, UDP port, and TCP port, which
    clients can use to connect to the server for further communication.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting
    server_socket.bind(("", UDP_PORT))  # Bind to the specified UDP port

    print(f"Server is listening on UDP port {UDP_PORT}")

    def broadcast_offer_message():
        while True:
            # Create the offer message
            offer_message = struct.pack('!IBHH', MAGIC_COOKIE, OFFER_MESSAGE_TYPE, UDP_PORT, TCP_PORT)

            # Broadcast the offer message every second
            server_socket.sendto(offer_message, ('<broadcast>', UDP_PORT))
            print("Sent offer message")
            time.sleep(1)

def send_large_data(conn, data_chunk):
    """
    Sends a large amount of data to the client over a TCP connection.

    Args:
        conn (socket): The TCP connection object.
        data_chunk (str): A chunk of data to send repeatedly.

    Notes:
        The total size of the data sent is 1 GB, and the data is sent in chunks.
    """
    total_size = 1 * 1024 * 1024 * 1024  # Total size: 1 GB
    bytes_sent = 0
    chunk_size = len(data_chunk)

    while bytes_sent < total_size:
        if bytes_sent + chunk_size > total_size:
            # Adjust the final chunk size to not exceed the total size
            data_chunk = data_chunk[:total_size - bytes_sent]

        conn.sendall(data_chunk.encode('utf-8'))  # Send the data chunk
        bytes_sent += len(data_chunk)

        # Optional: Break the loop if the data chunk is empty or None
        if not data_chunk:
            break

def start_server(host='localhost', port=4500):
    """
    Starts a TCP server to send large data to a connected client.

    Args:
        host (str): The hostname or IP address of the server (default is 'localhost').
        port (int): The TCP port number to listen on (default is 4500).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))  # Bind to the specified host and port
        server_socket.listen()  # Start listening for incoming connections
        print(f"Server listening on {host}:{port}")

        conn, addr = server_socket.accept()  # Accept a client connection
        data_chunk = '0' * 1024  # Example data chunk (1 KB)
        file_size = 1 * 1024 * 1024 * 1024  # Total file size (1 GB)

        with conn:
            print(f"Connected by {addr}")
            conn.sendall(str(file_size).encode())  # Send the file size to the client
            start_time = time.time()
            send_large_data(conn, data_chunk)  # Send the large data
            end_time = time.time()

            total_time = end_time - start_time
            bandwidth = file_size / total_time  # Calculate bandwidth in bytes per second

            print(f"File sent successfully in {total_time:.2f} seconds")
            print(f"Bandwidth: {bandwidth:.2f} bytes/sec")

if __name__ == "__main__":
    # Start the UDP server in a separate thread
    server_thread = threading.Thread(target=udp_server)
    server_thread.start()

    time.sleep(1)  # Allow the UDP server time to start

    # Uncomment the line below to start the TCP server
    # start_server()
