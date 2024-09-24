import asyncio

class Middleware:
    def __init__(self, ip, porta, estacao):
        self.ip = ip
        self.porta = porta
        self.estacao = estacao  # Referência à estação correspondente
        self.proximo_middleware = None  # O próximo middleware na lista circular

    async def iniciar_socket(self):
        # Inicializa o servidor assíncrono do middleware
        server = await asyncio.start_server(self.processar_mensagem, self.ip, self.porta)
        #print(f"Middleware iniciado em {self.ip}:{self.porta}")

        async with server:
            await server.serve_forever()

    async def processar_mensagem(self, reader, writer):
        data = await reader.read(100)
        message = data.decode('utf-8')
        print(f"Middleware {self.ip}:{self.porta} recebeu comando: {message}")

        if message == "BV":  # Comando buscar vaga
            response = await self.buscar_vaga()
        elif message == "AV":  # Atualizar vaga (comando vindo da estação)
            response = await self.atualizar_bkp_gerente()
        else:
            response = "Comando não reconhecido"

        writer.write(response.encode('utf-8'))
        await writer.drain()
        writer.close()

    async def buscar_vaga(self):
        # Verifica se há vagas na estação correspondente
        if self.estacao.vagas_ocupadas < self.estacao.total_vagas:
            self.estacao.vagas_ocupadas += 1
            return "OK"  # Vaga encontrada
        else:
            # Não há vagas, consulta o próximo middleware
            print(f"Middleware {self.ip}:{self.porta} consultando próximo middleware...")
            return await self.consultar_proximo_middleware()

    async def consultar_proximo_middleware(self):
        if self.proximo_middleware:
            try:
                reader, writer = await asyncio.open_connection(self.proximo_middleware.ip, self.proximo_middleware.porta)
                writer.write("BV".encode('utf-8'))
                await writer.drain()

                response = await reader.read(100)
                writer.close()
                await writer.wait_closed()
                return response.decode('utf-8')  # Retorna a resposta do próximo middleware
            except Exception as e:
                print(f"Erro ao conectar com o próximo middleware: {e}")
                return "Erro no middleware"

        return "Nenhum middleware disponível"

    async def atualizar_bkp_gerente(self):
        # Função de exemplo para atualizar o backup no gerente
        print(f"Middleware {self.ip}:{self.porta} atualizando bkp no gerente...")
        # Aqui você pode implementar a lógica de comunicação com o gerente para atualizar o estado
        return "Backup atualizado no gerente"
