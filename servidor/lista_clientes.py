import threading

class ListaClientes:
    def __init__(self):
        self._clientes = {} 
        self._lock = threading.Lock()

    def adicionar(self, player_id, connection):
        """Adiciona um cliente à lista de clientes conectados."""
        with self._lock:
            self._clientes[player_id] = connection
            print(f"[!] Jogador {player_id} adicionado. Total: {len(self._clientes)}")

    def remover(self, player_id):
        """Remove um cliente da lista de clientes conectados."""
        with self._lock:
            if player_id in self._clientes:
                del self._clientes[player_id]
                print(f"[!] Jogador {player_id} removido. Total: {len(self._clientes)}")

    def obter_lista(self):
        """Retorna uma cópia da lista de clientes para evitar problemas de concorrência."""
        with self._lock:
            return self._clientes.copy()
