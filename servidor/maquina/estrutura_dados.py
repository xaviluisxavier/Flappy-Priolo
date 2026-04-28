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
        self.velocidade_vulcoes = 2
        self.distancia_entre_vulcoes = 60
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
            servidor_esta_cheio = len(self.jogadores) >= 5
            if servidor_esta_cheio:
                return False, "SERVIDOR CHEIO"
            
            # 2. Verifica se o nome já está a ser utilizado por outro jogador ativo
            for pid, dados in self.jogadores.items():
                nome_ja_em_uso = dados['nome'] == nome
                if nome_ja_em_uso:
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
                    forca_do_salto = 20
                    nova_pos = self.jogadores[player_id]['y'] - forca_do_salto
                    
                    bateu_no_teto_do_ecra = nova_pos < 0
                    
                    if bateu_no_teto_do_ecra:
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
            limite_do_chao = 100
            bateu_no_chao = jogador['y'] >= limite_do_chao
            if bateu_no_chao:
                morreu = True

            # 2. Colisão com os vulcões
            for v in jogador['vulcoes']:
                # Verifica se o Priolo está alinhado no eixo X com o vulcão
                distancia_horizontal = abs(v['x'] - jogador['x'])
                margem_horizontal_da_colisao = 10
                esta_alinhado_no_eixo_x = distancia_horizontal < margem_horizontal_da_colisao
                
                if esta_alinhado_no_eixo_x: 
                    # Verifica se o Priolo bateu nas margens do vulcão
                    metade_do_tamanho_da_abertura = 15
                    teto_do_vulcao = v['abertura_y'] - metade_do_tamanho_da_abertura
                    chao_do_vulcao = v['abertura_y'] + metade_do_tamanho_da_abertura
                    
                    bateu_no_vulcao_de_cima = jogador['y'] < teto_do_vulcao
                    bateu_no_vulcao_de_baixo = jogador['y'] > chao_do_vulcao
                    
                    if bateu_no_vulcao_de_cima or bateu_no_vulcao_de_baixo:
                        morreu = True

            if morreu:
                # Reset do jogador: Volta ao início, zera os pontos e gera um novo ecrã
                jogador['y'] = 20 
                jogador['score'] = 0 
                nova_abertura_aleatoria = random.randint(30, 70)
                jogador['vulcoes'] = [{'x': 100, 'abertura_y': nova_abertura_aleatoria, 'contado': False}]
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
                    passaro_ja_passou_pelo_vulcao = v['x'] < self.posicao_x_priolos
                    ponto_ainda_nao_contabilizado = not v.get('contado', False)
                    
                    if passaro_ja_passou_pelo_vulcao and ponto_ainda_nao_contabilizado:
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
                    v['x'] -= self.velocidade_vulcoes

                tem_vulcoes_no_ecra = len(jogador['vulcoes']) > 0
                
                if tem_vulcoes_no_ecra:
                    vulcao_mais_antigo = jogador['vulcoes'][0]
                    vulcao_saiu_do_ecra = vulcao_mais_antigo['x'] < -10
                    
                    # Se o vulcão saiu completamente do ecrã pela esquerda, elimina-o
                    if vulcao_saiu_do_ecra:
                        jogador['vulcoes'].pop(0)

                # Avalia de novo se há vulcões após uma possível remoção acima
                if len(jogador['vulcoes']) > 0:
                    ultimo_vulcao = jogador['vulcoes'][-1]
                    posicao_para_criar_novo_vulcao = 100 - self.distancia_entre_vulcoes
                    
                    ultimo_vulcao_andou_o_suficiente = ultimo_vulcao['x'] < posicao_para_criar_novo_vulcao
                    
                    # Se o último vulcão da lista já andou o suficiente, cria um novo no lado direito
                    if ultimo_vulcao_andou_o_suficiente:
                        nova_abertura = random.randint(30, 70)
                        novo_vulcao = {'x': 100, 'abertura_y': nova_abertura, 'contado': False}
                        jogador['vulcoes'].append(novo_vulcao)

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
