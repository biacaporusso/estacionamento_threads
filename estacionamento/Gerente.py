import asyncio
import socket

class Gerente:
    def __init__(self, ip, porta):
        self.ip = ip
        self.porta = porta
        self.backup_estacoes = {}
        for id in range(1, 11):
            self.backup_estacoes[id] = {
                "id_vagas_livres": [],
                "id_vagas_ocupadas": [],
                "id_vaga_ocupada_carro": [],
                "estacao_ativa": False
                # "porta_middleware": None,
                # "ultimo_ping": None
            }


    async def iniciar_socket(self):
        server = await asyncio.start_server(self.processar_mensagem, self.ip, self.porta)
        print(f"Gerente iniciado em {self.ip}:{self.porta}")

        async with server:
            await server.serve_forever()

    async def processar_mensagem(self, reader, writer):
        data = await reader.read(100)
        message = data.decode('utf-8')
        comando, *args = message.split()
        comando = args[0]
        id_estacao = args[1]
        id_vaga = args[2]
        id_carro = args[3]
        print(f"Gerente recebeu: {message}")

        # Processa mensagens para atualizar o backup
        if comando == "AV":
            self.atualizar_backup(id_estacao, id_vaga, id_carro)  # atualizar quantidade de vagas livres (vagas livres - 1)

        writer.close()

    async def atualizar_backup(self, id_estacao, id_vaga, id_carro):
        self.backup_estacoes[id_estacao]["id_vagas_livres"].remove(id_vaga)
        self.backup_estacoes[id_estacao]["id_vagas_ocupadas"].append(id_vaga)
        self.backup_estacoes[id_estacao]["id_vaga_ocupada_carro"].append(id_carro)

        
