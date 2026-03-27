"""
Servidor Multijogador - Flappy Priolo
Este script gere as ligações de rede dos vários jogadores usando TCP Sockets.
Mantém o estado de todos os jogadores sincronizado, recebendo as posições de cada um
e retransmitindo a informação global de volta para todos os clientes ligados.
"""

import socket
import threading
import pickle

# --- Configurações de Conexão ---
SERVER = "26.195.177.217" 
PORT = 5555
MAX_PLAYERS = 3

# Inicializa o socket IPv4 (AF_INET) e protocolo TCP (SOCK_STREAM)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((SERVER, PORT))
    s.listen(MAX_PLAYERS)
except socket.error as e:
    print(f"Error starting server: {e}")
    exit()

print("Server started. Waiting for a connection...")

# Dicionário global para armazenar os dados de todos os jogadores ativos.
# Estrutura esperada: { player_id: {'y': Y_POS, 'score': SCORE, 'game_over': BOOL, 'name': STRING} }
players_data = {} 
player_count = 0

def threaded_client(conn, player_id):
    """
    Função executada numa thread (linha de execução) separada para cada jogador ligado.
    Gere a receção e o envio contínuo de dados enquanto o jogador estiver online, 
    sem bloquear o resto do servidor.
    
    Args:
        conn (socket.socket): O objeto de ligação do jogador.
        player_id (int): O identificador único atribuído a este jogador.
    """
    global player_count

    players_data[player_id] = {'y': 300, 'score': 0, 'game_over': False, 'name': f"P{player_id}"}
    
    conn.send(str.encode(str(player_id))) 
    
    while True:
        try:
            raw_data = conn.recv(2048)
            
            if not raw_data:
                break
    
            data = pickle.loads(raw_data)
            players_data[player_id] = data
            conn.sendall(pickle.dumps(players_data))

        except Exception:
            break


    print(f"Player {player_id} disconnected.")
    
    if player_id in players_data:
        del players_data[player_id] 
    player_count -= 1
    conn.close()

# --- Ciclo Principal do Servidor ---
while True:
    conn, addr = s.accept()
    
    if player_count < MAX_PLAYERS:
        print(f"Connected to: {addr} (Player {player_count})")
        threading.Thread(target=threaded_client, args=(conn, player_count)).start()
        player_count += 1
    else:
        print(f"Connection from {addr} refused. Maximum players reached.")
        conn.send(str.encode("Server full."))
        conn.close()