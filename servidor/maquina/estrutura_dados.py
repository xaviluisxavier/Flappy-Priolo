import threading
import random
import servidor

class DadosJogo:
    def __init__(self):
        self.jogadores = {} 
        self.lock = threading.Lock() 
        self.v_id_counter = 0

    def gerar_id_vulcao(self):
        self.v_id_counter += 1
        return self.v_id_counter

    def adicionar_jogador(self, player_id, nome):
       with self.lock:
            if len(self.jogadores) >= 5: return False, "SERVIDOR CHEIO"
            for pid, dados in self.jogadores.items():
                if dados['nome'] == nome: return False, "NOME JÁ EXISTE"
            
            self.jogadores[player_id] = {
                'nome': nome, 
                'x': servidor.POSICAO_X_PRIOLOS, 
                'y': 20.0, 
                'vel_y': 0.0, 
                'score': 0,
                'vulcoes': [{'id': self.gerar_id_vulcao(), 'x': 100.0, 'abertura_y': random.randint(15, 85), 'contado': False}] 
            }
            return True, "SUCESSO"

    def remover_jogador(self, player_id):
        with self.lock:
            if player_id in self.jogadores: del self.jogadores[player_id]

    def atualizar_posicao(self, player_id, acao):
        with self.lock:
            if player_id in self.jogadores:
                if acao == "FLAP":
                    jogador = self.jogadores[player_id]
                    jogador['vel_y'] = -servidor.SALTO_BASE 
        return False

    def aplicar_gravidade(self, player_id):
        with self.lock:
            if player_id not in self.jogadores: return False
            jogador = self.jogadores[player_id]
            
            jogador['vel_y'] += servidor.GRAVIDADE_BASE 
            
            if jogador['vel_y'] > 4.5:
                jogador['vel_y'] = 4.5
                
            jogador['y'] += jogador['vel_y']
            
            morreu = False
            
            if jogador['y'] >= 100 or jogador['y'] < 0: 
                morreu = True
            
            for v in jogador['vulcoes']:
                if abs(v['x'] - jogador['x']) < 10: 
                    if jogador['y'] < v['abertura_y'] - 15 or jogador['y'] > v['abertura_y'] + 15: 
                        morreu = True

            if morreu:
                jogador['y'] = 20.0
                jogador['vel_y'] = 0.0 
                jogador['score'] = 0 
                jogador['vulcoes'] = [{'id': self.gerar_id_vulcao(), 'x': 100.0, 'abertura_y': random.randint(15, 85), 'contado': False}]
                return True
                
            return False
        
    def verificar_pontos(self):
        with self.lock:
            for pid, jogador in self.jogadores.items():
                for v in jogador['vulcoes']:
                    if v['x'] < servidor.POSICAO_X_PRIOLOS and not v.get('contado', False):
                        jogador['score'] += 1
                        v['contado'] = True

    def atualizar_mundo(self):
        with self.lock:
            for pid, jogador in self.jogadores.items():
                velocidade_atual = servidor.VELOCIDADE_BASE + ((jogador['score'] // 5) * 0.2)
                for v in jogador['vulcoes']: 
                    v['x'] -= velocidade_atual
                    
                if jogador['vulcoes'] and jogador['vulcoes'][0]['x'] < -10: 
                    jogador['vulcoes'].pop(0)
                    
                if jogador['vulcoes'][-1]['x'] < (100 - servidor.DISTANCIA_ENTRE_VULCOES):
                    jogador['vulcoes'].append({'id': self.gerar_id_vulcao(), 'x': 100.0, 'abertura_y': random.randint(15, 85), 'contado': False})

    def obter_estado(self):
        with self.lock: 
            estado_limpo = {}
            for pid, j in self.jogadores.items():
                estado_limpo[pid] = {
                    'nome': j['nome'],
                    'x': int(j['x']),
                    'y': int(j['y']),
                    'score': j['score'],
                    'vulcoes': [{'id': v.get('id', 0), 'x': int(v['x']), 'abertura_y': int(v['abertura_y']), 'contado': v['contado']} for v in j['vulcoes']]
                }

            parametros_atuais = {
                'gravidade': round(servidor.GRAVIDADE_BASE, 2),
                'salto': round(servidor.SALTO_BASE, 2),
                'velocidade': round(servidor.VELOCIDADE_BASE, 2),
                'distancia': servidor.DISTANCIA_ENTRE_VULCOES,
                'v_ids': self.v_id_counter
            }
            return {'jogadores': estado_limpo, 'parametros': parametros_atuais}
