# Documento de Suporte: Descrição, Estrutura e Protocolos do Jogo (Flappy Priolo)
**GRUPO:** G11

## 1. Descrição do Jogo
O "Flappy Priolo" é um jogo multiplayer distribuído com uma mecânica de sobrevivência e precisão. 
**Objetivo:** O objetivo é controlar a personagem (o pássaro Priolo) e passar pelo maior número possível de obstáculos (vulcões) sem ir contra nenhum deles.

**Regras e Pontuação:**
* O jogador interage para fazer o pássaro subir (Flap).
* Sem interação do jogador, a gravidade fará o pássaro cair.
* O jogador ganha 1 ponto assim que ultrapassa a coordenada horizontal de um vulcão com sucesso.
* O jogo termina se o pássaro colidir com um dos vulcões ou cair no chão ou bater no teto.

**Visualização:** Embora originalmente o jogo fosse renderizado no terminal em modo Split-Screen, o projeto evoluiu. Agora conta com uma **Interface Gráfica renderizada em Pygame**, que permite visualização suave, animações e interpolação de movimento a rodar em Tempo Real.

## 2. A Estrutura de Dados (Estado do Jogo)
A base de dados do jogo encontra-se na componente do servidor, gerida de forma centralizada e Thread-Safe (usando `threading.Lock()` para evitar condições de corrida entre múltiplas threads). A estrutura divide-se em duas componentes principais:

### 2.1. Dicionário de Jogadores (`jogadores`)
Esta estrutura armazena o estado individual e o "mundo" de cada jogador, utilizando o ID da ligação como chave. Por cada ID, guarda-se um dicionário com:
* **nome:** O nickname introduzido.
* **x:** A posição horizontal do jogador.
* **y:** A posição vertical do jogador no ecrã.
* **score:** A pontuação atual.
* **vulcoes:** Uma lista privada de obstáculos gerada exclusivamente para cada jogador. Regista a zona de `abertura_y` (onde os jogadores podem passar com segurança e pontuar). *(Atualização: Cada vulcão gerado recebe agora também um `id` único, o que permite à interface gráfica identificar cada obstáculo e animá-lo de forma fluida).*
* **vel_y:** *(Novo Parâmetro)* A velocidade vertical instantânea da personagem no eixo Y.

### 2.2. Lista de Clientes Ativos (`ListaClientes`)
Um dicionário independente, também protegido por Locks, que armazena os sockets (ligações TCP) de todos os jogadores atualmente ligados, sendo essencial para o envio de mensagens em Broadcast.

## 3. Parâmetros do Jogo
* **Gravidade:** O valor que puxa a posição do jogador para baixo regularmente.
* **Velocidade dos vulcões:**velocidade de deslocação dos vulcões ao longo do eixo horizontal. *(Atualização: O jogo escala agora a dificuldade dinamicamente, aumentando progressivamente esta velocidade consoante o `score` alcançado).*
* **Distância entre vulcões:** O espaço necessário para desencadear a geração de um novo obstáculo.

## 4. Protocolos de Comunicação
A interação entre as diferentes partes baseia-se numa arquitetura Cliente-Servidor com Broadcast, utilizando o pacote socket e threading do Python. O protocolo obedece aos seguintes princípios:

### Empacotamento e Comandos
A comunicação de envio de comandos (Cliente -> Servidor) utiliza strings de tamanho fixo de 9 bytes. Já a comunicação de estado (Servidor -> Cliente) assenta na troca de dicionários JSON. Antes de o JSON ser transmitido, o emissor envia um bloco inteiro de 8 bytes indicando o tamanho exato da mensagem. O recetor lê este tamanho primeiro, evitando que as mensagens TCP cheguem coladas ou fragmentadas.

### Arquitetura de Threads no Servidor
O servidor separa completamente a receção de dados do envio de dados, utilizando duas threads distintas:
* **1. Thread ProcessaCliente (Receção Passiva):** Por cada jogador que entra, é criada uma thread dedicada a ouvir a rede. O cliente nunca envia as suas coordenadas, apenas as intenções geradas pelo teclado. A thread recebe a intenção, atualiza a estrutura de dados central, mas não responde diretamente ao cliente.
* **2. ThreadBroadcast (Emissão Contínua):** Uma única thread corre em background e, periodicamente, bloqueia a base de dados, processa a física do jogo (movimento dos vulcões e gravidade) e envia o estado global atualizado para todos os clientes. Em vez de respostas individuais, o servidor envia de forma contínua a fotografia completa do estado global, garantindo que atua como uma entidade autoritária com todos os clientes perfeitamente sincronizados.

---

## DESTAQUE ARQUITETURA: Refatoração da Física (`vel_y`) e Aumento de Dificuldade

Na transição de um jogo de "turnos" para um modelo contínuo em **Tempo Real**, a manipulação direta das coordenadas do jogador foi substituída por um motor de física simples baseado em velocidade (`vel_y`). O pássaro não "salta" teleportando-se no eixo Y, mas sim recebendo um impulso negativo na sua velocidade, que interage continuamente com a gravidade.

**O Problema do Aumento de Dificuldade e Efeito "Teleporte":**
Com a nova mecânica onde a velocidade dos vulcões aumenta dinamicamente conforme a pontuação do jogador, o jogo torna-se mais rápido. Adicionalmente, se o jogador deixar o pássaro em queda livre (sem pressionar Flap), a gravidade acumularia uma força cada vez maior na `vel_y`.
Se o pássaro acumulasse demasiada velocidade, ele desceria uma quantidade enorme de unidades na grelha numa única transição do servidor (ex: deslocar-se 15 unidades num único *frame* de 0.03s). Como a colisão é detetada verificando se a coordenada exata do pássaro interseta a parede do vulcão, um movimento tão brusco permitiria que o Priolo sofresse um "teleporte", atravessando paredes por passar do ponto A para o ponto B sem registar intersecção nos pontos intermédios.

**A Solução Implementada (Limite de Velocidade):**
Para garantir a integridade da deteção de colisões (*Hitboxes*), foi implementado um **cap máximo de velocidade na estrutura de dados** (ex: `if jogador['vel_y'] > 4.5: jogador['vel_y'] = 4.5`).
Isto funciona como a "velocidade" do pássaro. Ao limitar a taxa máxima de queda, asseguramos que o percurso *frame a frame* é sempre contínuo e suficientemente pequeno para que o sistema de colisões detete de forma rigorosa qualquer impacto contra a abertura do vulcão ou contra o chão, garantindo uma jogabilidade justa mesmo a altas velocidades.
