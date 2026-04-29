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

## 5. Interface Gráfica e Motor de Jogo (Pygame)

Para a versão final do projeto, a visualização em terminal baseada em turnos foi totalmente substituída por um **Motor Gráfico em Tempo Real** desenvolvido na biblioteca `pygame`. Esta transição exigiu uma reestruturação da arquitetura do cliente para separar a lógica de rede da lógica de renderização.

### 5.1. Nova Arquitetura do Cliente
Na versão baseada em terminal, a thread de receção de dados (`BroadcastReceiver`) era responsável por limpar e desenhar o ecrã. No entanto, em aplicações gráficas, desenhar a partir de threads secundárias causa instabilidade e *crashes*.
* **Solução:** O `BroadcastReceiver` passou a ter uma função puramente passiva. Ele apenas ouve os pacotes JSON vindos do servidor e guarda-os numa variável partilhada (`self.estado_atual = estado`).
* **Game Loop:** A classe `InterfaceGrafica` corre no *Main Thread*. Em cada ciclo, ela lê o último `estado_atual` disponível e desenha os elementos no ecrã.

### 5.2. Interpolação de Movimento (Movement Smoothing)
Como o servidor opera a um *Tick Rate* de ~33 FPS (envia dados a cada 0.03s) para poupar largura de banda, desenhar as coordenadas exatas causaria um movimento "engasgado". Para resolver isto, implementámos interpolação visual:
* O cliente não desenha o Priolo e os Vulcões exatamente onde o servidor diz que eles estão. Em vez disso, ele define essas coordenadas como "alvos" (`target_x` e `target_y`).
* A cada *frame*, o Pygame desliza suavemente os *sprites* da sua posição visual atual em direção à posição alvo matemática.
* **O Papel das IDs:** Para que a interpolação dos vulcões funcione sem erros, o servidor gera um `id` único para cada vulcão. O cliente usa este ID para saber exatamente qual vulcão deve deslizar para onde, evitando que os obstáculos deem "teleporte" no ecrã quando o primeiro vulcão da lista é apagado pelo servidor.

### 5.3. Física Visual e Animações
A interface foi programada para reagir de forma orgânica às leis da física enviadas pelo servidor:
* **Rotação Dinâmica (Tilt):** O ângulo do pássaro no ecrã ajusta-se consoante a sua velocidade vertical. Se estiver a cair, o *sprite* roda para apontar para baixo; se receber um impulso ("FLAP"), roda para apontar para cima.
* **Processamento de Assets:** O fundo do jogo suporta animações contínuas (GIFs), extraindo *frames* utilizando a biblioteca `PIL` (Pillow), garantindo que os elementos do fundo se movem independentemente dos pacotes de rede.

### 5.4. Dependências Necessárias
Para correr a versão final do cliente gráfico, é necessário instalar as seguintes bibliotecas Python:
```bash
pip install pygame
pip install pillow
```
---

## DESTAQUE ARQUITETURA: Refatoração da Física (`vel_y`) e Aumento de Dificuldade

Na transição de um jogo de "turnos" para um modelo contínuo em **Tempo Real**, a manipulação direta das coordenadas do jogador foi substituída por um motor de física simples baseado em velocidade (`vel_y`). O pássaro não "salta" teleportando-se no eixo Y, mas sim recebendo um impulso negativo na sua velocidade, que interage continuamente com a gravidade.

**O Problema do Aumento de Dificuldade e Efeito "Teleporte":**
Com a nova mecânica onde a velocidade dos vulcões aumenta dinamicamente conforme a pontuação do jogador, o jogo torna-se mais rápido. Adicionalmente, se o jogador deixar o pássaro em queda livre (sem pressionar Flap), a gravidade acumularia uma força cada vez maior na `vel_y`.
Se o pássaro acumulasse demasiada velocidade, ele desceria uma quantidade enorme de unidades na grelha numa única transição do servidor (ex: deslocar-se 15 unidades num único *frame* de 0.03s). Como a colisão é detetada verificando se a coordenada exata do pássaro interseta a parede do vulcão, um movimento tão brusco permitiria que o Priolo sofresse um "teleporte", atravessando paredes por passar do ponto A para o ponto B sem registar intersecção nos pontos intermédios.

**A Solução Implementada (Limite de Velocidade):**
Para garantir a integridade da deteção de colisões (*Hitboxes*), foi implementado um **cap máximo de velocidade na estrutura de dados** (ex: `if jogador['vel_y'] > 4.5: jogador['vel_y'] = 4.5`).
Isto funciona como a "velocidade" do pássaro. Ao limitar a taxa máxima de queda, asseguramos que o percurso *frame a frame* é sempre contínuo e suficientemente pequeno para que o sistema de colisões detete de forma rigorosa qualquer impacto contra a abertura do vulcão ou contra o chão, garantindo uma jogabilidade justa mesmo a altas velocidades.

### Anexo: Prompt para a Geração do Pygame

Para a conversão da interface de terminal numa interface gráfica, foi necessário desenhar um *prompt* técnico que garantisse a estabilidade da rede e a fluidez visual do jogo. O *prompt* utilizado foi o seguinte:

> **Prompt:**
> "O meu projeto 'Flappy Priolo' tem um servidor que corre a um *tick rate* de ~33 FPS (0.03s de intervalo) e envia o estado do jogo em formato JSON via Broadcast para múltiplos clientes. 
> 
> Preciso que programes a classe `InterfaceGrafica` (cliente Pygame) cumprindo estritamente os seguintes requisitos arquiteturais:
> 
> **1. Concorrência e *Thread Safety*:**
> O Pygame não suporta renderização a partir de threads em background. Portanto, o `BroadcastReceiver` (que herda de `threading.Thread`) deve apenas ler o socket e guardar o JSON descodificado numa variável de instância `estado_atual`. O *Game Loop* principal do Pygame correrá a 60 FPS e fará a leitura dessa variável para desenhar o ecrã.
> 
> **2. Interpolação Linear (Movement Smoothing):**
> Como o servidor envia dados a ~33 FPS e o ecrã atualiza a 60 FPS, desenhar as coordenadas brutas causaria 'soluços' visuais. Implementa dicionários de suavização (`suave_y` e `suave_vx`) que apliquem interpolação para deslizar os *sprites* progressivamente até à posição alvo. 
> 
> **3. Gestão de IDs e Prevenção de Teleportes:**
> O servidor apaga os vulcões da lista quando estes saem do ecrã (`pop(0)`). Para que o sistema de interpolação não confunda o vulcão novo com o antigo (o que causaria um teleporte visual no ecrã), utiliza a chave `id` que o servidor envia dentro do dicionário de cada vulcão para os rastrear de forma única.
> 
> **4. Lógica de UI e Menus:**
> - Cria um ecrã inicial para pedir o nome do jogador.
> - Um *Leaderboard* no canto superior direito a mostrar os 5 melhores jogadores.
> - Um menu de Pausa (tecla ESC) que congele os inputs do jogador (mas não o socket) com botões para 'Retomar' ou 'Sair' (voltando ao menu inicial de forma limpa, fechando a ligação atual).
> - Um *Debug Overlay* no canto superior esquerdo que leia o dicionário `parametros` do JSON para mostrar a Gravidade, Velocidade Atual e IDs gerados em tempo real.
> 
> **5. Feedback Visual:**
> Calcula a velocidade visual do pássaro baseada na diferença da sua posição interpolada e aplica uma rotação (*tilt*) ao *sprite*: apontar para cima quando sobe, e para baixo quando cai. Utiliza a biblioteca PIL para extrair frames do fundo animado `background_acores.gif`."
