import socket
from dados.estrutura_dados import DadosJogo
from comunicacao.processa_cliente import ProcessaCliente

class ServidorPriolo:
    def __init__(self):
        self.dados = DadosJogo() # Instância ÚNICA partilhada por todas as threads
        self.contador_id = 1

    def start_server(self, host='127.0.0.1', port=5000):
        # Criação do Socket TCP IPv4
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5) # Suporta até 5 jogadores em simultâneo
        
        print(f"=== SERVIDOR FLAPPY PRIOLO ===")
        print(f"Ativo em {host}:{port}. À espera de ligações...")

        try:
            while True:
                # Aceita a ligação de um novo cliente
                conn, addr = server_socket.accept()
                print(f"\nNova ligação estabelecida com {addr}")
                
                # Arranca uma Thread para lidar com o jogador
                processo = ProcessaCliente(conn, addr, self.dados, self.contador_id)
                processo.start()
                
                self.contador_id += 1
        except KeyboardInterrupt:
            print("\nServidor encerrado manualmente.")
        finally:
            server_socket.close()

if __name__ == '__main__':
    servidor = ServidorPriolo()
    servidor.start_server()