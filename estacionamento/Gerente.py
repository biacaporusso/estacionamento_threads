import socket

class Gerente:
    def __init__(self, ip, porta):
        self.ip = ip
        self.porta = porta
        self.socket_gerente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # backup