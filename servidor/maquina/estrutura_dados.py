import threading
import random

class DadosJogo:
    """
    Classe central que gere todo o estado e a lógica física do jogo 'Flappy Priolo'.
    Garante que todas as operações de leitura e escrita no estado do jogo sejam 
    seguras num ambiente multi-thread (Thread-safe) utilizando Locks.
    Cada jogador possui o seu próprio conjunto de vulcões.
    """

    def __init__(self):
        """
        Inicializa os dados base do jogo, incluindo o armazenamento de jogadores 
        e a configuração das leis da física (gravidade e movimento).
        """
        # Dicionário para guardar os jogadores. Chave: player_id (str), Valor: estado do jogador (dict)
        self.jogadores = {} 
        self.lock = threading.Lock() 
                
        # Parâmetros físicos
        self.gravidade = 5
        self.velocidade_tubos = 2
        self.distancia_entre_tubos = 60
        self.posicao_x_priolos = 20 

    def adicionar_jogador(self, player_id, nome):
       """
       Tenta adicionar um novo jogador à partida.
       
       :param player_id: O identificador único do jogador (IP e porta).
       :param nome: O nome de ecrã escolhido pelo jogador.
       :return: Um tuplo (sucesso: bool, mensagem: str) indicando se a entrada foi permitida.
       """
       with self.lock:
            # 1. Verifica limite de jogadores para não sobrecarregar o servidor
            if len(self.jogadores) >= 5:
                return False, "SERVIDOR CHEIO"
            
            # 2. Verifica se o nome já está a ser utilizado por outro jogador ativo
            for pid, dados in self.jogadores.items():
                if dados['nome'] == nome:
                    return False, "NOME JÁ EXISTE"
            
            # 3. Guarda o jogador e inicializa
            self.jogadores[player_id] = {
                'nome': nome, 
                'x': self.posicao_x_priolos, 
                'y': 20, 
                'score': 0,
                'vulcoes': [{'x': 100, 'abertura_y': 50, 'contado': False}] 
            }
            return True, "SUCESSO"

    def remover_jogador(self, player_id):
        """
        Remove um jogador do jogo, apagando o seu estado no servidor.
        
        :param player_id: O identificador único do jogador a remover.
        """
        with self.lock:
            if player_id in self.jogadores:
                del self.jogadores[player_id]

    def atualizar_posicao(self, player_id, acao):
        """
        Atualiza a posição do jogador com base numa ação recebida.
        
        :param player_id: O identificador do jogador que executou a ação.
        :param acao: O tipo de ação (neste caso, espera-se "FLAP").
        :return: True se o jogador bateu no "teto" (limite superior), False caso contrário.
        """
        with self.lock:
            if player_id in self.jogadores:
                if acao == "FLAP":
                    # O Priolo sobe subtraindo valor ao eixo Y
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
        """
        Aplica a gravidade contínua a um jogador específico e verifica se este 
        colidiu com o chão ou com os seus vulcões.
        
        :param player_id: O identificador do jogador.
        :return: True se o jogador morreu (colisão), False caso continue vivo.
        """
        with self.lock:
            if player_id not in self.jogadores:
                return False
            
            jogador = self.jogadores[player_id]
            jogador['y'] += self.gravidade
            morreu = False

            # 1. Colisão com o chão (Limite inferior do ecrã)
            if jogador['y'] >= 100:
                morreu = True

            # 2. Colisão com os vulcões
            for v in jogador['vulcoes']:
                # Verifica se o Priolo está alinhado no eixo X com o vulcão
                if abs(v['x'] - jogador['x']) < 10: 
                    # Verifica se o Priolo bateu nas margens do vulcão
                    if jogador['y'] < v['abertura_y'] - 15 or jogador['y'] > v['abertura_y'] + 15:
                        morreu = True

            if morreu:
                # Reset do jogador: Volta ao início, zera os pontos e gera um novo ecrã
                jogador['y'] = 20 
                jogador['score'] = 0 
                jogador['vulcoes'] = [{'x': 100, 'abertura_y': random.randint(30, 70), 'contado': False}]
                return True
            
            return False
        
    def verificar_pontos(self):
        """
        Verifica a posição transversal de todos os jogadores em relação aos seus vulcões.
        Se um jogador ultrapassou um vulcão de forma segura, ganha um ponto.
        """
        with self.lock:
            for pid, jogador in self.jogadores.items():
                for v in jogador['vulcoes']:
                    # Se o vulcão ficou à esquerda do pássaro e ainda não foi contabilizado
                    if v['x'] < self.posicao_x_priolos and not v.get('contado', False):
                        jogador['score'] += 1
                        v['contado'] = True

    def atualizar_mundo(self):
        """
        Desloca os vulcões para a esquerda.
        Remove os vulcões que já saíram do ecrã e gera novos vulcões há direita de 
        forma independente para cada jogador.
        """
        with self.lock:
            for pid, jogador in self.jogadores.items():
                # Move todos os vulcões deste jogador para a esquerda
                for v in jogador['vulcoes']:
                    v['x'] -= self.velocidade_tubos

                # Se o vulcão mais antigo saiu completamente do ecrã pela esquerda, elimina-o
                if jogador['vulcoes'] and jogador['vulcoes'][0]['x'] < -10:
                    jogador['vulcoes'].pop(0)

                # Se o último vulcão da lista já andou o suficiente, cria um novo no lado direito
                if jogador['vulcoes'][-1]['x'] < (100 - self.distancia_entre_tubos):
                    nova_abertura = random.randint(30, 70)
                    jogador['vulcoes'].append({'x': 100, 'abertura_y': nova_abertura, 'contado': False})

    def obter_estado(self):
        """
        Obtém uma fotografia atual do estado de todos os jogadores no jogo para ser 
        enviada via broadcast.
        
        :return: Um dicionário contendo a cópia do estado atual de todos os jogadores.
        """
        with self.lock:
            # Envia a cópia do dicionário de jogadores
            return {
                'jogadores': self.jogadores.copy()
            }