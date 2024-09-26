import asyncio

porta_gerente = 5524

class Middleware:
    def __init__(self, ip, porta, estacao):
        self.ip = ip
        self.porta = porta
        self.estacao = estacao  # Referência à estação correspondente
        self.proximo_middleware = None  # O próximo middleware na lista circular
        self.ativo = False

    async def iniciar_socket_middleware(self):
        server = await asyncio.start_server(self.processar_mensagem, self.ip, self.porta)
        
        async with server:
            await server.serve_forever()


    async def processar_mensagem(self, reader, writer):
        data = await reader.read(100)
        message = data.decode('utf-8')
        print("message no middleware: ", message)
        comando, *args = message.split()
        # args[0] ja e o parametro e nao o comando
        print(f"Middleware {self.ip}:{self.porta} recebeu comando: {message}")

        if comando == "BV":  # Comando buscar vaga
            response = await self.enviar_mensagem(f"BV", self.ip, porta_gerente) #(args[1]) # nesse caso, args[1] é o id_carro 
        elif comando == "AV":
            response = await self.enviar_mensagem(f"AV {args[0]} {args[1]} {args[2]}", self.ip, porta_gerente) # id_estacao id_vaga id_carro
        elif comando == "AE":
            response = await self.enviar_mensagem(f"AE {args[0]}", self.ip, porta_gerente) # AE id_estação => passar a mensagem ativar estação para o backup do gerente
        elif comando == "VD":
            response = await self.enviar_mensagem("VD", self.ip, porta_gerente)
        elif comando == "ativada":
            await self.enviar_mensagem("ativada", self.ip, self.porta-10)
        else:
            response = "Comando não reconhecido"

        # writer.write(response.encode('utf-8'))
        # await writer.drain()
        #writer.close()


    # Função para enviar mensagens ao middleware
    async def enviar_mensagem(self, mensagem, ip, porta):
        try:
            reader, writer = await asyncio.open_connection(self.ip, porta)
            writer.write(mensagem.encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Erro ao conectar ao middleware: {e}")

