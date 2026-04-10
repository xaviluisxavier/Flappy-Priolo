import threading
import random

class DadosJogo:
    def __init__(self):
        """Inicializa os dados do jogo, incluindo jogadores, vulcões e parâmetros do jogo."""
        # Dicionário para guardar os jogadores
        self.jogadores = {} 
        self.lock = threading.Lock() 
        
        # Cada vulcão tem uma posição 'x' e um 'abertura_y'
        self.vulcoes = [{'x': 100, 'abertura_y': 50}] 
        
        # Parâmetros do Jogo
        self.gravidade = 5
        self.velocidade_tubos = 2
        self.distancia_entre_tubos = 60
        self.posicao_x_priolos = 20 

    def adicionar_jogador(self, player_id, nome):
       """Adiciona um jogador ao jogo, verificando o limite de jogadores e a unicidade do nome."""
       with self.lock:
            # 1. Verifica limite de jogadores
            if len(self.jogadores) >= 5:
                return False, "SERVIDOR CHEIO"
            
            # 2. Verifica nome
            for pid, dados in self.jogadores.items():
                if dados['nome'] == nome:
                    return False, "NOME JÁ EXISTE"
            
            # 3. Guarda o jogador usando o ID
            self.jogadores[player_id] = {
                'nome': nome, 
                'x': self.posicao_x_priolos, 
                'y': 20, 
                'score': 0
            }
            return True, "SUCESSO"

    def remover_jogador(self, player_id):
        """Remove um jogador do jogo usando seu ID."""
        with self.lock:
            if player_id in self.jogadores:
                del self.jogadores[player_id]

    def atualizar_posicao(self, player_id, acao):
        """Atualiza a posição do jogador com base na ação recebida (FLAP)."""
        with self.lock:
            if player_id in self.jogadores:
                if acao == "FLAP":
                    nova_pos = self.jogadores[player_id]['y'] - 20
                    
                    if nova_pos < 0:
                        self.jogadores[player_id]['y'] = 20
                        self.jogadores[player_id]['score'] = 0
                        return True
                    else:
                        self.jogadores[player_id]['y'] = nova_pos
                        return False
        return False

    def aplicar_gravidade(self, player_id):
        """Aplica a gravidade ao jogador e verifica colisões com o chão e com os vulcões."""
        with self.lock:
            if player_id not in self.jogadores:
                return False
            
            jogador = self.jogadores[player_id]
            jogador['y'] += self.gravidade
            morreu = False

            # 1. Colisão com o chão
            if jogador['y'] >= 100:
                morreu = True

            # 2. Colisão com os vulcões
            for v in self.vulcoes:
                # Se o vulcão está a cruzar-se com a posição do Priolo
                if abs(v['x'] - jogador['x']) < 10: 
                    # Verifica se bateu nas margens do vulcão
                    if jogador['y'] < v['abertura_y'] - 15 or jogador['y'] > v['abertura_y'] + 15:
                        morreu = True

            if morreu:
                # Reset da posição e pontuação quando o jogo termina para o jogador
                jogador['y'] = 20 
                jogador['score'] = 0 
                return True
            
            return False
        

    def verificar_pontos(self):
        """Verifica se os jogadores passaram pelos vulcões e atualiza a pontuação."""
        with self.lock:
            for v in self.vulcoes:
                # Se o vulcão passou a posição X dos pássaros
                if v['x'] < self.posicao_x_priolos and not v.get('contado', False):
                    for pid in self.jogadores:
                        self.jogadores[pid]['score'] += 1
                    v['contado'] = True 

    def atualizar_mundo(self):
        """Move os vulcões para a esquerda e gera novos vulcões quando necessário."""
        with self.lock:
            for v in self.vulcoes:
                v['x'] -= self.velocidade_tubos

            if self.vulcoes and self.vulcoes[0]['x'] < -10:
                self.vulcoes.pop(0)

            if self.vulcoes[-1]['x'] < (100 - self.distancia_entre_tubos):
                nova_abertura = random.randint(30, 70)
                self.vulcoes.append({'x': 100, 'abertura_y': nova_abertura, 'contado': False})

    def obter_estado(self):
        """Retorna o estado atual do jogo, incluindo a posição dos jogadores e dos vulcões."""
        with self.lock:
            # Envia o estado de todos os jogadores e também a lista de vulcões
            return {
                'jogadores': self.jogadores.copy(),
                'vulcoes': list(self.vulcoes)
            }
        
