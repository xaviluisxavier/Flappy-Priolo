import socket
import servidor
from servidor.maquina.processa_cliente import ProcessaCliente
from servidor.maquina.lista_clientes import ListaClientes
from servidor.maquina.broadcast_emissor import ThreadBroadcast
from servidor.maquina.estrutura_dados import DadosJogo

class Maquina:
    """
    Classe principal do servidor do jogo Flappy Priolo.
    É responsável por configurar a rede, gerir o estado global do jogo e 
    coordenar a comunicação com múltiplos clientes.
    """

    def __init__(self):
        """
        Inicializa o servidor, configurando os sockets de rede e os componentes do jogo.
        Prepara a estrutura de dados, a lista de clientes ativos e inicia a 
        thread de broadcast.
        """
        self.s = socket.socket()
        self.s.bind(('', servidor.PORT))
        
        self.dados = DadosJogo()
        self.clientes = ListaClientes()
        
        # O intervalo é 0.03 segundos para garantir a fluidez do jogo
        self.broadcast = ThreadBroadcast(self.clientes, self.dados, intervalo=0.03)
        self.broadcast.start()

    def execute(self):
        """
        Inicia o ciclo principal de execução do servidor.
        Coloca o socket preparado e aceita novas ligações. Para cada cliente
        que se liga, adiciona-o à lista de clientes ativos e cria uma nova thread
        dedicada para processar os seus comandos de forma independente.
        """
        self.s.listen(5) # O jogo permite um máximo de 5 jogadores em simultâneo
        print("Servidor Flappy Priolo a correr na porta " + str(servidor.PORT))
        
        while True: 
                connection, address = self.s.accept()
                print("Cliente", address, "ligou-se!")
                    
                self.clientes.adicionar(address, connection)
                processo_cliente = ProcessaCliente(connection, address, self.dados, self.clientes)
                processo_cliente.start()

   