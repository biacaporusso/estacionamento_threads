from Vaga import Vaga
from Vaga import Vaga

# Classe Estacao que representa uma estação com vagas e status de ativação
class Estacao:
    def __init__(self, id_estacao, total_vagas):
        self.id_estacao = id_estacao  # ID da estação
        self.vagas = [Vaga() for _ in range(total_vagas)]  # Lista de vagas
        self.ativada = False  # Inicialmente a estação está desativada

    def ativar(self):
        if not self.ativada:
            self.ativada = True  # Ativa a estação
            print(f"Estação {self.id_estacao} ativada.")
            return "OK"
        else:
            print(f"Estação {self.id_estacao} já está ativada.")
            return "Já ativada"

    def desativar(self):
        self.ativada = False  # Desativa a estação
        print(f"Estação {self.id_estacao} desativada.")
        return "OK"

    def vagas_ocupadas(self):
        return sum(vaga.ocupada for vaga in self.vagas)

    def vagas_livres(self):
        return len(self.vagas) - self.vagas_ocupadas()

    def requisitar_vaga(self):
        if self.vagas_livres() > 0:
            for vaga in self.vagas:
                if vaga.ocupar():
                    return "OK"  # Vaga ocupada com sucesso
        return "SEM VAGA"  # Nenhuma vaga disponível

    def liberar_vaga(self):
        if self.vagas_ocupadas() > 0:
            for vaga in self.vagas:
                if vaga.liberar():
                    return "OK"  # Vaga liberada com sucesso
        return "ERRO"  # Nenhuma vaga ocupada para liberar

    def vagas_disponiveis(self):
        return f"Vagas disponiveis = {self.vagas_livres()} | Ocupadas = {self.vagas_ocupadas()}"
