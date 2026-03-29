import threading

class DadosJogo:
    def __init__(self):
        self.jogadores = {} 
        self.lock = threading.Lock() 

    def adicionar_jogador(self, player_id, nome):
       with self.lock:
            # Verifica se já estão 5 jogadores a jogar
            if len(self.jogadores) >= 5:
                return False # Recusa a entrada
            self.jogadores[player_id] = {'nome': nome, 'y': 20, 'score': 0}
            return True # Entrada com sucesso

    def remover_jogador(self, player_id):
        with self.lock:
            if player_id in self.jogadores:
                del self.jogadores[player_id]

    def atualizar_posicao(self, player_id, acao):
        with self.lock:
            if player_id in self.jogadores:
                if acao == "FLAP":
                    nova_pos = self.jogadores[player_id]['y'] - 20
                    # LIMITE DO TETO: O Y não pode ser menor que 0
                    self.jogadores[player_id]['y'] = max(0, nova_pos)

    def aplicar_gravidade(self, player_id):
        with self.lock:
            if player_id in self.jogadores:
                nova_pos = self.jogadores[player_id]['y'] + 10
                
                if nova_pos >= 100:
                    self.jogadores[player_id]['y'] = 20
                    self.jogadores[player_id]['score'] = 0 
                    return True
                else:
                    self.jogadores[player_id]['y'] = nova_pos
                    self.jogadores[player_id]['score'] += 1
                    return False 
        return False

    def obter_estado(self):
        with self.lock:
            return self.jogadores.copy()
