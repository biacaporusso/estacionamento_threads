import asyncio

class Estacao:
    def __init__(self, id_estacao, ip, porta, total_vagas):
        self.id_estacao = id_estacao
        self.ip = ip
        self.porta = porta
        self.total_vagas = total_vagas
        self.vagas_ocupadas = 0
        self.ativo = False  # Estação começa inativa
        self.server_socket = None  # Referência ao socket da estação

    async def iniciar_socket(self):
        # Inicializa o socket usando asyncio para comunicação assíncrona
        self.server_socket = await asyncio.start_server(self.processar_comando, self.ip, self.porta)
        print(f"Estação {self.id_estacao} está escutando em {self.ip}:{self.porta}")
        async with self.server_socket:
            await self.server_socket.serve_forever()


    async def processar_comando(self, reader, writer):
        data = await reader.read(100)
        message = data.decode('utf-8')
        print(f"Estação {self.id_estacao} recebeu comando: {message}")

        if message.startswith("RV"):
            response = await self.requisitar_vaga()
        elif message.startswith("LV"):
            response = await self.liberar_vaga()
        elif message.startswith("AE"):
            response = await self.ativar_estacao()
        elif message.startswith("FE"):
            response = await self.finalizar_estacao()
        else:
            response = "Comando inválido."

        writer.write(response.encode('utf-8'))
        await writer.drain()
        writer.close()


    async def requisitar_vaga(self):
        if self.vagas_ocupadas < self.total_vagas:
            self.vagas_ocupadas += 1
            print("Carro conseguiu vaga.")
            await self.enviar_mensagem("OK", self.ip, self.porta)       # Envia um "OK" pro endereço da stação
            await self.enviar_mensagem("AV", self.ip, self.porta+10)    # Envia um "AV" pro middleware (middleware tem q atualizar o bkp no gerente)
        else:
            await self.enviar_mensagem("BV", self.ip, self.porta+10)    # Envia um "BV" (buscar vaga) para o middleware procurar vaga em outro middleware/estação


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


    async def liberar_vaga(self):
        if self.vagas_ocupadas > 0:
            self.vagas_ocupadas -= 1
            return f"Vaga liberada. Total ocupadas: {self.vagas_ocupadas}."
        else:
            return "Não há vagas ocupadas para liberar."


    async def ativar_estacao(self):
        self.ativo = True
        return f"Estação {self.id_estacao} ativada."


    async def finalizar_estacao(self):
        self.ativo = False
        return f"Estação {self.id_estacao} finalizada."



    ## =========================================================================================================
    

    async def my_requisitar_vaga(self, id_carro):
        # Verifica se ainda há vagas disponíveis
        if len(self.vagas_ocupadas) < self.total_vagas:
            # Encontra a próxima vaga disponível
            for vaga in range(1, self.total_vagas + 1):
                if vaga not in self.vagas_ocupadas:
                    # Aloca a vaga para o carro
                    self.vagas_ocupadas[vaga] = id_carro
                    print(f'Vaga {vaga} alocada ao carro {id_carro}.')

                    # Envia um "OK" pro endereço da stação
                    await self.enviar_mensagem("OK", self.ip, self.porta)
                    # Envia um "AV" pro middleware (middleware tem q atualizar o bkp no gerente)
                    await self.enviar_mensagem("AV", self.ip, self.porta+10)
                    return True

        # Se não houver vaga, envia "BV" ao middleware (buscar vaga em outra estação)
        print(f'Nenhuma vaga disponível na estação {self.id_estacao}.')
        await self.enviar_mensagem("BV", self.ip, self.porta+10)
        return False






    # interperetar os comandos aqui, 
    # só atualizar o bkp (manager)
