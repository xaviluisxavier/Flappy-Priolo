import threading
import json
import cliente

class BroadcastReceiver(threading.Thread):
    """
    Classe responsável APENAS por ouvir o servidor em segundo plano.
    Quando recebe um novo estado, guarda-o na variável 'estado_atual' 
    para que o Pygame a possa ler e desenhar no ecrã.
    """

    def __init__(self, connection):
        super().__init__(daemon=True)
        self.connection = connection
        self.ativo = True
        self.estado_atual = None 

    def receive_int(self, n_bytes: int) -> int:
        data = self.connection.recv(n_bytes)
        return int.from_bytes(data, byteorder='big', signed=True)

    def receive_object(self):
        size = self.receive_int(cliente.INT_SIZE)
        data = self.connection.recv(size)
        return json.loads(data.decode('utf-8'))

    def run(self):
        while self.ativo:
            try:
                estado = self.receive_object() 
                
                if not estado:
                    break

                self.estado_atual = estado
                
                if "acao" in estado and estado["acao"] == "ERRO":
                    self.ativo = False
                    break
                    
            except Exception:
                self.ativo = False
                break