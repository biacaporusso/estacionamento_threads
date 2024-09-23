import socket
import threading
from Estacao import Estacao

# Função para iniciar o servidor da estação
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
    with open('file.txt', 'r') as file:
        for line in file:
            partes = line.split()
            if len(partes) == 3:
                id_estacao = partes[0]
                ip = partes[1]
                porta = int(partes[2])
                total_vagas = 5  # Definimos um número fixo de vagas por estação
                estacao = Estacao(id_estacao, total_vagas)
                estacoes.append((ip, porta, estacao))
    return estacoes

# Função principal para iniciar servidores para todas as estações
def main():
    estacoes = ler_arquivo_estacoes()  # Lê o arquivo file.txt e cria as estações

    threads = []

    # Inicia um servidor em cada porta em threads separadas
    for ip, porta, estacao in estacoes:
        thread = threading.Thread(target=iniciar_servidor, args=(ip, porta, estacao))
        threads.append(thread)
        thread.start()

    # Mantém a execução principal aguardando o término das threads
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
