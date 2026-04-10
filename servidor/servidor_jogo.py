import socket

from servidor.dados.estrutura_dados import DadosJogo
from servidor.lista_clientes import ListaClientes
from servidor.processa_cliente import ProcessaCliente
from servidor.broadcast_emissor import ThreadBroadcast

class ServidorPriolo:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.dados = DadosJogo()
        self.contador_id = 0
        
        self.lista_clientes = ListaClientes() 
        self.broadcast = ThreadBroadcast(self.lista_clientes, self.dados, intervalo=0.2)
        self.broadcast.start()

    def start_server(self):
        """Inicia o servidor, aceita conexões e cria threads para cada cliente."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Servidor em {self.host}:{self.port}...")

        while True:
            conn, addr = server_socket.accept()
            self.contador_id += 1 
            id_atual = self.contador_id 
            
            print(f"Nova ligação de {addr} atribuída ao ID: {id_atual}")
            
            processo = ProcessaCliente(conn, addr, self.dados, self.lista_clientes, id_atual)
            processo.start()
