import socket
import os
import cliente
from cliente.interface.broadcast_receiver import BroadcastReceiver

class Interface:
    """
    Classe responsável por gerir a interação com o jogador, recolher inputs
    e renderizar o ecrã do jogo.
    """

    def __init__(self):
        self.connection = socket.socket()
        self.connection.connect((cliente.SERVER_ADDRESS, cliente.PORT))

    def send_str(self, connect, value: str) -> None:
        connect.send(value.encode())

    def atualizar_ecra(self, estado):
        """
        Este método é chamado pelo BroadcastReceiver sempre que chega um novo estado.
        É aqui que fica toda a "Interface Gráfica" (os prints).
        """
        # Trata erros
        if "acao" in estado and estado["acao"] == "ERRO":
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"\nLIGAÇÃO RECUSADA: {estado['motivo']}")
            print("Pressiona [ENTER] para sair.")
            return

        # Limpa e desenha
        os.system('cls' if os.name == 'nt' else 'clear')
        print("FLAPPY PRIOLO")
        
        for pid, info in estado['jogadores'].items(): 
            print(f"\n[Ecrã de {info['nome']}] Pontos: {info['score']}")
            print("=" * 51)
            
            for y in range(10, 100, 10): 
                linha = ""
                for x in range(0, 101, 2): 
                    pixel = " "
                    
                    # Vulcões
                    for vulcao in info['vulcoes']:
                        na_coluna = abs(vulcao['x'] - x) <= 2
                        desenha_vulcao = y < vulcao['abertura_y'] - 15 or y > vulcao['abertura_y'] + 15
                        if na_coluna and desenha_vulcao:
                            pixel = "X" 
                    
                    # Pássaro
                    no_x = (info['x'] == x)
                    no_y = abs(info['y'] - y) <= 4
                    if no_x and no_y:
                        pixel = "🐦" 
                            
                    linha += pixel 
                print(linha)
            print("=" * 51) 
            
        print("\nEscreve 'f' e [ENTER] para saltar!")

    def execute(self):
        nome = input("Bem-vindo ao Flappy Priolo! Qual é o teu nome? ")
        self.send_str(self.connection, nome)
        
        # Inicia o receiver, passando 'self' para ele conhecer a interface
        receiver = BroadcastReceiver(self.connection, self)
        receiver.start()

        # Ciclo de jogo
        while True:
            try:
                comando = input() 
                
                if comando.lower() == 'f':
                    self.send_str(self.connection, "FLAP")
                elif comando.lower() == '.':
                    self.send_str(self.connection, "END")
                    break
                    
            except KeyboardInterrupt:
                break
                
        self.connection.close()