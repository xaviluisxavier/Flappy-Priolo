import threading
from typing import Dict, Tuple
import socket

class ListaClientes:
    """
    Classe responsável por gerir a lista de clientes (jogadores) ligados ao servidor.
    Utiliza mecanismos de sincronização (Locks) para garantir que a adição, remoção 
    e leitura dos clientes é feita de forma segura num ambiente multi-thread (Thread-safe).
    """

    def __init__(self):
        """
        Inicializa a estrutura de dados para o armazenamento dos clientes.
        Cria o dicionário de clientes, o lock e o contador.
        """
        self._clientes: Dict[Tuple[str, int], socket.socket] = {}
        self._lock = threading.Lock()
        self._nr_clientes = 0

    def adicionar(self, address: Tuple[str, int], connection: socket.socket) -> None:
        """
        Adiciona um novo cliente à lista de clientes ativos de forma segura.
        
        :param address: O endereço do cliente (IP, porta) que servirá como chave única.
        :param connection: O objeto socket que representa a ligação ativa com o cliente.
        """
        with self._lock:
            self._clientes[address] = connection
            self._nr_clientes += 1
            print("Cliente ", address," adicionado ao dicionário!")
            print("Nr. de clientes:", self._nr_clientes)

    def remover(self, addr: Tuple[str, int]) -> None:
        """
        Remove um cliente da lista de clientes ativos de forma segura, 
        caso este esteja registado.
        
        :param addr: O endereço do cliente (IP, porta) a ser removido.
        """
        with self._lock:
            if addr in self._clientes:
                del self._clientes[addr]
                self._nr_clientes -= 1

    def obter_lista(self) -> Dict[Tuple[str, int], socket.socket]:
        """
        Retorna uma cópia da lista de clientes ativos.
        :return: Um dicionário com os endereços e respetivas ligações (sockets) dos clientes.
        """
        with self._lock:
            return self._clientes.copy()

    def obter_nr_clientes(self) -> int:
        """
        Retorna o número total de clientes atualmente ligados ao servidor.
        
        :return: O número inteiro correspondente à quantidade de clientes ativos.
        """
        return self._nr_clientes