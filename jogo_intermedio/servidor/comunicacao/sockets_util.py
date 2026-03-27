import json

INT_SIZE = 4

def receive_int(connection, size):
    """Função auxiliar para receber o tamanho do objeto."""
    data = connection.recv(size)
    if not data: return 0
    return int.from_bytes(data, byteorder='big')

def receive_object(connection):
    """1º: lê o tamanho, 2º: lê os dados em JSON e descodifica."""
    size = receive_int(connection, INT_SIZE)
    if size == 0: return None
    data = connection.recv(size)
    return json.loads(data.decode('utf-8'))

def send_int(connection, value, size):
    """Função auxiliar para enviar o tamanho do objeto."""
    connection.send(value.to_bytes(size, byteorder='big'))

def send_object(connection, obj):
    """1º: envia o tamanho, 2º: envia os dados serializados em JSON."""
    data = json.dumps(obj).encode('utf-8')
    size = len(data)
    send_int(connection, size, INT_SIZE)
    connection.send(data)