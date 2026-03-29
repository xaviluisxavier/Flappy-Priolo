import threading
import socket
from comunicacao.sockets_util import receive_object, send_object

class ProcessaCliente(threading.Thread):
    def __init__(self, connection, address, dados, player_id):
        super().__init__()
        self.connection = connection
        self.address = address
        self.dados = dados 
        self.player_id = player_id

    def run(self):
        print(f"[{self.address}] Thread iniciada para o Jogador {self.player_id}.")
        ativo = True
        
        try:
           # Recebe o nome do jogador
            msg_inicial = receive_object(self.connection)
            if msg_inicial and msg_inicial.get("acao") == "ENTRAR":
                nome = msg_inicial.get("nome", f"Priolo_{self.player_id}")
                # Tenta adicionar. Se a base de dados devolver False, é porque está cheio!
                conseguiu_entrar = self.dados.adicionar_jogador(self.player_id, nome)
                
                if conseguiu_entrar:
                    print(f"\n[+] {self.address} - O jogador '{nome}' ENTROU no jogo!")
                    print(f"ESTADO GLOBAL: {self.dados.obter_estado()}\n")
                else:
                    print(f"\n[!] {self.address} - O jogador '{nome}' tentou entrar, mas o SERVIDOR ESTÁ CHEIO!")
                    ativo = False 
            else:
                ativo = False

            self.connection.settimeout(1.0) 

            while ativo:
                try:
                    pedido = receive_object(self.connection)
                    
                    if not pedido or pedido.get("acao") == "SAIR":
                        #O servidor regista o pedido de saída
                        print(f"[-] {self.address} - O jogador '{nome}' (ID: {self.player_id}) saiu.")
                        ativo = False
                        break
                    
                    if pedido.get("acao") == "FLAP":
                        print(f"[AÇÃO] O jogador '{nome}' (ID: {self.player_id}) voou")
                        self.dados.atualizar_posicao(self.player_id, "FLAP")

                except socket.timeout:
                    morreu = self.dados.aplicar_gravidade(self.player_id)
                    if morreu:
                        print(f"[!] O jogador '{nome}' (ID: {self.player_id}) morreu!")
                
                estado_global = self.dados.obter_estado()
                send_object(self.connection, estado_global)
                
        except Exception as e:
            if ativo: print(f"[{self.address}] Erro: {e}")
        finally:
            self.dados.remover_jogador(self.player_id)
            print(f"Ligação fechada para o Jogador {self.player_id}.")            
            print(f"ESTADO: {self.dados.obter_estado()}\n")
            self.connection.close()
