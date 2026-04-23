import socket
import cliente
from cliente.interface.broadcast_receiver import BroadcastReceiver

class Interface:
    """
    Classe responsável por gerir a interação direta do jogador com o jogo (lado do cliente).
    Estabelece a ligação com o servidor, recolhe os comandos do teclado e inicia a thread 
    responsável por desenhar o ecrã em tempo real.
    """

    def __init__(self):
        """
        Inicializa a interface do cliente.
        Cria o socket de rede e estabelece imediatamente a ligação ao servidor 
        utilizando o endereço (IP) e a porta definidos no ficheiro de configurações.
        """
        self.connection = socket.socket()
        self.connection.connect((cliente.SERVER_ADDRESS, cliente.PORT))

    def send_str(self, connect, value: str) -> None:
        """
        Codifica uma string (texto) em bytes e envia-a através da rede.
        
        :param connect: O objeto socket que representa a ligação ao servidor.
        :param value: A string a ser enviada (ex: o nome do jogador ou o comando de salto).
        """
        connect.send(value.encode())

    def execute(self):
        """
        Inicia o ciclo principal de execução do cliente.
        O fluxo de interação funciona da seguinte forma:
        1. Pede o nome do jogador e envia-o como primeira mensagem para o servidor.
        2. Instancia e arranca o BroadcastReceiver (thread que vai ouvir o estado do 
           jogo e desenhar a grelha/ecrã no terminal).
        3. Entra num ciclo infinito à espera de inputs do utilizador:
           - 'f' (seguido de ENTER) envia o comando para o pássaro saltar ("FLAP").
           - '.' (seguido de ENTER) envia o comando de paragem ("END") e desliga o jogo.
        """
        # 1. Pede o nome
        nome = input("Bem-vindo ao Flappy Priolo! Qual é o teu nome? ")
        self.send_str(self.connection, nome) # Envia o nome para o servidor
        
        # 2. Inicia a thread que desenha o ecrã
        receiver = BroadcastReceiver(self.connection)
        receiver.start()

        # 3. Ciclo infinito à espera que o jogador carregue em 'f'
        while True:
            try:
                comando = input() # Fica à espera do "f" e Enter
                
                if comando.lower() == 'f':
                    self.send_str(self.connection, "FLAP")
                    
                elif comando.lower() == '.':
                    self.send_str(self.connection, "END")
                    break
                    
            except KeyboardInterrupt:
                # Permite fechar o jogo com Ctrl+C
                break
                
        self.connection.close()