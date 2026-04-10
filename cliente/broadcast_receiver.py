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
                
                # Para CADA jogador
                for pid, info in estado['jogadores'].items(): 
                    
                    print(f"\n[Ecrã de {info['nome']}] Pontos: {info['score']}")
                    print("=" * 51) 
                    
                    # Desenha o jogo
                    for y in range(10, 100, 10): 
                        linha = ""
                        for x in range(0, 101, 2): 
                            char = " " 
                            
                            # Desenha os vulcões
                            for v in estado['vulcoes']:
                                if abs(v['x'] - x) <= 2:
                                    if y < v['abertura_y'] - 15 or y > v['abertura_y'] + 15:
                                        char = "X" 
                            
                            # Desenha o pássaro
                            if info['x'] == x and abs(info['y'] - y) <= 4:
                                char = "🐦" 
                                    
                            linha += char
                        print(linha)
                        
                    print("=" * 51)
                    
                # Mensagem final no fundo do terminal
                print("\nEscreve 'f' e [ENTER] para saltar!")
                    
            except Exception:
                self.ativo = False
                break
