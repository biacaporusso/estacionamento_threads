import asyncio
import threading
from llist import sllist

porta_gerente = 5523
vagas_total = 10
# lista_ativos = sllist()
lista_ativos = []

class Middleware:
    def __init__(self, ip, porta, estacao):
        self.ip = ip
        self.porta = porta
        self.response = None
        self.response_future = None
        self.vagas = []
        self.estacao = estacao  # Referência à estação correspondente
        self.proximo_middleware = None  # O próximo middleware na lista circular
        self.ativo = False
        self.pings = []
        self.tempo_ping = 0

    async def iniciar_socket_middleware(self):
        server = await asyncio.start_server(self.processar_mensagem, self.ip, self.porta)
        
        async with server:
            await server.serve_forever()

    # async def iniciar_ping(self):
    #     server = await asyncio.start_server(self.ping_estacoes, self.ip, self.porta+50)

    #     async with server:
    #         await server.serve_forever()


    async def processar_mensagem(self, reader, writer):
        data = await reader.read(1024)
        message = data.decode('utf-8')
        # print(f"Middleware {self.ip}:{self.porta} recebeu comando: {message}")

        if message.startswith("RV"):
            msg = message.split()
            await self.requisitar_vaga(msg[1], msg[2])

        elif message.startswith("AE"):
            msg = message.split()
            self.ativo = True
            await self.teste_AE()
            response = await self.enviar_mensagem(f"atualizar_vaga.{msg[1]}.{self.vagas}", self.ip, porta_gerente) # AE id_estação => passar a mensagem ativar estação para o backup do gerente
            #response2 = await self.enviar_mensagem(f"ativada.{self.vagas}", self.ip, self.porta-10) # AE id_estação => passar a mensagem ativar estação para a estação
        
        elif message.startswith("LV"):
            msg = message.split()
            await self.teste_LV(msg[1])

        elif message.startswith("FE"):
            msg = message.split()
            self.ativo = False
            self.vagas = []

        elif message.startswith("VD"):
            msg = message.split(".")
            response = await self.enviar_mensagem(f"VD.{msg[1]}", self.ip, porta_gerente)

        elif message.startswith("vd_response"):
            msg = message.split(".")
            response = await self.enviar_mensagem(f"vd_response.{msg[1]}", self.ip, self.porta-10)
        
        elif message.startswith("nvagas"):
            msg = message.split()
            response = await self.enviar_mensagem(f"set_response.{len(self.vagas)}", msg[1], int(msg[2]))

        elif message.startswith("emprestar_vagas"):
            msg = message.split()
            # cálculo de quantas vagas vai emprestar
            vagas_emprestando = self.vagas[:len(self.vagas)//2]
            self.vagas = self.vagas[len(self.vagas)//2:]
            await self.enviar_mensagem(f"set_response.{vagas_emprestando}", msg[1], int(msg[2]))
            await self.enviar_mensagem(f"atualizar_vaga.{self.estacao.id_estacao}.{self.vagas}", self.ip, porta_gerente)

        elif message.startswith("vaga_livre"):
            msg = message.split()
            alocado = False
            for i in range(len(self.vagas)):
                vaga = self.vagas[i]
                if vaga[1] is None:
                    self.vagas[i] = (vaga[0], msg[3])
                    await self.enviar_mensagem(f"atualizar_vaga.{self.estacao.id_estacao}.{self.vagas}", self.ip, porta_gerente)
                    response = await self.enviar_mensagem(f"set_response.alocada", msg[1], msg[2])
                    alocado = True
                    break
            if not alocado:
                response = await self.enviar_mensagem(f"set_response.nao_alocada", msg[1], msg[2])

        elif message.startswith("liberar_carro"):
            msg = message.split()
            liberado = False
            for i in range(len(self.vagas)):
                vaga = self.vagas[i]
                if vaga[1] == msg[3]: # se é o id_carro
                    self.vagas[i] = (vaga[0], None)
                    await self.enviar_mensagem(f"atualizar_vaga.{self.estacao.id_estacao}.{self.vagas}", self.ip, porta_gerente)
                    response = await self.enviar_mensagem(f"set_response.liberou", msg[1], msg[2])
                    liberado = True
                    break
            if not liberado:
                await self.enviar_mensagem(f"set_response.nao_liberada", msg[1], msg[2])
        
        elif message.startswith("ping"):
            msg = message.split()
            if self.ativo == True:
                await self.enviar_mensagem(f"set_response.{self.estacao.id_estacao}", msg[1], int(msg[2]))
            else:
                await self.enviar_mensagem(f"set_response.None", msg[1], int(msg[2]))

        elif message.startswith("herdar_vaga"):
            msg = message.split(".")
            temp = msg[1].replace("[", "").replace("]", "").split(")")
            vagas_estacao_falhou = []
            for i in temp:
                if not i:
                    continue
                var = i.replace("(", "").replace(",", "").split()
                # print(f"\n\n->>>> {var}\n")
                if var[1] == "None":
                    var[1] = None
                vagas_estacao_falhou.append((int(var[0]), var[1]))
            
            self.vagas.extend(vagas_estacao_falhou)
            await self.enviar_mensagem(f"atualizar_vaga.{self.estacao.id_estacao}.{self.vagas}", self.ip, porta_gerente)

        elif message.startswith("set_response"):
            self.response = message.split(".")[1]
            if not self.response_future.done():
                self.response_future.set_result(self.response)


        
        else:
            response = "Comando não reconhecido"

        # writer.write(response.encode('utf-8'))
        # await writer.drain()
        #writer.close()



    async def ping_estacoes(self):
        while True:
            # print(f" {self.estacao.id_estacao} KKKKKKKKKKKKKKKKKKKKK entrou no ping")
            # if not self.ativo:
            #     await asyncio.sleep(2)
            #     continue
            while not self.ativo:
                await asyncio.sleep(1)

            await asyncio.sleep(10)
            for mid in lista_ativos:
                if mid != self:
                    self.response_future = asyncio.Future()
                    await self.enviar_mensagem(f"ping {self.ip} {self.porta}", mid.ip, mid.porta)
                    response = await self.response_future
                    if response != "None":
                        self.pings.append(response) # guardar response (id_estacao) na lista de ping
            # verificar se o middleware ta na lista de ping
            self.pings.append(self.estacao.id_estacao)
            # print(f"Ping {self.estacao.id_estacao} {self.pings}")
            if len(lista_ativos) != len(self.pings): # se tiver diferente, ocorreu falha
                # descobrir qual middleware falhou
                for mid in lista_ativos:
                    if mid.estacao.id_estacao not in self.pings:
                        print(" === Eleição: quem descobriu e quem falhou", self.estacao.id_estacao, mid.estacao.id_estacao)
                        lista_ativos.remove(mid)
                        self.pings = []
                        await self.eleicao(mid.estacao.id_estacao)
                        break
            else:
                self.pings = []
                print(" ¨¨ todas ativas")


    async def eleicao(self, id_estacao_falha):
        # redistribuir as vagas que estavam na estação que falhou (usar o gerente pra pegar as vagas de quem falhou)
        self.response_future = asyncio.Future()
        await self.enviar_mensagem(f"eleicao {id_estacao_falha} {self.ip} {self.porta}", self.ip, porta_gerente)
        response = await self.response_future # vagas do mid que falhou
        temp = response.replace("[", "").replace("]", "").split(")")
        vagas_estacao_falhou = []
        for i in temp:
            if not i:
                continue
            var = i.replace("(", "").replace(",", "").split()
            if var[1] == "None":
                var[1] = None
            vagas_estacao_falhou.append((int(var[0]), var[1]))
        # contas p redistribuir as vagas (mandar p quem tem menos ao invés de mais)
        min_estacao = 9999
        index = -1
        if len(lista_ativos) > 0: # ja tem estação ativada entao tem q redistribuir as vagas
            for i in range(len(lista_ativos)):
                mid = lista_ativos[i]
                if mid == self:
                    continue
                print(f"--------> sending nvagas {mid.ip} {mid.porta}")
                # Cria uma nova Future para aguardar a resposta antes de enviar a mensagem
                self.response_future = asyncio.Future()
                # perguntando pro mid quantas vagas ele tem e depois responder
                await self.enviar_mensagem(f"nvagas {self.ip} {self.porta}", mid.ip, mid.porta) 
                # Aguardar a resposta que será setada no processar_mensagem
                response = await self.response_future # response = quantas vagas aquele mid tem
                # ver qual é o middleware com menos vagas
                if int(response) < min_estacao:
                    min_estacao = int(response)
                    index = i
            print("min_estacao, index: ", min_estacao, index) # min_estacao = quantas vagas o mid com menos vagas tem e index = indice do mid com menos vagas
            # agora eu tenho a estação com menos vagas (min_estacao) e seu indice
            if len(self.vagas) < min_estacao: # se o mid que falhou tem menos vagas que o mid com menos vagas
                self.vagas.extend(vagas_estacao_falhou) # redistribuir as vagas
                await self.enviar_mensagem(f"atualizar_vaga.{self.estacao.id_estacao}.{self.vagas}", self.ip, porta_gerente)
            else:
                print(f"Estacao falhou {vagas_estacao_falhou}")
                await self.enviar_mensagem(f"herdar_vaga.{vagas_estacao_falhou}", lista_ativos[index].ip, lista_ativos[index].porta)


    async def requisitar_vaga(self, id_estacao, id_carro):
        # verificar se há vaga na estação
        for i in range(len(self.vagas)):
            vaga = self.vagas[i]
            if vaga[1] is None: # vaga livre
                self.vagas[i] = (vaga[0], id_carro)
                print("     self.vagas[i][1]: ", self.vagas[i][1])
                await self.enviar_mensagem(f"atualizar_vaga.{self.estacao.id_estacao}.{self.vagas}", self.ip, porta_gerente)
                return "alocou"
            
        # não há vaga na estação, então tem que percorrer a lista buscando outra vaga
        if len(lista_ativos) > 0:
            for i in range(len(lista_ativos)):
                mid = lista_ativos[i]
                self.response_future = asyncio.Future()
                
                # verificar se tem vaga livre nesse mid
                await self.enviar_mensagem(f"vaga_livre {self.ip} {self.porta} {id_carro}", mid.ip, mid.porta) 
                response = await self.response_future
                if response == "alocada":
                    return "alocou"
                else:
                    continue


    async def teste_LV(self, id_carro):
        for i in range(len(self.vagas)):
            vaga = self.vagas[i]
            if vaga[1] == id_carro:
                print(" |||||||||| entrou no antes atualizar vaga de LV")
                self.vagas[i] = (vaga[0], None)
                await self.enviar_mensagem(f"atualizar_vaga.{self.estacao.id_estacao}.{self.vagas}", self.ip, porta_gerente)
                return "liberou"
        
        # procurar nas outras listas o id_carro
        if len(lista_ativos) > 0:
            for i in range(len(lista_ativos)):
                mid = lista_ativos[i]
                self.response_future = asyncio.Future()
                
                # verificar se tem id_carro nesse mid
                await self.enviar_mensagem(f"liberar_carro {self.ip} {self.porta} {id_carro}", mid.ip, mid.porta) 
                response = await self.response_future
                if response == "liberou":
                    return "liberou"
                else:
                    continue


    async def teste_AE(self):
        max_estacao = -1
        index = -1
        a = 0
        if len(lista_ativos) > 0: # ja tem estação ativada entao tem q redistribuir as vagas
            for i in range(len(lista_ativos)):
                mid = lista_ativos[i]
                print(f"--------> sending nvagas {mid.ip} {mid.porta}")
                # Cria uma nova Future para aguardar a resposta antes de enviar a mensagem
                self.response_future = asyncio.Future()
            
                # perguntando pro mid quantas vagas ele tem e depois responder
                await self.enviar_mensagem(f"nvagas {self.ip} {self.porta}", mid.ip, mid.porta) 
                # Aguardar a resposta que será setada no processar_mensagem
                response = await self.response_future # response = quantas vagas aquele mid tem
            
                a += 1
                # ver qual é o middleware com mais vagas
                if int(response) > max_estacao:
                    max_estacao = int(response)
                    index = i
            print("max_estacao, index: ", max_estacao, index)
            self.response_future = asyncio.Future()
            # pedir vaga pra outra estação (dentro do emprestar_vagas")
            await self.enviar_mensagem(f"emprestar_vagas {self.ip} {self.porta}", lista_ativos[index].ip, lista_ativos[index].porta)
            response = await self.response_future # lista de vagas que emprestou
            # transformar response de string para lista
            print("response: ", self.response)
            #temp = self.response.replace("[", "").replace("]", "").split(",")
            temp = self.response.replace("[", "").replace("]", "").split(")")
            for i in temp:
                if not i:
                    continue
                var = i.replace("(", "").replace(",", "").split()
                if var[1] == "None":
                    var[1] = None
                self.vagas.append((int(var[0]), var[1]))
            #print("vagas pos ativar: ", self.vagas)

            # distribuir vagas
            lista_ativos.append(self) #
        else:
            self.vagas = [(int(i), None) for i in range(0, vagas_total)]
            print("primeira ativação vagas: ", self.vagas)
            lista_ativos.append(self) #


    def teste_BV(self, lista_ativos):
        print("entrou no teste")
        for middleware in lista_ativos:
            print(" ************** vagas livres: ", len(middleware.estacao.vagas_livres))
            if len(middleware.estacao.vagas_livres) > 0:
                print(" @@@ tem vaga")


    # Função para enviar mensagens ao middleware
    async def enviar_mensagem(self, mensagem, ip, porta):
        try:
            reader, writer = await asyncio.open_connection(ip, porta)
            #print(f"Conectado a {ip}:{porta}")
            writer.write(mensagem.encode())
            await writer.drain()

            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            if self.response_future and not self.response_future.done():
                self.response_future.set_exception(e)
