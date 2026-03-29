import socket
import threading
import sys
import os
from comunicacao.sockets_util import receive_object, send_object

class ClientePriolo:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.ativo = True

    def ouvir_servidor(self, client_socket):
        """Esta função corre em SEGUNDO PLANO (Thread) a receber os frames do servidor."""
        while self.ativo:
            try:
                estado = receive_object(client_socket)
                if not estado:
                    self.ativo = False
                    break
                
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("JOGO EM EXECUÇÃO")
                for pid, info in estado.items():
                    altura_visual = max(0, int(info['y'] // 10)) # Calcula o espaço
                    espaco = " " * altura_visual
                    print(f"[{info['nome']}] Score: {info['score']} | Altura: {info['y']}")
                    print(f"{espaco} 🐦")
                    print("-" * 40)
                    
                print("\nEscreve 'f' e [ENTER] para saltar. Ou 'sair' para fechar.")
            except:
                self.ativo = False
                break

    def jogar(self):
        nome = input("Introduz o nome do teu Priolo: ").strip()
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            client_socket.connect((self.host, self.port))
            send_object(client_socket, {"acao": "ENTRAR", "nome": nome})
            
            # Arranca a Thread que vai imprimir o ecrã constantemente
            thread_rececao = threading.Thread(target=self.ouvir_servidor, args=(client_socket,))
            thread_rececao.start()

            # O ciclo principal serve APENAS para ler o que o utilizador escreve
            while self.ativo:
                comando = input().strip().lower()
                
                if comando == "sair":
                    send_object(client_socket, {"acao": "SAIR"})
                    self.ativo = False
                    break
                elif comando == "f":
                    send_object(client_socket, {"acao": "FLAP"})

        except Exception as e:
            print(f"Erro ao ligar ao servidor: {e}")
        finally:
            self.ativo = False
            client_socket.close()

if __name__ == '__main__':
    ip = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
    cliente = ClientePriolo(host=ip)
    cliente.jogar()
