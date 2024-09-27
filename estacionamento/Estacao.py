import asyncio

porta_gerente = 5524

class Estacao:
    def __init__(self, id_estacao, ip, porta):
        self.id_estacao = id_estacao
        self.ip = ip
        self.porta = porta
        # self.vagas_livres = []
        # self.vagas_ocupadas = {} # dicionario: id_vaga => id_carro
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
        print("Message: ", message)

        #comando, *args = message.split()  # Divide a mensagem em partes
        #print(args[0], args[1])
        print(f"Estação {self.id_estacao} recebeu comando: {message}")

        #if comando == "RV":
        if message.startswith("RV"):
            comando = message.split(".")
            writer.write(f"Chegou carro.".encode())
            await writer.drain()
            print("!!!!!!!!!",comando[1])
            #await self.requisitar_vaga(comando[1])  # Passa o parâmetro para a função - args[0] é o id do carro
            await self.enviar_mensagem(f"RV {self.id_estacao} {comando[1]}", self.ip, self.porta+10)    # Envia um "AV" pro middleware (middleware tem q atualizar o bkp no gerente)


        elif message.startswith("LV"):
            comando = message.split()
            writer.write(f"Liberou vaga.".encode())
            await writer.drain()
            await self.enviar_mensagem(f"LV {comando[1]}", self.ip, self.porta+10)    # Envia um "AV" pro middleware (middleware tem q atualizar o bkp no gerente)


        elif message.startswith("AE"):
            writer.write(f"{self.id_estacao} ativada.".encode())
            await writer.drain()
            #writer.close()
            response = await self.ativar_estacao(self.id_estacao) # passando id da estação

        elif message.startswith("FE"):
            response = await self.finalizar_estacao()

        elif message.startswith("VD"):
            print("entrou no VD")
            # Identifica a estação (ex: Station1, Station2 etc)
            station_id = self.id_estacao.replace("Station", "")
            # Armazena o writer associado ao ID da estação
            #self.writers[station_id] = writer
            print("station id e writer: ", station_id)
            # Agora processa a requisição de vagas disponíveis
            response = await self.vagas_disponiveis(self.ip, self.porta, station_id)

        elif message.startswith("vd_response"):
            # Extrai o ID da estação (ou outra identificação)
            lista_estacoes = message.split(".")  # Supondo que o ID da estação está na mensagem
            print(" lista estacoes ", lista_estacoes[1])
            await self.enviar_mensagem(f"vd_response.{lista_estacoes[1]}", self.ip, 5554)  # Envia a resposta para o middleware
            # Recupera o writer associado a essa estação
            # writer = self.writers.get(station_id)
            # if writer:
            #     # Monta a resposta
            #     response = "Sua resposta formatada aqui"
            #     writer.write(response.encode('utf-8'))
            #     await writer.drain()
            # else:
            #     print(f"Nenhum writer encontrado para a estação {station_id}")

        else:
            response = "Comando inválido."

        # writer.write(response.encode('utf-8'))
        # await writer.drain()
        # writer.close()


    async def ativar_estacao(self, id_estacao):
        self.ativo = True
        response = await self.enviar_mensagem(f"AE {id_estacao}", self.ip, self.porta+10)    # Envia um "AE" pro middleware
        return response
    

    async def vagas_disponiveis(self, ip, porta, id_estacao):
        # fazer isso para todas as estações ativas
        #enviar pro middleware que envia pro gerente que contem o bkacup
        await self.enviar_mensagem(f"VD.{id_estacao}", ip, porta+10)
        #await self.enviar_mensagem(f"{self.id_estacao}:{len(self.vagas_livres)}-{len(self.vagas_ocupadas)}", self.ip, self.porta) 


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


    async def finalizar_estacao(self):
        self.ativo = False
        return f"Estação {self.id_estacao} finalizada."




    # interperetar os comandos aqui, 
    # só atualizar o bkp (manager)
    # no AE o vagas_livres