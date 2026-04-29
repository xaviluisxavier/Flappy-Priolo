import threading
import servidor

class ProcessaCliente(threading.Thread):
    """
    Classe responsável por gerir a ligação de um cliente específico numa thread separada.
    Processa a entrada do jogador no jogo e escuta os seus comandos em tempo real.
    """
    
    def __init__(self, connection, address, dados, clientes):
        """
        Inicializa a thread de processamento do cliente.
        
        :param connection: O objeto socket que representa a ligação com o cliente.
        :param address: O endereço (IP, porta) do cliente ligado.
        :param dados: A estrutura de dados partilhada que contém o estado atual do jogo.
        :param clientes: A lista partilhada que gere todos os clientes ligados ao servidor.
        """
        super().__init__()
        self.connection = connection
        self.address = address
        self.dados = dados
        self.clientes = clientes

    def receive_str(self, connection, n_bytes: int) -> str:
        """
        Recebe e descodifica uma string enviada pelo cliente através da rede.
        
        :param connection: A ligação socket de onde os dados serão lidos.
        :param n_bytes: O número máximo de bytes a receber nesta operação.
        :return: A string descodificada, limpa de espaços em branco e quebras de linha nas extremidades.
        """
        data = connection.recv(n_bytes)
        return data.decode().strip()

    def send_object(self, connection, obj):
        """
        Codifica um objeto Python (dicionário) em formato JSON e envia-o para o cliente.
        O envio é feito em duas fases: primeiro envia o tamanho dos dados, depois os dados em si.
        
        :param connection: A ligação socket para onde o objeto será enviado.
        :param obj: O dicionário com o estado ou as informações a serem enviadas.
        """
        import json
        data = json.dumps(obj).encode('utf-8')
        size = len(data)
        connection.send(size.to_bytes(servidor.INT_SIZE, byteorder="big", signed=True))
        connection.send(data)

    def run(self):
        """
        Método principal executado quando a thread do cliente arranca.
        O fluxo de execução é o seguinte:
        1. Espera que o cliente envie o seu nome.
        2. Tenta adicionar o jogador ao jogo (falha se o servidor estiver cheio ou o nome já existir).
        3. Entra num ciclo infinito à espera das ações do jogador (ex: "FLAP" para saltar).
        4. Garante, através do bloco 'finally', que o jogador é removido da lista de clientes 
           e do jogo quando se desconecta, evitando jogadores "fantasmas".
        """
        print(self.address, "Thread iniciada")
        player_id = str(self.address)
        
        try:
            # 1. Espera pelo nome do jogador (primeira mensagem)
            nome = self.receive_str(self.connection, 1024)
            sucesso, msg = self.dados.adicionar_jogador(player_id, nome)
            
            if not sucesso:
                print(f"Erro ao adicionar jogador: {msg}")
                self.send_object(self.connection, {"acao": "ERRO", "motivo": msg})
                return # Termina a thread se estiver cheio ou nome repetido
            
            # 2. Fica à espera de ações do jogador
            while True:
                acao = self.receive_str(self.connection, 1024)
                if not acao:
                    break # Cliente desconectou
                    
                if acao == "FLAP":
                    self.dados.atualizar_posicao(player_id, "FLAP")
                elif acao == "END":
                    break
                    
        except Exception:
            pass
        finally:
            print(self.address, "Thread terminada")
            self.dados.remover_jogador(player_id)
            self.clientes.remover(self.address)
            self.connection.close()