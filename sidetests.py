# # import consts
# # import socket
# #
# # def get_ipv4_address():
# #     hostname = socket.gethostname()
# #     real_server_ip = socket.gethostbyname(hostname)
# #     return real_server_ip
# #
# # # Example usage
# # if __name__ == "__main__":
# #     ip_address = get_ipv4_address()
# #     print(f"Your IPv4 address is: {ip_address}")
# #
#
#
# import socket
#
# def get_ipv4_address():
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
#             s.connect(("8.8.8.8", 80))
#             return s.getsockname()[0]
#     except Exception as e:
#         print(f"Error occurred: {e}")
#         return None
#
# if __name__ == "__main__":
#     ip_address = get_ipv4_address()
#     print(f"Your network-facing IPv4 address is: {ip_address}")
