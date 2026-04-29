import threading
import time
import json
from typing import Dict
from servidor.maquina.lista_clientes import ListaClientes
import servidor

class ThreadBroadcast(threading.Thread):
    """
    Classe que funciona como o Motor do Jogo e o Emissor de Broadcast.
    É executada numa thread separada a cada fração de segundo para atualizar as leis 
    da física do jogo e enviar o estado atualizado para todos os clientes ligados.
    """

    def __init__(self, lista_clientes: ListaClientes, dados, intervalo: float = 0.03): 
        """
        Inicializa a thread do motor de jogo.
        A thread é configurada como 'daemon' para que termine automaticamente 
        quando o servidor principal for encerrado.
        
        :param lista_clientes: Referência para a estrutura que gere os clientes ligados.
        :param dados: Referência para a estrutura de dados (DadosJogo) com o estado do mundo.
        :param intervalo: O tempo de pausa (em segundos) entre cada atualização do jogo (ex: 0.2s).
        """
        super().__init__(daemon=True)
        self.lista_clientes = lista_clientes
        self.dados = dados
        self.intervalo = intervalo
        self.running = True

    def send_int(self, connection, value: int, n_bytes: int) -> None:
        """
        Envia um valor inteiro através de uma ligação socket, convertendo-o 
        para formato de bytes (big-endian).
        
        :param connection: A ligação socket do cliente de destino.
        :param value: O valor inteiro a ser enviado.
        :param n_bytes: O tamanho em bytes que o inteiro deve ocupar.
        """
        connection.send(value.to_bytes(n_bytes, byteorder="big", signed=True))

    def send_object(self, connection, obj):
        """
        Codifica e envia um objeto (dicionário) em formato JSON para um cliente.
        O protocolo envia primeiro o tamanho da mensagem (em bytes) e depois os dados, 
        para que o recetor saiba exatamente quanto tem de ler.
        
        :param connection: A ligação socket do cliente de destino.
        :param obj: O objeto Python a ser serializado e enviado.
        """
        data = json.dumps(obj).encode('utf-8')
        size = len(data)
        self.send_int(connection, size, servidor.INT_SIZE)
        connection.send(data)

    def broadcast_object(self, obj: Dict) -> None:
        """
        Envia uma mensagem (objeto) para todos os clientes ativos em simultâneo.
        Se detetar que um cliente se desligou ou ocorreu um erro na transmissão, 
        fecha a ligação e remove esse jogador do jogo para libertar recursos.
        
        :param obj: O estado do jogo a ser transmitido (em formato de dicionário).
        """
        with self.lista_clientes._lock:
            for address, conn in list(self.lista_clientes._clientes.items()):
                try:
                    self.send_object(conn, obj)
                except Exception:
                    # Cliente desconectou-se ou ocorreu um erro de rede
                    conn.close()
                    self.lista_clientes.remover(address)
                    self.dados.remover_jogador(str(address)) # Remove o jogador do jogo se ele cair

    def run(self):
        """
        Ciclo principal Jogo. Enquanto o servidor estiver a correr, 
        este método executa os seguintes passos a cada intervalo de tempo:
        1. Aplica a gravidade a todos os pássaros (fazendo-os cair).
        2. Atualiza o mundo (move os vulcões para a esquerda).
        3. Verifica se algum pássaro passou por um vulcão de forma segura para dar pontos.
        4. Obtém o estado final deste "frame" e emite o broadcast para todos os ecrãs.
        """
        while self.running:
            try:
                time.sleep(self.intervalo)
                
                # 1. ATUALIZA O MUNDO
                lista_jogadores = self.lista_clientes.obter_lista()
                for address in lista_jogadores:
                    self.dados.aplicar_gravidade(str(address)) # Aplica gravidade a cada jogador
                
                self.dados.atualizar_mundo() # Move vulcões
                self.dados.verificar_pontos() # Verifica se alguém pontuou
                
                # 2. VAI BUSCAR O ESTADO E ENVIA
                estado = self.dados.obter_estado()
                self.broadcast_object(estado)
                
            except Exception as e:
                pass