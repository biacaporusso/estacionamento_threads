class Vaga:
    def __init__(self):
        self.ocupada = False  # Inicialmente a vaga não está ocupada

    def ocupar(self):
        if not self.ocupada:
            self.ocupada = True
            return True  # Vaga foi ocupada com sucesso
        return False  # Vaga já estava ocupada

    def liberar(self):
        if self.ocupada:
            self.ocupada = False
            return True  # Vaga foi liberada com sucesso
        return False  # Vaga já estava livre