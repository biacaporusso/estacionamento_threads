import asyncio

#vagas = 3
porta_gerente = 5523

class Gerente:
    def __init__(self, ip, porta, portas_middlewares):
        self.ip = ip
        self.porta = porta
        self.backup_estacoes = {}
        for id in range(1, len(portas_middlewares)+1):
            self.backup_estacoes[id] = {
                "ip": "127.0.0.1",
                "porta": portas_middlewares[id-1],
                "vagas": [],
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
        
        if message.startswith("atualizar_vaga"):
            msg = message.split(".")
            id_nova_estacao = int(msg[1].replace("Station", ""))
            self.backup_estacoes[id_nova_estacao]["estacao_ativa"] = True
            temp = msg[2].replace("[", "").replace("]", "").split(")")
            vagas = []
            for i in temp:
                if not i:
                    continue
                var = i.replace("(", "").replace(",", "").split()
                if var[1] == "None":
                    var[1] = None
                vagas.append((int(var[0]), var[1]))
            self.backup_estacoes[id_nova_estacao]["vagas"] = vagas
            with open('backup_estacoes.txt', 'w') as f:
                for key in self.backup_estacoes.keys():
                    f.write(f'{key}:{self.backup_estacoes[key]}\n')

        elif message.startswith("VD"): # VD 3
            msg = message.split(".")
            await self.vagas_disponiveis(msg[1])
            # await self.enviar_mensagem(response, self.backup_estacoes[int(msg[1])]["ip"], self.backup_estacoes[int(msg[1])]["porta"])
        
        elif message.startswith("eleicao"):
            msg = message.split()
            # msg[1] = id da estação que falhou
            id_falhou = msg[1].replace("Station", "")
            # msg[2] e msg[3] = ip e porta de quem pediu
            vagas_falhou = self.backup_estacoes[int(id_falhou)]["vagas"]
            self.backup_estacoes[int(id_falhou)]["vagas"] = []
            await self.enviar_mensagem(f"set_response.{vagas_falhou}", msg[2], msg[3])
        
        else:
            print("Nao chegou comando pro gerente")


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


    async def liberar_vaga(self, id_estacao, id_vaga, id_carro):
        self.backup_estacoes[id_estacao]["id_vagas_ocupadas"].remove({"id_vaga": id_vaga, "id_carro": id_carro})
        self.backup_estacoes[id_estacao]["id_vagas_livres"].append(id_vaga)
        response = f"Vaga liberada"
        return response

    
    async def vagas_disponiveis(self, id_to_send):
        # Verifica quantas vagas estão disponíveis e ocupadas em cada estação ativa
        mensagem = "vd_response."
        for id_estacao in self.backup_estacoes.keys():
            # calculo de vagas livres e ocupadas
            vagas_livres = 0
            for vaga in self.backup_estacoes[id_estacao]["vagas"]:
                if vaga[1] is None:
                    vagas_livres += 1
            vagas_ocupadas = len(self.backup_estacoes[id_estacao]["vagas"]) - vagas_livres
            mensagem += f"\n{id_estacao}: {vagas_livres} - {vagas_ocupadas}   "
        
        # for key in self.backup_estacoes.keys():
        #             f.write(f'{key}:{self.backup_estacoes[key]}\n')
        print(mensagem)


    async def buscar_vaga(self):
        for i in range(0, len(self.backup_estacoes)):
            if self.backup_estacoes[i]["estacao_ativa"]:
                response = f"{self.backup_estacoes[i]['ip']} {self.backup_estacoes[i]['porta']}"
                # talvez retornar porta do middleware correspondente a ele
            else:
                print("Nenhuma estaçaõ ativa")
        return response
    
