import threading
import os
from comunicacao.sockets_util import receive_object

class BroadcastReceiver(threading.Thread):
    def __init__(self, connection):
        """Inicializa a thread de broadcast receiver, armazenando a conexão e definindo a thread como daemon."""
        super().__init__(daemon=True)
        self.connection = connection
        self.ativo = True

    def run(self):
        """Recebe os estados do jogo do servidor e os imprime no terminal."""
        while self.ativo:
            try:
                estado = receive_object(self.connection)
                if not estado:
                    break
                
                if "acao" in estado and estado["acao"] == "ERRO":
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(f"\nLIGAÇÃO RECUSADA: {estado['motivo']}")
                    print("Pressiona [ENTER] para sair.")
                    self.ativo = False
                    break
                
                os.system('cls' if os.name == 'nt' else 'clear')
                print("FLAPPY PRIOLO")
                
               # Para CADA jogador no dicionário
                for pid, info in estado['jogadores'].items(): 
                    
                    print(f"\n[Ecrã de {info['nome']}] Pontos: {info['score']}")
                    print("=" * 51)
                    
                    # ecrã de cima para baixo (Eixo Y)
                    for y in range(10, 100, 10): 
                        linha = ""
                        
                        # linha da esquerda para a direita (Eixo X)
                        for x in range(0, 101, 2): 
                            pixel = " "
                            
                            # 1. Verifica se nesta coordenada exata (X, Y) existe um VULCÃO
                            for vulcao in estado['vulcoes']:
                                na_coluna_do_vulcao = abs(vulcao['x'] - x) <= 2
                                bate_no_vulcao = y < vulcao['abertura_y'] - 15 or y > vulcao['abertura_y'] + 15
                                
                                if na_coluna_do_vulcao and bate_no_vulcao:
                                    pixel = "X" 
                            
                            # 2. Verifica se nesta coordenada exata (X, Y) está o PÁSSARO
                            no_x_do_passaro = (info['x'] == x)
                            no_y_do_passaro = abs(info['y'] - y) <= 4
                            
                            if no_x_do_passaro and no_y_do_passaro:
                                pixel = "🐦" 
                                    
                            # Adiciona o pixel (espaço, 'X' ou '🐦') à linha
                            linha += pixel 
                            
                        # Imprime a linha no terminal
                        print(linha)
                    print("=" * 51) 
                    
                # Mensagem final no fundo do terminal
                print("\nEscreve 'f' e [ENTER] para saltar!")
                    
            except Exception:
                self.ativo = False
                break