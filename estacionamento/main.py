import asyncio
import socket
import threading
from Estacao import Estacao
from Middleware import Middleware

# ============= ignorar essa função por enquanro ==============
def iniciar_servidor(ip, porta, estacao):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        servidor.bind((ip, porta))
        servidor.listen(5)
        print(f"Servidor da estação {estacao.id_estacao} escutando no IP {ip}, Porta {porta}...")

        while True:
            conexao, endereco = servidor.accept()
            print(f"Conexão recebida de {endereco} na porta {porta}")

            mensagem = conexao.recv(1024).decode('utf-8')
            print(f"Mensagem recebida: {mensagem} na porta {porta}")

            if mensagem.startswith("AE"):  # Ativar Estação
                resposta = estacao.ativar()
                conexao.send(resposta.encode('utf-8'))

            elif mensagem.startswith("FE"):  # Falha na Estação
                resposta = estacao.desativar()
                conexao.send(resposta.encode('utf-8'))
                print(f"Estação {estacao.id_estacao} entrou em estado de falha (desativada).")

            elif estacao.ativada:
                if mensagem.startswith("RV"):  # Requisitar Vaga
                    resposta = estacao.requisitar_vaga()
                    conexao.send(resposta.encode('utf-8'))

                elif mensagem.startswith("LV"):  # Liberar Vaga
                    resposta = estacao.liberar_vaga()
                    conexao.send(resposta.encode('utf-8'))

                elif mensagem.startswith("VD"):  # Verificar Vagas Disponíveis
                    resposta = estacao.vagas_disponiveis()
                    print(f" ==> {resposta}")
                    conexao.send(resposta.encode('utf-8'))

                else:
                    print(f"Mensagem desconhecida: {mensagem}")
            else:
                print(f"Estação {estacao.id_estacao} inativa. Ignorando mensagem: {mensagem}")
            
            conexao.close()
    
    except Exception as e:
        print(f"Erro no servidor da estação {estacao.id_estacao}: {e}")
    
    finally:
        servidor.close()

# Função para ler o arquivo de estações e retornar uma lista de objetos Estacao
def ler_arquivo_estacoes():
    estacoes = []
    middlewares = []

    with open('file.txt', 'r') as file:
        for line in file:
            partes = line.split()
            if len(partes) == 3:
                id_estacao = partes[0]
                ip = partes[1]
                porta = int(partes[2])
                total_vagas = 5  # Definimos um número fixo de vagas por estação

                # cria a estação
                estacao = Estacao(id_estacao, ip, porta, total_vagas)
                # estacoes.append((ip, porta, estacao))

                # cria o middleware correspondente
                middleware = Middleware(ip, porta+10)
                middlewares.append(middleware)

                # lista circular de middlewares
                for i in range(len(middlewares)):
                    next_index = (i + 1) % len(middlewares)  # Calcula o próximo middleware de forma circular
                    middlewares[i].proximo_middleware = middlewares[next_index]

    return estacoes


async def start_servidor(ip, porta, estacao):
    server = await asyncio.start_server(estacao, ip, porta)
    async with server:
        print(f'Servidor da estação {estacao} iniciado em {ip}:{porta}')
        await server.serve_forever()  # Mantém o servidor ativo



async def main():

    estacoes = ler_arquivo_estacoes()  # Lê o arquivo file.txt e cria as estações e seus respectivos middlewares
    
    tasks = []

    # Inicia um servidor em cada porta de maneira assíncrona
    for ip, porta, estacao in estacoes:
        task = asyncio.create_task(start_servidor(ip, porta, estacao))
        tasks.append(task)

    # Aguarda a execução de todas as tasks de forma simultânea
    await asyncio.gather(*tasks)

# Executa a função main
asyncio.run(main())

if __name__ == "__main__":
    main()



# classe middleware tbm tem q ter socket -> estação 8080 middleware correspondente 8081 
# middleware que vai ver se a estação tem vaga livre 
# passar por aprametro no middleware ip e porta tanto da estação quanto do outro middleware q será acessado
# (talvez) usar async ao inves de thread
# RV: rv, update rv e foward rv 
# RV 456 -> id do carro

# manager vai ser o bkp e a falha