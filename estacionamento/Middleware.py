import socket

class Middleware:
    def __init__(self, ip, porta):
        self.ip = ip
        self.porta = porta
        self.socket_mw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# implementar conexoes com o gerente (atualizar bkp)
# implementar conexoes com outros middlewares (buscar vaga)