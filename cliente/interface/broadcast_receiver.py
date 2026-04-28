import threading
import os
import json
import cliente

class BroadcastReceiver(threading.Thread):
    """
    Classe responsável por escutar continuamente o servidor em segundo plano (numa thread separada) 
    e renderizar a "interface gráfica" do jogo no terminal. 
    Descodifica o estado do jogo recebido via broadcast e desenha o ecrã em tempo real.
    """

    def __init__(self, connection):
        """
        Inicializa a thread do recetor de broadcast.
        É configurada como 'daemon' para garantir que esta thread em segundo plano 
        é encerrada automaticamente assim que o programa principal (o cliente) fechar.
        
        :param connection: O objeto socket que representa a ligação ao servidor.
        """
        super().__init__(daemon=True)
        self.connection = connection
        self.ativo = True

    def receive_int(self, n_bytes: int) -> int:
        """
        Lê um número inteiro diretamente do socket de rede. 
        É frequentemente utilizado para ler os primeiros bytes do protocolo, 
        que indicam o tamanho exato da mensagem JSON que se segue.
        
        :param n_bytes: A quantidade de bytes a ler do socket.
        :return: O valor numérico descodificado a partir dos bytes recebidos.
        """
        data = self.connection.recv(n_bytes)
        return int.from_bytes(data, byteorder='big', signed=True)

    def receive_object(self):
        """
        Lê e descodifica um objeto JSON enviado pelo servidor.
        A leitura funciona em duas etapas para garantir a integridade dos dados na rede:
        1º - Recebe um inteiro que indica o tamanho total do pacote em bytes.
        2º - Lê exatamente esse número de bytes e converte de volta para um dicionário Python.
        
        :return: Um dicionário contendo os dados do jogo, ou None em caso de falha.
        """
        size = self.receive_int(cliente.INT_SIZE)
        data = self.connection.recv(size)
        return json.loads(data.decode('utf-8'))

    def run(self):
        """
        Ciclo principal do motor gráfico do cliente.
        Enquanto a ligação estiver ativa, fica à escuta de novos pacotes de estado.
        Por cada pacote recebido:
        1. Verifica se a ligação foi recusada pelo servidor (ex: servidor cheio).
        2. Limpa o ecrã do terminal (frame a frame).
        3. Desenha a grelha do jogo, iterando sobre as coordenadas Y (linhas) e X (colunas).
        4. Imprime os vulcões ('X') e o Priolo ('🐦') nas posições correspondentes de cada jogador.
        """
        while self.ativo:
            try:
                estado = self.receive_object() 
                
                if not estado:
                    break
                
                # Trata erros enviados ativamente pelo servidor
                if "acao" in estado and estado["acao"] == "ERRO":
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"\nLIGAÇÃO RECUSADA: {estado['motivo']}")
                    print("Pressiona [ENTER] para sair.")
                    self.ativo = False
                    break
                
                # Limpa o ecrã para desenhar a nova "frame" do jogo
                os.system('cls' if os.name == 'nt' else 'clear')
                print("FLAPPY PRIOLO")
                
                # Renderiza o ecrã para cada jogador ativo na partida
                for pid, info in estado['jogadores'].items(): 
                    
                    print(f"\n[Ecrã de {info['nome']}] Pontos: {info['score']}")
                    print("=" * 51)
                    
                    # Desenha de cima para baixo (Eixo Y)
                    for y in range(10, 100, 10): 
                        linha = ""
                        
                        # Desenha da esquerda para a direita (Eixo X)
                        for x in range(0, 101, 2): 
                            pixel = " "
                            
                            # 1. Verifica se nesta coordenada exata (X, Y) existe um VULCÃO
                            for vulcao in info['vulcoes']:
                                na_coluna_do_vulcao = abs(vulcao['x'] - x) <= 2
                                desenha_vulcao = y < vulcao['abertura_y'] - 15 or y > vulcao['abertura_y'] + 15
                                
                                if na_coluna_do_vulcao and desenha_vulcao:
                                    pixel = "X" 
                            
                            # 2. Verifica se nesta coordenada exata (X, Y) está o PÁSSARO
                            no_x_do_passaro = (info['x'] == x)
                            no_y_do_passaro = abs(info['y'] - y) <= 4
                            
                            if no_x_do_passaro and no_y_do_passaro:
                                pixel = "🐦" 
                                    
                            # Adiciona o pixel (' ', 'X', ou '🐦') à linha atual
                            linha += pixel 
                            
                        # Imprime a linha completa no terminal
                        print(linha)
                    print("=" * 51) 
                    
                # Mensagem final afixada no fundo do terminal
                print("\nEscreve 'f' e [ENTER] para saltar!")
                    
            except Exception:
                # Se o servidor for desligado ou houver quebra de rede, termina
                self.ativo = False
                break