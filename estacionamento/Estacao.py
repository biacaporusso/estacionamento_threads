import asyncio

porta_gerente = 5523

class Estacao:
    def __init__(self, id_estacao, ip, porta):
        self.id_estacao = id_estacao
        self.ip = ip
        self.porta = porta
        self.ativo = False  # Estação começa inativa
        self.server_socket = None  # Referência ao socket da estação        implementar dicionario
        writers = {}  # Dicionário de writers associados a cada estação


    async def iniciar_socket_estacao(self):
        # Inicializa o socket usando asyncio para comunicação assíncrona
        self.server_socket = await asyncio.start_server(self.processar_comando, self.ip, self.porta)
        print(f"Estação {self.id_estacao} está escutando em {self.ip}:{self.porta}")
        async with self.server_socket:
            await self.server_socket.serve_forever()


    async def processar_comando(self, reader, writer):
        data = await reader.read(1000)
        message = data.decode('utf-8')
        print(f"\nEstação {self.id_estacao} recebeu comando: {message}")

        if message.startswith("RV"):
            comando = message.split(".")
            writer.write(f"Chegou carro.".encode())
            await writer.drain()
            await self.enviar_mensagem(f"RV {self.id_estacao} {comando[1]}", self.ip, self.porta+10)    # Envia um "AV" pro middleware (middleware tem q atualizar o bkp no gerente)

        elif message.startswith("LV"):
            comando = message.split(".")
            writer.write(f"Liberou vaga.".encode())
            await writer.drain()
            await self.enviar_mensagem(f"LV {comando[1]}", self.ip, self.porta+10)    # Envia um "AV" pro middleware (middleware tem q atualizar o bkp no gerente)

        elif message.startswith("AE"):
            writer.write(f"{self.id_estacao} ativada.".encode())
            await writer.drain()
            self.ativo = True
            await self.enviar_mensagem(f"AE {self.id_estacao}", self.ip, self.porta+10) 

        elif message.startswith("FE"):
            self.ativo = False
            writer.write(f"{self.id_estacao} desativada.".encode())
            await writer.drain()
            await self.enviar_mensagem(f"FE {self.id_estacao}", self.ip, self.porta+10)

        elif message.startswith("VD"):
            writer.write(f"Mostrou vagas disponíveis.".encode())
            await writer.drain()
            station_id = self.id_estacao.replace("Station", "")
            await self.enviar_mensagem(f"VD.{station_id}", self.ip, self.porta+10)

        elif message.startswith("vd_response"):
            # Extrai o ID da estação (ou outra identificação)
            lista_estacoes = message.split(".")  # Supondo que o ID da estação está na mensagem
            print(" lista estacoes ", lista_estacoes[1])
            await self.enviar_mensagem(f"vd_response.{lista_estacoes[1]}", self.ip, 5554)  # Envia a resposta para o middleware

        else:
            print("Comando inválido.")


    # Função para enviar mensagens ao middleware
    async def enviar_mensagem(self, mensagem, ip, porta):
        try:
            reader, writer = await asyncio.open_connection(ip, porta)
            writer.write(mensagem.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Erro ao conectar ao middleware: {e}")

        # receber mensagem pelo reader:
        data = await reader.read(100) 
        return data.decode('utf-8')
