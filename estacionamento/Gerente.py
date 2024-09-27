import asyncio

vagas = 3
porta_gerente = 5524

class Gerente:
    def __init__(self, ip, porta, portas_middlewares):
        self.ip = ip
        self.porta = porta
        self.backup_estacoes = {}
        for id in range(1, len(portas_middlewares)+1):
            self.backup_estacoes[id] = {
                "ip": "127.0.0.1",
                "porta": portas_middlewares[id-1],
                "id_vagas_livres": [],
                "id_vagas_ocupadas": [],
                "estacao_ativa": False
                # "porta_middleware": None,
                # "ultimo_ping": None
            }

    async def iniciar_socket_gerente(self):
        server = await asyncio.start_server(self.processar_mensagem, self.ip, self.porta)
        print(f"Gerente iniciado em {self.ip}:{self.porta}")
        async with server:
            await server.serve_forever()


    async def processar_mensagem(self, reader, writer):
        data = await reader.read(100)
        message = data.decode('utf-8')
        print(f"Gerente recebeu: {message}")

        # Processa mensagens para atualizar o backup
        if message.startswith("AV"):
            msg = message.split()
            response = await self.ocupar_vaga(msg[1], msg[2], msg[3])    # id_estacao id_vaga  id_carro
        
        elif message.startswith("AE"):
            msg = message.split(".")
            id_nova_estacao = int(msg[1].replace("Station", ""))
            print(f'{id_nova_estacao}')
            #response = self.ativar_estacao(id_nova_estacao, vagas)  # id_estacao
            self.backup_estacoes[id_nova_estacao]["estacao_ativa"] = True
            temp = msg[2].replace("[", "").replace("]", "").split(",")
            self.backup_estacoes[id_nova_estacao]["id_vagas_livres"] = [int(i) for i in temp]
            with open('backup_estacoes.txt', 'w') as f:
                for key in self.backup_estacoes.keys():
                    f.write(f'{key}:{self.backup_estacoes[key]}\n')

        elif message.startswith("BV"):
            response = self.buscar_vaga()

        elif message.startswith("VD"): # VD 3
            msg = message.split(".")
            response = await self.vagas_disponiveis(msg[1])
            await self.enviar_mensagem(response, self.backup_estacoes[int(msg[1])]["ip"], self.backup_estacoes[int(msg[1])]["porta"])
        else:
            print("Nao chegou comando pro gerente")

        # print(f"Gerente respondeu: {response}")
        # writer.write(response.encode('utf-8'))
        # await writer.drain()
        # #writer.close()
        # await self.enviar_mensagem(response, self.backup_estacoes[id_nova_estacao]["ip"], self.backup_estacoes[id_nova_estacao]["porta"]) # Victor mexi aqui pra id nova estacao antes tava id estacao


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




    def adicionar_vagas(self, id_estacao, vagas, tipo_vaga, qtd_vagas):
        print("adicionar_vagas:")
        aux_vagas = vagas
        count = 0
        for indice in  range(0, qtd_vagas):
            if self.backup_estacoes[id_estacao]["estacao_ativa"]:
                
                if count == 0:
                    count+=1
                    self.backup_estacoes[id_estacao][tipo_vaga] = []

                self.backup_estacoes[id_estacao][tipo_vaga].append(aux_vagas[indice])
                vagas.remove(aux_vagas[indice])
        return vagas
        

    async def ocupar_vaga(self, id_estacao, id_vaga, id_carro):
        self.backup_estacoes[id_estacao]["id_vagas_livres"].remove(id_vaga)
        self.backup_estacoes[id_estacao]["id_vagas_ocupadas"].append({"id_vaga": id_vaga, "id_carro": id_carro})
        with open('backup_estacoes.txt', 'a') as f:
            for key in self.backup_estacoes.keys():
                f.write(f'{key}:{self.backup_estacoes[key]}\n')
        self.enviar_mensagem(f"ocupada", self.backup_estacoes[id_estacao]["ip"], self.backup_estacoes[id_estacao]["porta"]+10)
        #response = f"Vaga ocupada."
        #return response


    async def liberar_vaga(self, id_estacao, id_vaga, id_carro):
        self.backup_estacoes[id_estacao]["id_vagas_ocupadas"].remove({"id_vaga": id_vaga, "id_carro": id_carro})
        self.backup_estacoes[id_estacao]["id_vagas_livres"].append(id_vaga)
        response = f"Vaga liberada"
        return response

    
    async def vagas_disponiveis(self, id_to_send):
        # Verifica quantas vagas estão disponíveis e ocupadas em cada estação ativa
        mensagem = "vd_response."
        for id_estacao in self.backup_estacoes.keys():
            mensagem += f"{id_estacao}:{len(self.backup_estacoes[id_estacao]['id_vagas_livres'])}-{len(self.backup_estacoes[id_estacao]['id_vagas_ocupadas'])}   "
        
        # for key in self.backup_estacoes.keys():
        #             f.write(f'{key}:{self.backup_estacoes[key]}\n')
        print(mensagem)
        #self.enviar_mensagem(mensagem, self.backup_estacoes[id_to_send]["ip"], self.backup_estacoes[id_to_send]["porta"]+10)
        return mensagem
        

    async def buscar_vaga(self):
        for i in range(0, len(self.backup_estacoes)):
            if self.backup_estacoes[i]["estacao_ativa"]:
                response = f"{self.backup_estacoes[i]['ip']} {self.backup_estacoes[i]['porta']}"
                # talvez retornar porta do middleware correspondente a ele
            else:
                print("Nenhuma estaçaõ ativa")
        return response
    


    def ativar_estacao(self, id_nova_estacao):
        nenhuma_estacao_ativa = True
        for id_estacao in self.backup_estacoes:
            if self.backup_estacoes[id_estacao]["estacao_ativa"]:
                nenhuma_estacao_ativa = False
        if nenhuma_estacao_ativa:
            for id_vaga in range(0, vagas):
                self.backup_estacoes[id_nova_estacao]["id_vagas_livres"].append(id_vaga)
            
            self.backup_estacoes[id_nova_estacao]["estacao_ativa"] = True
            print(self.backup_estacoes)
        else:
            vagas_ocupadas = []
            vagas_livres = []
            total_estacoes_ativas = 1
            for id_estacao in self.backup_estacoes:
                if self.backup_estacoes[id_estacao]["estacao_ativa"]:
                    vagas_ocupadas.extend(self.backup_estacoes[id_estacao]["id_vagas_ocupadas"])
                    vagas_livres.extend(self.backup_estacoes[id_estacao]["id_vagas_livres"])
                    total_estacoes_ativas+=1

            qtd_vagas_ocupadas_estacao = int(len(vagas_ocupadas)/total_estacoes_ativas)

            for id_estacao in self.backup_estacoes:
                if self.backup_estacoes[id_estacao]["estacao_ativa"]:
                    vagas_ocupadas = self.adicionar_vagas(id_estacao, vagas_ocupadas, "id_vagas_ocupadas", qtd_vagas_ocupadas_estacao)

            self.backup_estacoes[id_nova_estacao]["id_vagas_ocupadas"].extend(vagas_ocupadas)

            qtd_vagas_livres_estacao = int(len(vagas_livres)/total_estacoes_ativas)

            for id_estacao in self.backup_estacoes:
                if self.backup_estacoes[id_estacao]["estacao_ativa"]:
                    vagas_livres = self.adicionar_vagas(id_estacao, vagas_livres, "id_vagas_livres", qtd_vagas_livres_estacao)

            self.backup_estacoes[id_nova_estacao]["id_vagas_livres"].extend(vagas_livres)
            
        print(self.backup_estacoes)

        response = f'ativada.{self.backup_estacoes[id_nova_estacao]["id_vagas_livres"]}'
        return response