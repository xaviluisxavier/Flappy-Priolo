import socket
from comunicacao.sockets_util import send_object
from cliente.broadcast_receiver import BroadcastReceiver

class ClientePriolo:
    def jogar(self, host='127.0.0.1', port=5000):
        """Inicia o cliente, conecta ao servidor e gerencia a interação do jogador."""
        nome = input("Introduz o nome do teu Priolo: ").strip()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            client_socket.connect((host, port))
            send_object(client_socket, {"acao": "ENTRAR", "nome": nome})
            
            # Inicia o ficheiro
            receiver = BroadcastReceiver(client_socket)
            receiver.start()

            # Ciclo que envia ações
            while receiver.ativo:
                comando = input().strip().lower()
                if comando == "sair":
                    send_object(client_socket, {"acao": "SAIR"})
                    break
                elif comando == "f":
                    send_object(client_socket, {"acao": "FLAP"})

        except Exception as e:
            print(f"Erro: {e}")
        finally:
            client_socket.close()

if __name__ == '__main__':
    cliente = ClientePriolo()
    cliente.jogar()
