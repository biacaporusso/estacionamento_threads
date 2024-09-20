import socket
import threading

# Função para iniciar o servidor em uma determinada porta
def iniciar_servidor(ip, porta):
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        servidor.bind((ip, porta))  # Vincula o servidor ao IP e Porta
        servidor.listen(5)  # Limita a 5 conexões simultâneas no máximo
        print(f"Servidor escutando no IP {ip}, Porta {porta}...")

        while True:
            conexao, endereco = servidor.accept()  # Aguarda por novas conexões
            print(f"Conexão recebida de {endereco} na porta {porta}")

            # Recebe a mensagem do cliente (sistema do professor)
            mensagem = conexao.recv(1024).decode('utf-8')
            print(f"Mensagem recebida: {mensagem} na porta {porta}")

            # Processar a mensagem (neste exemplo, estamos esperando um código 'RV')
            if mensagem.startswith("RV"):  # Verifica se a mensagem é uma requisição de vaga
                print(f"Processando requisição de vaga na porta {porta}...")
                conexao.send("OK".encode('utf-8'))  # Envia a resposta "OK"

            # Feche a conexão depois de processar a mensagem
            conexao.close()
            print(f"Conexão fechada na porta {porta}.")
    
    except Exception as e:
        print(f"Ocorreu um erro no servidor da porta {porta}: {e}")

    finally:
        servidor.close()  # Garante que o servidor seja fechado corretamente em caso de erro

# Função para ler o arquivo de estações e retornar uma lista com IPs e portas
def ler_arquivo_estacoes():
    estacoes = []
    with open('file.txt', 'r') as file:
        for line in file:
            partes = line.split()
            if len(partes) == 3:
                ip = partes[1]
                porta = int(partes[2])
                estacoes.append((ip, porta))
    return estacoes

# Função principal para iniciar um servidor para cada estação
def main():
    estacoes = ler_arquivo_estacoes()  # Lê o arquivo file.txt e extrai IPs e Portas

    threads = []

    # Inicia um servidor em cada porta em threads separadas
    for ip, porta in estacoes:
        thread = threading.Thread(target=iniciar_servidor, args=(ip, porta))
        threads.append(thread)
        thread.start()
        print(f"Servidor iniciado para IP {ip} e Porta {porta}...")

    # Mantém a execução principal aguardando o término das threads (servidores)
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
