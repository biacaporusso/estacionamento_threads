import asyncio

porta_gerente = 5524

class Estacao:
    def __init__(self, id_estacao, ip, porta):
        self.id_estacao = id_estacao
        self.ip = ip
        self.porta = porta
        self.vagas_livres = []
        self.vagas_ocupadas = {} # dicionario: id_vaga => id_carro
        self.ativo = False  # Estação começa inativa
        self.server_socket = None  # Referência ao socket da estação        implementar dicionario

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
            response = await self.requisitar_vaga(comando[1])  # Passa o parâmetro para a função - args[0] é o id do carro
        elif message.startswith("LV"):
            writer.write(f"Liberou vaga.".encode())
            await writer.drain()
            response = await self.liberar_vaga()

        elif message.startswith("AE"):
            writer.write(f"{self.id_estacao} ativada.".encode())
            await writer.drain()
            #writer.close()
            response = await self.ativar_estacao(self.id_estacao) # passando id da estação
            print("resposta: ", response)

        elif message.startswith("FE"):
            response = await self.finalizar_estacao()

        elif message.startswith("VD"):
            response = await self.vagas_disponiveis(self.ip, self.porta)

        elif message.startswith("ativada"):
            print("===== entrou ativada estacao")
            vagas_livres = message.split(".")
            vagas_livres = vagas_livres[1].replace("[", "").replace("]", "").split(",")
            print(" @@@@@@ vagas livres: ", vagas_livres)
            self.vagas_livres = vagas_livres

        elif message.startswith("ocupada"):
            print("carro ocupou vaga")
        else:
            response = "Comando inválido."

        # writer.write(response.encode('utf-8'))
        # await writer.drain()
        # writer.close()


    async def ativar_estacao(self, id_estacao):
        self.ativo = True
        response = await self.enviar_mensagem(f"AE {id_estacao}", self.ip, self.porta+10)    # Envia um "AE" pro middleware
        # await self.enviar_mensagem(f"Estação {id_estacao} ativada", self.ip, self.porta) # Envia resposta ao sakuray

        # PAREI AQUI
        # atualizei no backup a estação ativa, agora precisa redistribuir as vagas
        # primeiro: olhar no backup quantas estações estão ativas
        # segundo: dividir as vagas entre as estações ativas
        # terceiro: enviar mensagem para cada estação ativa com as vagas que ela deve cuidar

        #return f"Estação {self.id_estacao} ativada."
        return response
    

    async def requisitar_vaga(self, id_carro):
        print(" @@ requisitar vaga: ", len(self.vagas_livres))
        if len(self.vagas_livres) > 0:
            id_vaga = self.vagas_livres.pop(0)
            self.vagas_ocupadas[id_vaga] = id_carro
            print("Carro conseguiu vaga.")
            #await self.enviar_mensagem(f"OK {self.id_estacao} {id_vaga} {id_carro}", self.ip, self.porta)       # Envia um "OK" pro endereço da stação
            await self.enviar_mensagem(f"AV {self.id_estacao} {id_vaga} {id_carro}", self.ip, self.porta+10)    # Envia um "AV" pro middleware (middleware tem q atualizar o bkp no gerente)
        else:
            await self.enviar_mensagem(f"BV {id_carro}", self.ip, self.porta+10)    # Envia um "BV" (buscar vaga) para o middleware procurar vaga em outro middleware/estação
    

    async def vagas_disponiveis(self, ip, porta):
        # fazer isso para todas as estações ativas

        #enviar pro middleware que envia pro gerente que contem o bkacup
        await self.enviar_mensagem("VD", ip, porta+10)
        await self.enviar_mensagem(f"{self.id_estacao}:{len(self.vagas_livres)}-{len(self.vagas_ocupadas)}", self.ip, self.porta) 

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
    
    async def liberar_vaga(self, id_carro):
        if len(self.vagas_ocupadas) > 0:
            id_vaga = self.vagas_livres.pop(0)
            self.vagas_ocupadas[id_vaga] = id_carro
            print("Carro liberou vaga.")
            #await self.enviar_mensagem(f"OK {self.id_estacao} {id_vaga} {id_carro}", self.ip, self.porta)       # Envia um "OK" pro endereço da stação
            await self.enviar_mensagem(f"AV {self.id_estacao} {id_vaga} {id_carro}", self.ip, self.porta+10)    # Envia um "AV" pro middleware (middleware tem q atualizar o bkp no gerente)
        else:
            await self.enviar_mensagem(f"BV {id_carro}", self.ip, self.porta+10)    # Envia um "BV" (buscar vaga) para o middleware procurar vaga em outro middleware/estação

    # async def liberar_vaga(self):
    #     print("entrou no liberar vaga")
    #     if self.vagas_ocupadas > 0:
    #         self.vagas_ocupadas -= 1
    #         return f"Vaga liberada. Total ocupadas: {self.vagas_ocupadas}."
    #     else:
    #         return "Não há vagas ocupadas para liberar."


    async def finalizar_estacao(self):
        self.ativo = False
        return f"Estação {self.id_estacao} finalizada."




    # interperetar os comandos aqui, 
    # só atualizar o bkp (manager)
    # no AE o vagas_livres