import asyncio
import threading
from llist import sllist

porta_gerente = 5524
vagas_total = 3
lista_ativos = sllist()

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

    async def iniciar_socket_middleware(self):
        server = await asyncio.start_server(self.processar_mensagem, self.ip, self.porta)
        
        async with server:
            await server.serve_forever()


    async def processar_mensagem(self, reader, writer):
        data = await reader.read(1024)
        message = data.decode('utf-8')
        # print("message no middleware: ", message)
        # args[0] ja e o parametro e nao o comando
        print(f"Middleware {self.ip}:{self.porta} recebeu comando: {message}")

        if message.startswith("BV"):  # Comando buscar vaga
            # procurar na lista de ativos se tem vaga livre
            await self.teste_BV(lista_ativos)
            #response = await self.enviar_mensagem(f"BV", self.ip, porta_gerente) #(args[1]) # nesse caso, args[1] é o id_carro 
        
        elif message.startswith("AV"):
            msg = message.split()
            response = await self.enviar_mensagem(f'AV {msg[1].replace("Station", "")} {msg[2]} {msg[3]}', self.ip, porta_gerente) # id_estacao id_vaga id_carro
        
        elif message.startswith("AE"):
            msg = message.split()
            await self.teste_AE()
            # teste.join()
            response = await self.enviar_mensagem(f"AE.{msg[1]}.{self.vagas}", self.ip, porta_gerente) # AE id_estação => passar a mensagem ativar estação para o backup do gerente
            response2 = await self.enviar_mensagem(f"ativada.{self.vagas}", self.ip, self.porta-10) # AE id_estação => passar a mensagem ativar estação para a estação
            #print("\n ########      Ativos: ", lista_ativos)
        
        elif message.startswith("VD"):
            msg = message.split(".")
            print(">>>>> VD:: ", msg[1])
            # print(">>>>> VD:: )
            response = await self.enviar_mensagem(f"VD.{msg[1]}", self.ip, porta_gerente)

        elif message.startswith("vd_response"):
            msg = message.split(".")
            response = await self.enviar_mensagem(f"vd_response.{msg[1]}", self.ip, self.porta-10)
        
        elif message.startswith("nvagas"):
            print(">>>>> entrou nvagas middleware") 
            msg = message.split()
            response = await self.enviar_mensagem(f"response_nvagas {len(self.vagas)}", msg[1], int(msg[2]))
        
        elif message.startswith("response_nvagas"):
            print(">>>>> entrou response_nvagas middleware")
            self.response = message.split()[1]
            if not self.response_future.done():  # Verifica se a Future já foi completada
                self.response_future.set_result(self.response)

        elif message.startswith("emprestar_vagas"):
            print(">>>>> entrou emprestar middleware")
            msg = message.split()
            vagas_emprestando = self.vagas[:len(self.vagas)//2]
            self.vagas = self.vagas[len(self.vagas)//2:]
            response = await self.enviar_mensagem(f"response_emprestar_vagas.{vagas_emprestando}", msg[1], int(msg[2]))
            response = await self.enviar_mensagem(f"AE.{self.estacao.id_estacao}.{self.vagas}", self.ip, porta_gerente)

        elif message.startswith("response_emprestar_vagas"):
            print(">>>>> entrou response emprestar middleware ", message)
            self.response = message.split(".")[1]
            if not self.response_future.done():  # Verifica se a Future já foi completada
                self.response_future.set_result(self.response)

        elif message.startswith("ativada"):
            print(">>>>> entrou ativada middleware")
            lista_resposta = message.split(".")
            await self.enviar_mensagem(message, self.ip, self.porta-10)

        elif message.startswith("ocupada"):
            await self.enviar_mensagem("ocupada", self.ip, self.porta-10)
        else:
            response = "Comando não reconhecido"

        # writer.write(response.encode('utf-8'))
        # await writer.drain()
        #writer.close()


    async def teste_AE(self):
        max_estacao = -1
        index = -1
        a = 0

        if len(lista_ativos) > 0:
            for i in range(len(lista_ativos)):
                mid = lista_ativos[i]
                print(f"--------> sending nvagas {mid.ip} {mid.porta}")
                # Cria uma nova Future para aguardar a resposta antes de enviar a mensagem
                self.response_future = asyncio.Future()  # Create a new Future for each request
            
                await self.enviar_mensagem(f"nvagas {self.ip} {self.porta}", mid.ip, mid.porta)
                # Aguardar a resposta que será setada no processar_mensagem
                response = await self.response_future  # Await the response from processar_mensagem
            
                print(f"çççç {a} response: ", response)
                a += 1
                if int(response) > max_estacao:
                    max_estacao = int(response)
                    index = i
            print("max_estacao, index: ", max_estacao, index)
            self.response_future = asyncio.Future()  # Create a new Future for each request
            bla = await self.enviar_mensagem(f"emprestar_vagas {self.ip} {self.porta}", lista_ativos[index].ip, lista_ativos[index].porta)
            response = await self.response_future  # Await the response from processar_mensagem
            # transformar response de string para lista
            print("response: ", self.response)
            temp = self.response.replace("[", "").replace("]", "").split(",")
            self.vagas = [int(i) for i in temp]
            print("vagas pos ativar: ", self.vagas)

            # distribuir vagas
            lista_ativos.append(self) #
        else:
            self.vagas = [i for i in range(0, vagas_total)]
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
            print(f"Conectado a {ip}:{porta}")
            writer.write(mensagem.encode())
            await writer.drain()

            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Erro ao enviar mensagem: {e}")
            if self.response_future and not self.response_future.done():
                self.response_future.set_exception(e)
