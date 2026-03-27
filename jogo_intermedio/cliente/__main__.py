import sys
from comunicacao.cliente_jogo import ClientePriolo

if __name__ == '__main__':
    # Permite passar o IP do servidor no terminal. Se não passares nada, usa localhost.
    ip_servidor = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
    cliente = ClientePriolo(host=ip_servidor)
    cliente.jogar()