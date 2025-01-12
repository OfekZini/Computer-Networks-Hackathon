import socket
import struct
import threading
import time

MAGIC_COOKIE = 0xabcddcba
OFFER_MESSAGE_TYPE = 0x2
UDP_PORT = 12345
TCP_PORT = 54321


# Server code
def udp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting
    server_socket.bind(("", UDP_PORT))

    print(f"Server is listening on UDP port {UDP_PORT}")

    while True:
        # Create the offer message
        offer_message = struct.pack('!IBHH', MAGIC_COOKIE, OFFER_MESSAGE_TYPE, UDP_PORT, TCP_PORT)

        # Send the offer message every 1 second
        server_socket.sendto(offer_message, ('<broadcast>', UDP_PORT))
        print("Sent offer message")
        time.sleep(1)



# Run server and client on different threads
server_thread = threading.Thread(target=udp_server)





def send_large_data(conn, data_chunk):
    total_size = 1 * 1024 * 1024 * 1024  # 1 GB
    bytes_sent = 0
    chunk_size = len(data_chunk)

    while bytes_sent < total_size:
        if bytes_sent + chunk_size > total_size:
            # Adjust the final chunk to not exceed the 1 GB limit
            data_chunk = data_chunk[:total_size - bytes_sent]

        conn.sendall(data_chunk.encode('utf-8'))
        bytes_sent += len(data_chunk)

        # Optional: Break the loop if the string element is empty or None
        if not data_chunk:
            break

def start_server(host='localhost', port=4500):

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Server listening on {host}:{port}")

        conn, addr = server_socket.accept()
        data_chunk = '0'*1024
        file_size =  1 * 1024 * 1024 * 1024
        with conn:
            print(f"Connected by {addr}")
            conn.sendall(str(file_size).encode())  # Send the file size
            start_time = time.time()
            send_large_data(conn, data_chunk)
            end_time = time.time()
            total_time = end_time - start_time
            bandwidth = file_size / total_time  # in bytes per second

            print(f"File sent successfully in {total_time:.2f} seconds")
            print(f"Bandwidth: {bandwidth:.2f} bytes/sec")


if __name__ == "__main__":


    server_thread = threading.Thread(target=udp_server)
    server_thread.start()
    time.sleep(1)  # Give the server time to start
    server_thread.join()


   ### start_server()