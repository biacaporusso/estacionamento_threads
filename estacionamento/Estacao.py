import asyncio
from Vaga import Vaga
import socket

# Classe Estacao que representa uma estação com vagas e status de ativação
class Estacao:
    def __init__(self, id_estacao, ip, porta, total_vagas):
        self.id_estacao = id_estacao  
        self.ip = ip
        self.porta = porta
        self.total_vagas = total_vagas  # Número total de vagas
        self.ativada = False  # A estação começa desativada
        self.vagas_ocupadas = {}  # Dicionário que mapeia a vaga ao ID do carro
        self.proxima_vaga = 1  # Controle para definir a próxima vaga disponível
        self.socket_estacao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def ativar(self):
        if not self.ativada:
            self.ativada = True  # Ativa a estação
            #print(f"Estação {self.id_estacao} ativada.")
            #return "OK"
        else:
            print(f"Estação {self.id_estacao} já está ativada.")
            #return "Já ativada"

    def desativar(self):
        self.ativada = False  # Desativa a estação
        print(f"Estação {self.id_estacao} desativada.")
        #return "OK"

    def vagas_livres(self):
        return self.total_vagas - self.vagas_ocupadas()
    

    async def requisitar_vaga(self, id_carro):
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
                    # Envia um "atualizar" pro middleware (middleware tem q atualizar o bkp no gerente)
                    await self.enviar_mensagem("atualizar", self.ip, self.porta+10)
                    return True

        # Se não houver vaga, envia "BV" ao middleware
        print(f'Nenhuma vaga disponível na estação {self.id_estacao}.')
        await self.enviar_mensagem("BV", self.ip, self.porta+10)
        return False


    # Função para enviar mensagens ao middleware
    async def enviar_mensagem(self, mensagem, ip, porta):
        try:
            reader, writer = await asyncio.open_connection(self.ip, porta)
            writer.write(mensagem.encode())
            await writer.drain()
            #print(f"Mensagem '{mensagem}' enviada para o middleware {self.ip}:{middleware_porta}.")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Erro ao conectar ao middleware: {e}")






    # ======= IGNORA POR ENQUANTO ==========

    def liberar_vaga(self, id_carro):
        # Procura a vaga ocupada pelo carro
        for vaga, carro in self.vagas_ocupadas.items():
            if carro == id_carro:
                # Libera a vaga
                del self.vagas_ocupadas[vaga]
                print(f'Vaga {vaga} liberada pelo carro {id_carro}.')
                return True  # Retorna sucesso na liberação
        print(f'Carro {id_carro} não encontrado em nenhuma vaga.')
        return False  # Carro não encontrado

    # interperetar os comandos aqui, 
    # só atualizar o bkp (manager)
