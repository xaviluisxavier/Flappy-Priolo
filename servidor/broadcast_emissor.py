import threading
import time
from comunicacao.sockets_util import send_object

class ThreadBroadcast(threading.Thread):
    def __init__(self, lista_clientes, dados, intervalo=0.1): 
        super().__init__(daemon=True)
        self.lista_clientes = lista_clientes
        self.dados = dados
        self.intervalo = intervalo
        self.running = True

    def run(self):
        """Loop que atualiza o estado do jogo e envia para os clientes."""
        print("ThreadBroadcast ativa")
        while self.running:
            time.sleep(self.intervalo)
            
            # 1. Atualiza a física do jogo (move os vulcões, aplica gravidade)
            self.dados.atualizar_mundo()
            for player_id in list(self.dados.jogadores.keys()):
                self.dados.aplicar_gravidade(player_id)
            
            # 2. Pega no estado atualizado
            estado = self.dados.obter_estado()
            
            #3. atualiza os pontos 
            self.dados.verificar_pontos()
            
            # 3. Envia (Broadcast) para TODOS os clientes da lista
            clientes = self.lista_clientes.obter_lista()
            for player_id, conn in list(clientes.items()):
                try:
                    send_object(conn, estado)
                except Exception:
                    # Se der erro a enviar. Remove o cliente.
                    self.lista_clientes.remover(player_id)
                    self.dados.remover_jogador(player_id)
