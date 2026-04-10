import threading
from comunicacao.sockets_util import receive_object

class ProcessaCliente(threading.Thread):
    def __init__(self, connection, address, dados, lista_clientes, player_id):
        """Inicializa a thread para processar um cliente, armazenando a conexão, endereço, dados do jogo, lista de clientes e ID do jogador."""
        super().__init__(daemon=True)
        self.connection = connection
        self.address = address
        self.dados = dados 
        self.lista_clientes = lista_clientes
        self.player_id = player_id

    def run(self):
        """Gerencia a comunicação com um cliente específico, processando suas ações e atualizando o estado do jogo."""
        try:
            msg_inicial = receive_object(self.connection)
            if msg_inicial and msg_inicial.get("acao") == "ENTRAR":
                nome = msg_inicial.get("nome", f"Priolo_{self.player_id}")
                
                # Tenta adicionar na base de dados
                sucesso, motivo = self.dados.adicionar_jogador(self.player_id, nome)
                if sucesso:
                    self.lista_clientes.adicionar(self.player_id, self.connection) # Adiciona à rede
                    print(f"[+] {nome} entrou!")
                else:
                    print(f"[!] Entrada recusada: {motivo}")
                    return # Sai da thread
            
            # Fica num loop apenas a ler as ações do jogador
            while True:
                pedido = receive_object(self.connection)
                if not pedido or pedido.get("acao") == "SAIR":
                    break
                if pedido.get("acao") == "FLAP":
                    self.dados.atualizar_posicao(self.player_id, "FLAP")
                    
        except Exception:
            pass # Ignora erros de ligação
        finally:
            self.dados.remover_jogador(self.player_id)
            self.lista_clientes.remover(self.player_id)
            self.connection.close()
