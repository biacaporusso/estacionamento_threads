import asyncio
from Estacao import Estacao
from Middleware import Middleware
from Gerente import Gerente
import threading

porta_gerente = 5523

# Função para ler o arquivo de estações e retornar uma lista de objetos Estacao
def ler_arquivo_estacoes():
    estacoes = []
    middlewares = []
    portas_middlewares = []

    with open('file.txt', 'r') as file:
        for line in file:
            partes = line.split()
            if len(partes) == 3:
                id_estacao = partes[0]
                ip = partes[1]
                porta = int(partes[2])

                # Cria a estação
                estacao = Estacao(id_estacao, ip, porta)
                estacoes.append(estacao)

                # Cria o middleware correspondente à estação
                middleware = Middleware(ip, porta + 10, estacao)
                portas_middlewares.append(porta + 10)
                middlewares.append(middleware)

   

    return estacoes, middlewares, portas_middlewares


async def main():
    estacoes, middlewares, portas_middlewares = ler_arquivo_estacoes()  # Lê o arquivo e cria as estações e middlewares
    tasks = []

    # Iniciar o servidor do gerente
    gerente = Gerente(ip="127.0.0.1", porta=porta_gerente, portas_middlewares=portas_middlewares)
    task_gerente = asyncio.create_task(gerente.iniciar_socket_gerente())
    tasks.append(task_gerente)

    # Inicia o servidor para cada estação e seu middleware correspondente
    threads = []
    for estacao, middleware in zip(estacoes, middlewares):
        # Iniciar o socket da estação
        task_estacao = asyncio.create_task(estacao.iniciar_socket_estacao())
        tasks.append(task_estacao)

        # Iniciar o socket do middleware
        task_middleware = asyncio.create_task(middleware.iniciar_socket_middleware())
        tasks.append(task_middleware)
        
        # task_ping = asyncio.create_task(middleware.iniciar_ping())
        task_ping = asyncio.create_task(middleware.ping_estacoes())
        tasks.append(task_ping) 
        
        # ping_thread = threading.Thread(target=middleware.ping_estacoes)
        # threads.append(ping_thread)

    # for thread in threads:
    #     print("start threads")
    #     thread.start()
    # Aguarda todas as tasks (servidores de estação e middleware) rodarem simultaneamente
    await asyncio.gather(*tasks)


# Executa a função main
asyncio.run(main())