import asyncio

class Estacao:
    def __init__(self, id_estacao, ip, porta):
        self.id_estacao = id_estacao
        self.ip = ip
        self.porta = porta
        self.vagas_livres = []
        self.vagas_ocupadas = {} # dicionario: id_vaga => id_carro
        self.ativo = False  # Estação começa inativa
        self.server_socket = None  # Referência ao socket da estação        implementar dicionario

    async def iniciar_socket(self):
        # Inicializa o socket usando asyncio para comunicação assíncrona
        self.server_socket = await asyncio.start_server(self.processar_comando, self.ip, self.porta)
        print(f"Estação {self.id_estacao} está escutando em {self.ip}:{self.porta}")
        async with self.server_socket:
            await self.server_socket.serve_forever()


    async def processar_comando(self, reader, writer):
        data = await reader.read(100)
        message = data.decode('utf-8')

        partes = message.split()  # Divide a mensagem em partes
        comando = partes[0]  # O primeiro elemento é o comando
        parametro = partes[1] if len(partes) > 1 else None  # O segundo elemento é o parâmetro (se existir)
        print(f"Estação {self.id_estacao} recebeu comando: {comando}")

        if comando == "RV":
            if parametro is not None:
                response = await self.requisitar_vaga(parametro)  # Passa o parâmetro para a função
            #else:
            #    response = "Parâmetro ausente para RV."
        elif comando == "LV":
            response = await self.liberar_vaga()
        elif comando == "AE":
            response = await self.ativar_estacao()
        elif comando == "FE":
            response = await self.finalizar_estacao()
        else:
            response = "Comando inválido."

        writer.write(response.encode('utf-8'))
        await writer.drain()
        writer.close()


    async def requisitar_vaga(self, id_carro):
        
        if len(self.vagas_livres) > 0:
            id_vaga = self.vagas_livres.pop(0)
            self.vagas_ocupadas[id_vaga] = id_carro
            print("Carro conseguiu vaga.")
            mensagem = f"OK {self.id_estacao} {id_vaga} {id_carro}"
            await self.enviar_mensagem("OK", self.ip, self.porta)       # Envia um "OK" pro endereço da stação
            await self.enviar_mensagem(f"AV {self.id_estacao} {id_vaga} {id_carro}", self.ip, self.porta+10)    # Envia um "AV" pro middleware (middleware tem q atualizar o bkp no gerente)
        else:
            await self.enviar_mensagem("BV {id_carro}", self.ip, self.porta+10)    # Envia um "BV" (buscar vaga) para o middleware procurar vaga em outro middleware/estação
    


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
        if len(self.vagas_ocupadas) < self.vagas_livres:
            # Encontra a próxima vaga disponível
            for vaga in range(1, self.vagas_livres + 1):
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
    # no AE o vagas_livres