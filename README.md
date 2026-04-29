# Relatório Intermédio: Flappy Priolo
**GRUPO:** G11
**GITHUB:** https://github.com/xaviluisxavier/Flappy-Priolo/

## 1. O que conseguimos realizar
Até ao momento, concluímos com sucesso a base arquitetural do jogo e a mecânica central de funcionamento:
* **Motor Multiplayer:** O "Flappy Priolo" já é um jogo multiplayer distribuído funcional.
* **Estrutura de Dados Centralizada:** A base de dados do jogo encontra-se na componente do servidor, gerida de forma centralizada e Thread-Safe (usando `threading.Lock()` para evitar condições de corrida entre múltiplas threads).
* **Mecânicas Base:** A física e as regras foram implementadas com sucesso. A gravidade faz o pássaro cair, o jogador ganha 1 ponto ao ultrapassar um vulcão e o jogo termina se colidir ou cair no chão.
* **Visualização no Terminal:** O jogo é atualmente renderizado no terminal em modo Split-Screen (ecrã dividido), permitindo que múltiplos jogadores partilhem o mesmo servidor enquanto visualizam os seus respetivos ecrãs em tempo real.

## 2. Objetivos que faltam
Para a fase final do projeto, pretendemos evoluir a arquitetura atual para uma versão mais robusta e visualmente apelativa:
* **Transição para Interface Gráfica:** Substituir a renderização em terminal (Split-Screen) por um cliente gráfico desenvolvido em *Pygame*.
* **Motor de Jogo em Tempo Real:** Alterar a lógica do servidor para um simulador contínuo, movendo-nos de uma arquitetura estática para uma que envia *frames* fluidas constantemente.
* **Aprimoramento da Física e Dificuldade:** Implementar velocidade vetorial (`vel_y`) e aumentar a velocidade de movimentação do mundo de forma dinâmica com base no *score* dos jogadores.

## 3. Descrição dos Protocolos de Comunicação
A interação entre as diferentes partes baseia-se numa arquitetura Cliente-Servidor com Broadcast, utilizando o pacote socket e threading do Python. O protocolo obedece aos seguintes princípios:

### 3.1. Formato das Mensagens
* **Envio de Comandos (Cliente -> Servidor):** Utiliza strings de tamanho fixo de 9 bytes (COMMAND_SIZE = 9). Os jogadores enviam estritamente intenções, sem nunca enviar as suas coordenadas. Exemplo de intenções enviadas: `{"acao": "ENTRAR", "nome": "Luis"}`, `{"acao": "FLAP"}` e `{"acao": "SAIR"}`.
* **Comunicação de Estado (Servidor -> Cliente):** Assenta na troca de dicionários JSON. Antes de o JSON ser transmitido, o emissor envia um bloco inteiro de 8 bytes indicando o tamanho exato da mensagem. O recetor lê este tamanho primeiro, evitando que as mensagens TCP cheguem coladas ou fragmentadas.

### 3.2. Arquitetura de Threads no Servidor
O servidor separa completamente a receção de dados do envio de dados, utilizando duas threads distintas:
* **Thread ProcessaCliente (Receção Passiva):** Por cada jogador que entra, é criada uma thread dedicada a ouvir a rede. Esta thread apenas atualiza a estrutura de dados central com a intenção recebida e não responde diretamente ao cliente.
* **ThreadBroadcast (Emissão Contínua):** Uma única thread corre em background e, periodicamente, processa a física do jogo e envia o estado global atualizado para todos os clientes registados. Em vez de devolver respostas individuais, o servidor envia de forma contínua a fotografia completa do estado global do jogo. A informação inclui o dicionário completo de jogadores com nomes, coordenadas Y, pontos e a lista privada de vulcões.
