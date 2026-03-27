import threading

class DadosJogo:
    def __init__(self):
        self.jogadores = {} 
        self.lock = threading.Lock() 

    def adicionar_jogador(self, player_id, nome):
        with self.lock:
            self.jogadores[player_id] = {'nome': nome, 'y': 50, 'score': 0}

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
                # LIMITE DO CHÃO
                if nova_pos >= 100:
                    # GAME OVER / RESPAWN: Volta à posição inicial
                    self.jogadores[player_id]['y'] = 20
                    # Perde a pontuação toda
                    self.jogadores[player_id]['score'] = 0 
                else:
                    self.jogadores[player_id]['y'] = nova_pos
                    # Só ganha pontos se não bater no chão
                    self.jogadores[player_id]['score'] += 1

    def obter_estado(self):
        with self.lock:
            return self.jogadores.copy()