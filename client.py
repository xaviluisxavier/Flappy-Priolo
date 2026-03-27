"""
Flappy Priolo - Azores Edition
Um jogo em Pygame baseado no clássico Flappy Bird, apresentando a ave endémica 
dos Açores (o Priolo) e obstáculos vulcânicos. Inclui modos de um jogador, 
modo "Hardcore" (com aumento progressivo de velocidade) e modo Multijogador em rede.
"""

import pygame
import socket
import pickle
import random
import sys
import os
from PIL import Image, ImageSequence

def get_asset_path(filename):
    """
    Obtém o caminho absoluto para os ficheiros de recursos (assets).
    Garante que os ficheiros são encontrados quer ao correr o script diretamente,
    quer ao correr através de um executável compilado com o PyInstaller.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "assets", filename)

def load_gif_frame(filename, size):
    """
    Carrega e redimensiona os frames de uma imagem gif.
    Retorna uma lista de superfícies do Pygame convertidas para desempenho máximo.
    """
    path = get_asset_path(filename)
    if not os.path.exists(path):
        return [pygame.Surface(size)]
    pil_img = Image.open(path)
    frames = []
    for frame in ImageSequence.Iterator(pil_img):
        frame_rgba = frame.convert("RGBA")
        pygame_surface = pygame.image.fromstring(
            frame_rgba.tobytes(), frame_rgba.size, frame_rgba.mode
        ).convert_alpha()
        frames.append(pygame.transform.scale(pygame_surface, size))
    return frames

pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
pygame.init()
pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Priolo - Azores Edition")

WHITE, BLACK, YELLOW = (255, 255, 255), (0, 0, 0), (255, 255, 0)
BLUE, BLUE_HOVER = (0, 100, 255), (100, 180, 255)
GREEN, GREEN_HOVER = (0, 180, 0), (100, 255, 100)
RED, RED_HOVER = (200, 0, 0), (255, 80, 80)
ORANGE, ORANGE_HOVER = (255, 140, 0), (255, 180, 50)

def load_fire_borders():
    """Carrega, recorta e roda o GIF de fogo, convertendo-o para renderização acelerada."""
    path = get_asset_path("fire.gif")
    top, bottom, left, right = [], [], [], []
    if not os.path.exists(path):
        return [], [], [], []
    try:
        pil_img = Image.open(path)
        fw = 80 
        for frame in ImageSequence.Iterator(pil_img):
            frame_rgba = frame.convert("RGBA")
            pygame_surface = pygame.image.fromstring(
                frame_rgba.tobytes(), frame_rgba.size, frame_rgba.mode
            ).convert_alpha()
            surf_b = pygame.transform.scale(pygame_surface, (WIDTH, fw))
            surf_t = pygame.transform.flip(surf_b, False, True)
            surf_base_side = pygame.transform.scale(pygame_surface, (HEIGHT, fw))
            surf_r = pygame.transform.rotate(surf_base_side, 90)
            surf_l = pygame.transform.rotate(surf_base_side, -90)
            bottom.append(surf_b)
            top.append(surf_t)
            right.append(surf_r)
            left.append(surf_l)
    except:
        pass
    return top, bottom, left, right

FIRE_TOP, FIRE_BOTTOM, FIRE_LEFT, FIRE_RIGHT = load_fire_borders()

BLACK_OVERLAY = pygame.Surface((WIDTH, HEIGHT))
BLACK_OVERLAY.fill(BLACK)
MENU_OVERLAY = pygame.Surface((WIDTH, HEIGHT))
MENU_OVERLAY.set_alpha(150)
MENU_OVERLAY.fill(BLACK)
LEADERBOARD_BG = pygame.Surface((200, 160))
LEADERBOARD_BG.fill(BLACK)
LEADERBOARD_BG.set_alpha(150)
FLASH_OVERLAY = pygame.Surface((WIDTH, HEIGHT))
FLASH_OVERLAY.fill(WHITE)

FONT = pygame.font.SysFont("comicsans", 30, True)
SMALL_FONT = pygame.font.SysFont("comicsans", 20, True)
BIG_FONT = pygame.font.SysFont("comicsans", 55, True)
BUTTON_FONT = pygame.font.SysFont("comicsans", 25, True)

DEATH_SOUND = None
MUSIC_END = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(MUSIC_END)

PLAYLIST_NORMAL = ["music_normal_1.mp3", "music_normal_2.mp3"]
PLAYLIST_HARDCORE = ["music_hardcore_1.mp3", "music_hardcore_2.mp3"]
PLAYLIST_MULTI = ["music_multi_1.mp3"]

current_queue = []
current_mode_list = []

def load_sounds():
    """Carrega os efeitos sonoros do jogo, nomeadamente o som de morte/colisão."""
    global DEATH_SOUND
    try:
        path = get_asset_path("death.wav")
        DEATH_SOUND = pygame.mixer.Sound(path)
        DEATH_SOUND.set_volume(0.6)
    except: pass

def get_next_song_path():
    """Devolve o caminho para a próxima música na playlist, baralhando a fila se necessário."""
    global current_queue, current_mode_list
    if not current_mode_list: return None
    if not current_queue:
        current_queue = current_mode_list[:]
        random.shuffle(current_queue)
    if current_queue:
        return get_asset_path(current_queue.pop(0))
    return None

def start_playlist(multiplayer, hardcore):
    """Interrompe a música atual e inicia a playlist adequada ao modo de jogo selecionado."""
    global current_queue, current_mode_list
    pygame.mixer.music.stop()
    if multiplayer: current_mode_list = PLAYLIST_MULTI[:]
    elif hardcore: current_mode_list = PLAYLIST_HARDCORE[:]
    else: current_mode_list = PLAYLIST_NORMAL[:]
    
    current_queue = [] 
    first_song = get_next_song_path()
    if first_song and os.path.exists(first_song):
        try:
            pygame.mixer.music.load(first_song)
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play()
            queue_next_song()
        except: pass

def queue_next_song():
    """Adiciona a próxima música da playlist atual à fila de espera do misturador (mixer)."""
    next_song = get_next_song_path()
    if next_song and os.path.exists(next_song):
        try: pygame.mixer.music.queue(next_song)
        except: pass

def play_death_sound():
    """Para imediatamente a música de fundo e reproduz o efeito sonoro de derrota."""
    pygame.mixer.music.stop() 
    if DEATH_SOUND: DEATH_SOUND.play()

def draw_text_shadow(win, text, font, color, x, y):
    """Desenha um texto com uma leve sombra preta para aumentar o contraste e a legibilidade."""
    shadow = font.render(text, True, BLACK)
    win.blit(shadow, (x + 2, y + 2))
    main_text = font.render(text, True, color)
    win.blit(main_text, (x, y))

def draw_styled_button(win, rect, text, font, base_color, hover_color, text_color):
    """Desenha um botão retangular estético que muda de cor ao passar com o rato (hover)."""
    mouse_pos = pygame.mouse.get_pos()
    color = hover_color if rect.collidepoint(mouse_pos) else base_color
    border_color = YELLOW if rect.collidepoint(mouse_pos) else WHITE
    pygame.draw.rect(win, color, rect)
    pygame.draw.rect(win, border_color, rect, 3)
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    draw_text_shadow(win, text, font, text_color, text_rect.x, text_rect.y)

def load_and_clean_asset(path, size):
    """Carrega uma imagem com canal alfa, corta o espaço vazio em volta e ajusta-a ao tamanho pedido."""
    try:
        img = pygame.image.load(path).convert_alpha()
        rect = img.get_bounding_rect()
        trimmed_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        trimmed_surface.blit(img, (0, 0), rect)
        return pygame.transform.scale(trimmed_surface, size)
    except FileNotFoundError:
        s = pygame.Surface(size, pygame.SRCALPHA)
        s.fill(RED)
        return s

try:
    BACKGROUND_FRAMES = load_gif_frame("background_acores.gif", (WIDTH, HEIGHT))
    if not BACKGROUND_FRAMES:
        bg = pygame.Surface((WIDTH, HEIGHT))
        bg.fill(BLACK)
        BACKGROUND_FRAMES = [bg]

    PRIOLO_UP = load_and_clean_asset(get_asset_path("priolo_up.png"), (70, 50))
    PRIOLO_MID = load_and_clean_asset(get_asset_path("priolo_mid.png"), (70, 50))
    PRIOLO_DOWN = load_and_clean_asset(get_asset_path("priolo_down.png"), (70, 50))
    
    VOLCANO_BOTTOM_IMG = load_and_clean_asset(get_asset_path("volcano_bottom.png"), (120, 500))
    VOLCANO_TOP_IMG = load_and_clean_asset(get_asset_path("volcano_top.png"), (120, 500))
    
    VOLCANO_TOP_MASK = pygame.mask.from_surface(VOLCANO_TOP_IMG)
    VOLCANO_BOTTOM_MASK = pygame.mask.from_surface(VOLCANO_BOTTOM_IMG)
    
    load_sounds()
except Exception as e:
    print(f"Asset loading error: {e}")
    sys.exit()

SERVER_IP, SERVER_PORT = "26.195.177.217", 5555

class Priolo:
    """Classe que representa a ave controlada pelo jogador."""
    def __init__(self, x, y):
        """Inicializa o Priolo com a sua posição, atributos de velocidade e frames de animação."""
        self.x = x
        self.y = y
        self.vel = 0
        self.imgs = [PRIOLO_UP, PRIOLO_MID, PRIOLO_DOWN]
        self.img_index = 0
        self.img = self.imgs[self.img_index]
        self.anim_timer = 0
        self.anim_speed = 5
        self.mask = pygame.mask.from_surface(self.img)
        self.width, self.height = self.img.get_width(), self.img.get_height()
        
    def flap(self): 
        """Aplica um impulso negativo na velocidade para fazer o Priolo saltar para cima."""
        self.vel = -8
        
    def update(self):
        """Atualiza a posição do Priolo aplicando gravidade e gere a animação do bater de asas."""
        self.vel += 0.5
        self.y += self.vel
        
        if self.y > HEIGHT - self.height: 
            self.y, self.vel = HEIGHT - self.height, 0
        if self.y < 0: 
            self.y, self.vel = 0, 0
            
        if self.vel < 3:
            self.anim_timer += 1
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.img_index = (self.img_index + 1) % 3
            self.img = self.imgs[self.img_index]
        else:
            self.img = PRIOLO_MID
            self.img_index = 1
            
    def draw(self, window): 
        """Desenha o Priolo no ecrã e aplica a rotação consoante a velocidade de queda."""
        tilt = -self.vel * 3  
        tilt = max(-90, min(tilt, 25))
        rotated_img = pygame.transform.rotate(self.img, tilt)
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft=(self.x, int(self.y))).center)
        window.blit(rotated_img, new_rect.topleft)
        self.mask = pygame.mask.from_surface(rotated_img)

class Volcano:
    """Classe que representa os obstáculos do jogo (os vulcões)."""
    GAP = 150
    def __init__(self, x):
        """Inicializa um par de vulcões (topo e base) numa determinada coordenada X."""
        self.x = x
        self.passed = False
        self.TOP_PIPE = VOLCANO_TOP_IMG
        self.BOTTOM_PIPE = VOLCANO_BOTTOM_IMG
        self.set_height()
        
    def set_height(self):
        """Gera aleatoriamente a altura da abertura por onde o pássaro deve passar e reutiliza máscaras."""
        self.height = random.randrange(100, HEIGHT - self.GAP - 100)
        self.top = self.height - self.TOP_PIPE.get_height()
        self.bottom = self.height + self.GAP
        self.top_mask = VOLCANO_TOP_MASK
        self.bottom_mask = VOLCANO_BOTTOM_MASK
        
    def move(self, velocity): 
        """Desloca o obstáculo para a esquerda."""
        self.x -= velocity
        
    def draw(self, window):
        """Desenha a parte superior e inferior do vulcão no ecrã."""
        window.blit(self.TOP_PIPE, (self.x, self.top))
        window.blit(self.BOTTOM_PIPE, (self.x, self.bottom))
        
    def collide(self, priolo):
        """Verifica se existe sobreposição entre a máscara do Priolo e a máscara dos vulcões."""
        priolo_rect = priolo.img.get_rect(topleft=(priolo.x, priolo.y))
        top_rect = self.TOP_PIPE.get_rect(topleft=(self.x, self.top))
        bottom_rect = self.BOTTOM_PIPE.get_rect(topleft=(self.x, self.bottom))
        
        if not (priolo_rect.colliderect(top_rect) or priolo_rect.colliderect(bottom_rect)):
            return False
            
        priolo_mask = priolo.mask
        return priolo_mask.overlap(self.top_mask, (self.x - priolo.x, self.top - int(priolo.y))) or \
               priolo_mask.overlap(self.bottom_mask, (self.x - priolo.x, self.bottom - int(priolo.y)))

def ask_for_name():
    """Abre um menu interativo para o jogador escrever o seu nome antes de entrar no modo Multiplayer."""
    user_text = ''
    input_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 25, 300, 50)
    bg_idx, bg_timer = 0, 0
    while True:
        bg_timer += 1
        if bg_timer >= 15: 
            bg_idx = (bg_idx + 1) % len(BACKGROUND_FRAMES)
            bg_timer = 0
        current_bg = BACKGROUND_FRAMES[bg_idx]

        win.blit(current_bg, (0,0))
        win.blit(MENU_OVERLAY, (0,0))
        
        txt_title = "Enter your name:"
        draw_text_shadow(win, txt_title, FONT, WHITE, WIDTH//2 - FONT.size(txt_title)[0]//2, HEIGHT//2 - 80)
        pygame.draw.rect(win, WHITE, input_rect)
        pygame.draw.rect(win, YELLOW, input_rect, 3)
        
        text_surface = FONT.render(user_text, True, BLACK)
        win.blit(text_surface, (input_rect.x + 10, input_rect.y + 10))
        
        txt_enter = "(Press ENTER to confirm)"
        draw_text_shadow(win, txt_enter, SMALL_FONT, YELLOW, WIDTH//2 - SMALL_FONT.size(txt_enter)[0]//2, HEIGHT//2 + 40)
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and len(user_text) > 0: 
                    return user_text
                elif event.key == pygame.K_BACKSPACE: 
                    user_text = user_text[:-1]
                else:
                    if len(user_text) < 10: 
                        user_text += event.unicode

def draw_window(win, bg_surface, players, volcanoes, score, best_score, game_over, my_id, btn_restart, btn_menu, flash_alpha, multiplayer, local_player, fire_frame_idx):
    """Renderiza no ecrã todos os elementos ativos e respeita a hierarquia visual"""
    # 1. Fundo
    win.blit(bg_surface, (0, 0))
    
    # 2. Obstáculos
    for v in volcanoes: 
        v.draw(win)
        
    # 3. Jogadores
    if local_player:
        local_player.draw(win)
        my_name = players.get(my_id, {}).get('name', 'Me') if players else "Me"
        draw_text_shadow(win, my_name, SMALL_FONT, YELLOW, local_player.x, int(local_player.y) - 25)

    if multiplayer and players:
        for p_id, p_data in players.items():
            if p_id != my_id:
                y_pos = int(p_data['y'])
                win.blit(PRIOLO_MID, (100, y_pos))
                draw_text_shadow(win, p_data.get('name', f"P{p_id}"), SMALL_FONT, WHITE, 100, y_pos - 25)
    
    # 4. Efeito de Fogo
    if score >= 10 and len(FIRE_BOTTOM) > 0:
        current_top = FIRE_TOP[fire_frame_idx]
        current_bottom = FIRE_BOTTOM[fire_frame_idx]
        current_left = FIRE_LEFT[fire_frame_idx]
        current_right = FIRE_RIGHT[fire_frame_idx]
        
        current_top.set_alpha(255)
        current_bottom.set_alpha(255)
        current_left.set_alpha(255)
        current_right.set_alpha(255)
        
        win.blit(current_top, (0, 0))
        win.blit(current_bottom, (0, HEIGHT - current_bottom.get_height()))
        win.blit(current_left, (0, 0))
        win.blit(current_right, (WIDTH - current_right.get_width(), 0))
    
    # 5. Efeito de Flash de Luz
    if flash_alpha > 0:
        FLASH_OVERLAY.set_alpha(int(flash_alpha))
        win.blit(FLASH_OVERLAY, (0, 0))

    # 6. UI (Score e Leaderboard)
    if multiplayer:
        win.blit(LEADERBOARD_BG, (WIDTH - 210, 10))
        draw_text_shadow(win, "TOP PLAYERS", SMALL_FONT, YELLOW, WIDTH - 200, 15)
        
        if players:
            sorted_players = sorted(players.items(), key=lambda x: x[1]['score'], reverse=True)
            for i, (p_id, p_data) in enumerate(sorted_players[:5]):
                name = p_data.get('name', f"P{p_id}")[:8]
                p_score = p_data['score']
                txt = f"{i+1}. {name}: {p_score}"
                color = YELLOW if p_id == my_id else WHITE
                draw_text_shadow(win, txt, SMALL_FONT, color, WIDTH - 200, 45 + (i * 22))
    else: 
        if not game_over: 
            draw_text_shadow(win, f"Score: {score}", FONT, WHITE, 20, 20)

    # 7. Menu de Game Over
    if game_over:
        BLACK_OVERLAY.set_alpha(200)
        win.blit(BLACK_OVERLAY, (0,0))
        draw_text_shadow(win, "GAME OVER", BIG_FONT, RED, WIDTH//2 - BIG_FONT.size("GAME OVER")[0]//2, 80)
        draw_text_shadow(win, f"Score: {score}", FONT, WHITE, WIDTH//2 - FONT.size(f"Score: {score}")[0]//2, 140)
        draw_text_shadow(win, f"Best: {best_score}", FONT, YELLOW, WIDTH//2 - FONT.size(f"Best: {best_score}")[0]//2, 175)
        
        draw_styled_button(win, btn_restart, "Play Again", BUTTON_FONT, GREEN, GREEN_HOVER, WHITE)
        draw_styled_button(win, btn_menu, "MAIN MENU", BUTTON_FONT, RED, RED_HOVER, WHITE)
        
    pygame.display.update()

def main():
    """Função principal: Gere os menus iniciais, o ciclo de vida do jogo e a comunicação de rede no modo multijogador."""
    session_best_normal, session_best_hardcore = 0, 0
    bg_frame_index, bg_timer = 0, 0
    fire_frame_idx, fire_timer = 0, 0
    
    while True:
        pygame.mixer.music.stop()
        menu_active, multiplayer, hardcore_mode, server_error_msg = True, False, False, ""
        
        btn_single = pygame.Rect(WIDTH//2 - 150, 200, 300, 60)
        btn_hardcore = pygame.Rect(WIDTH//2 - 150, 280, 300, 60)
        btn_multi = pygame.Rect(WIDTH//2 - 150, 360, 300, 60)
        btn_quit = pygame.Rect(WIDTH//2 - 150, 440, 300, 60)
        client, connected = None, False

        while menu_active:
            bg_timer += 1
            if bg_timer >= 25: 
                bg_frame_index = (bg_frame_index + 1) % len(BACKGROUND_FRAMES)
                bg_timer = 0
            current_bg = BACKGROUND_FRAMES[bg_frame_index]
            
            win.blit(current_bg, (0,0))
            draw_text_shadow(win, "FLAPPY PRIOLO", BIG_FONT, WHITE, WIDTH//2 - BIG_FONT.size("FLAPPY PRIOLO")[0]//2, 80)
            
            if server_error_msg: 
                draw_text_shadow(win, server_error_msg, FONT, RED, WIDTH//2 - FONT.size(server_error_msg)[0]//2, 150)
                
            draw_styled_button(win, btn_single, "SINGLE PLAYER", BUTTON_FONT, BLUE, BLUE_HOVER, WHITE)
            draw_styled_button(win, btn_hardcore, "HARDCORE (SPEED)", BUTTON_FONT, ORANGE, ORANGE_HOVER, WHITE)
            draw_styled_button(win, btn_multi, "MULTIPLAYER", BUTTON_FONT, GREEN, GREEN_HOVER, WHITE)
            draw_styled_button(win, btn_quit, "QUIT", BUTTON_FONT, RED, RED_HOVER, WHITE)
            
            pygame.display.update()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if btn_single.collidepoint(mx, my): 
                        menu_active = False
                    elif btn_hardcore.collidepoint(mx, my): 
                        hardcore_mode, menu_active = True, False
                    elif btn_multi.collidepoint(mx, my): 
                        win.blit(current_bg, (0,0))
                        msg_con = "Connecting to server..."
                        draw_text_shadow(win, msg_con, FONT, YELLOW, WIDTH//2 - FONT.size(msg_con)[0]//2, HEIGHT//2)
                        pygame.display.update()
                        try:
                            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            client.settimeout(1.0) 
                            client.connect((SERVER_IP, SERVER_PORT))
                            multiplayer, menu_active = True, False
                        except: 
                            server_error_msg = "SERVER OFFLINE!"
                    elif btn_quit.collidepoint(mx, my): 
                        pygame.quit(); sys.exit()

        my_name = ask_for_name() if multiplayer else "Me"
        
        if multiplayer and client:
            try: 
                client.settimeout(None)
                my_id = int(client.recv(2048).decode())
                connected = True
            except: 
                multiplayer = False
        else: 
            my_id = 0

        start_playlist(multiplayer, hardcore_mode)
        player = Priolo(100, 300)
        volcanoes = [Volcano(WIDTH + 200)] 
        
        score, game_over, clock, run_game = 0, False, pygame.time.Clock(), True
        current_speed, last_score = 4, 0
        flash_alpha = 0
        
        btn_restart = pygame.Rect(WIDTH//2-150, 240, 300, 60)
        btn_menu = pygame.Rect(WIDTH//2-150, 320, 300, 60)
        
        all_p = {}

        while run_game:
            clock.tick(60)
            
            bg_timer += 1
            if bg_timer >= 5: 
                bg_frame_index = (bg_frame_index + 1) % len(BACKGROUND_FRAMES)
                bg_timer = 0
            current_bg = BACKGROUND_FRAMES[bg_frame_index]
            
            fire_timer += 1
            if fire_timer >= 4:
                fire_frame_idx = (fire_frame_idx + 1) % len(FIRE_BOTTOM) if len(FIRE_BOTTOM) > 0 else 0
                fire_timer = 0
            
            best_score = session_best_hardcore if hardcore_mode else session_best_normal
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    pygame.quit(); sys.exit()
                if event.type == MUSIC_END and not game_over: 
                    queue_next_song()
                    
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if not game_over: 
                        player.flap()
                    else: 
                        player, volcanoes, score, game_over = Priolo(100, 300), [Volcano(WIDTH + 200)], 0, False
                        current_speed, last_score, flash_alpha = 4, 0, 0
                        start_playlist(multiplayer, hardcore_mode)
                        
                if event.type == pygame.MOUSEBUTTONDOWN and game_over:
                    mx, my = pygame.mouse.get_pos()
                    if btn_restart.collidepoint(mx, my):
                        player, volcanoes, score, game_over = Priolo(100, 300), [Volcano(WIDTH + 200)], 0, False
                        current_speed, last_score, flash_alpha = 4, 0, 0
                        start_playlist(multiplayer, hardcore_mode)
                    elif btn_menu.collidepoint(mx, my): 
                        run_game = False

            if not game_over:
                if hardcore_mode:
                    if score > session_best_hardcore: session_best_hardcore = score
                    current_speed = 4 + (score // 3)
                else:
                    if score > session_best_normal: session_best_normal = score
                    current_speed = 4 + (score // 10)
                
                if score > last_score:
                    if score >= 10 and score % 10 == 0: 
                        flash_alpha = 200 
                    last_score = score
                
                if flash_alpha > 0:
                    flash_alpha -= 8
                    if flash_alpha < 0:
                        flash_alpha = 0

                player.update()
                add_v, rem = False, []
                
                for v in volcanoes:
                    v.move(current_speed)
                    if v.collide(player): 
                        play_death_sound()
                        game_over = True 
                        
                    if v.x + 120 < 100 and not v.passed: 
                        v.passed = True
                        add_v = True
                        
                    if v.x + 120 < 0: 
                        rem.append(v)
                        
                if add_v: 
                    score += 1
                    distancia_extra = random.randrange(50, 150)
                    volcanoes.append(Volcano(WIDTH + distancia_extra))
                    
                for r in rem: 
                    volcanoes.remove(r)
                    
                if player.y >= HEIGHT - player.height or player.y < 0: 
                    play_death_sound()
                    game_over = True

            if multiplayer and connected:
                try:
                    client.settimeout(0.005) 
                    client.send(pickle.dumps({'y': player.y, 'score': score, 'game_over': game_over, 'name': my_name}))
                    novos_dados = pickle.loads(client.recv(4096))
                    all_p = novos_dados
                except socket.timeout:
                    pass
                except Exception as e:
                    connected = False
            else: 
                all_p = {my_id: {'y': player.y, 'score': score, 'name': my_name}}
            
            draw_window(win, current_bg, all_p, volcanoes, score, best_score, game_over, my_id, btn_restart, btn_menu, flash_alpha, multiplayer, player, fire_frame_idx)
            
        if client: 
            client.close()

if __name__ == "__main__":
    main()