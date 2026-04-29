import pygame
import socket
import sys
import os
from PIL import Image, ImageSequence
import cliente
from cliente.interface.broadcast_receiver import BroadcastReceiver

def get_asset_path(filename):
    base_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.dirname(os.path.dirname(base_path))
    return os.path.join(root_path, "assets", filename)

def load_gif_frame(filename, size):
    path = get_asset_path(filename)
    if not os.path.exists(path): return [pygame.Surface(size)]
    pil_img = Image.open(path)
    frames = []
    for frame in ImageSequence.Iterator(pil_img):
        frame_rgba = frame.convert("RGBA")
        pygame_surface = pygame.image.fromstring(
            frame_rgba.tobytes(), frame_rgba.size, frame_rgba.mode
        ).convert_alpha()
        frames.append(pygame.transform.scale(pygame_surface, size))
    return frames

def load_and_clean_asset(path, size):
    try:
        img = pygame.image.load(path).convert_alpha()
        rect = img.get_bounding_rect()
        trimmed_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        trimmed_surface.blit(img, (0, 0), rect)
        return pygame.transform.scale(trimmed_surface, size)
    except:
        s = pygame.Surface(size, pygame.SRCALPHA); s.fill((255,0,0)); return s

def draw_text_shadow(win, text, font, color, x, y):
    shadow = font.render(text, True, (0, 0, 0))
    win.blit(shadow, (x + 2, y + 2))
    win.blit(font.render(text, True, color), (x, y))

def draw_styled_button(win, rect, text, font, base_color, hover_color, text_color):
    mouse_pos = pygame.mouse.get_pos()
    color = hover_color if rect.collidepoint(mouse_pos) else base_color
    border_color = (255, 255, 0) if rect.collidepoint(mouse_pos) else (255, 255, 255)
    pygame.draw.rect(win, color, rect)
    pygame.draw.rect(win, border_color, rect, 3)
    text_surf = font.render(text, True, text_color)
    win.blit(text_surf, text_surf.get_rect(center=rect.center))

WIDTH, HEIGHT = 800, 600
WHITE, BLACK, YELLOW = (255, 255, 255), (0, 0, 0), (255, 255, 0)
GREEN, GREEN_HOVER = (0, 180, 0), (100, 255, 100)
RED, RED_HOVER = (200, 0, 0), (255, 80, 80)

class InterfaceGrafica:
    def __init__(self):
        pygame.init()
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Flappy Priolo - Azores Edition")
        
        self.ESCALA_X = WIDTH / 100 
        self.ESCALA_Y = HEIGHT / 100
        
        self.BACKGROUND_FRAMES = load_gif_frame("background_acores.gif", (WIDTH, HEIGHT))
        self.PRIOLO_IMGS = [
            load_and_clean_asset(get_asset_path("priolo_up.png"), (70, 50)),
            load_and_clean_asset(get_asset_path("priolo_mid.png"), (70, 50)),
            load_and_clean_asset(get_asset_path("priolo_down.png"), (70, 50))
        ]
        self.VOLCANO_TOP = load_and_clean_asset(get_asset_path("volcano_top.png"), (120, 500))
        self.VOLCANO_BOTTOM = load_and_clean_asset(get_asset_path("volcano_bottom.png"), (120, 500))

        self.FONT = pygame.font.SysFont("comicsans", 30, True)
        self.SMALL_FONT = pygame.font.SysFont("comicsans", 20, True)
        self.BIG_FONT = pygame.font.SysFont("comicsans", 55, True)
        self.BUTTON_FONT = pygame.font.SysFont("comicsans", 25, True)

        self.LEADERBOARD_BG = pygame.Surface((200, 160)); self.LEADERBOARD_BG.set_alpha(150); self.LEADERBOARD_BG.fill(BLACK)
        self.MENU_OVERLAY = pygame.Surface((WIDTH, HEIGHT)); self.MENU_OVERLAY.set_alpha(150); self.MENU_OVERLAY.fill(BLACK)
        self.PAUSE_BG = pygame.Surface((WIDTH, HEIGHT)); self.PAUSE_BG.set_alpha(180); self.PAUSE_BG.fill(BLACK)

        self.connection = socket.socket()
        self.paused = False
        
        # Dicionários para interpolação de movimento fluida
        self.suave_y = {} 
        self.suave_vx = {} 
        self.tilt = {}

    def ask_for_name(self, bg_idx):
        user_text = ''
        input_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 25, 300, 50)
        bg_timer = 0
        while True:
            bg_timer += 1
            if bg_timer >= 10:
                bg_idx = (bg_idx + 1) % len(self.BACKGROUND_FRAMES)
                bg_timer = 0

            self.win.blit(self.BACKGROUND_FRAMES[bg_idx], (0,0))
            self.win.blit(self.MENU_OVERLAY, (0,0))
            draw_text_shadow(self.win, "Enter your name:", self.FONT, WHITE, WIDTH//2 - 100, HEIGHT//2 - 70)
            pygame.draw.rect(self.win, WHITE, input_rect)
            pygame.draw.rect(self.win, YELLOW, input_rect, 3)
            self.win.blit(self.FONT.render(user_text, True, BLACK), (input_rect.x + 10, input_rect.y + 10))
            pygame.display.update()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                        clean_name = user_text.strip()
                        if len(clean_name) > 0: return clean_name
                    elif event.key == pygame.K_BACKSPACE: user_text = user_text[:-1]
                    elif event.unicode.isprintable() and len(user_text) < 10: user_text += event.unicode

    def draw_game(self, estado, meu_nome, bg_idx):
        self.win.blit(self.BACKGROUND_FRAMES[bg_idx], (0, 0))
        
        if not estado or 'jogadores' not in estado: 
            draw_text_shadow(self.win, "A carregar o mundo...", self.FONT, WHITE, WIDTH//2 - 120, HEIGHT//2)
            pygame.display.update()
            return

        tempo = pygame.time.get_ticks()

        # 1. DESENHAR VULCÕES
        for pid, info in estado['jogadores'].items():
            if info['nome'] == meu_nome:
                novos_vids = []
                for i, v in enumerate(info['vulcoes']):
                    target_vx = v['x'] * self.ESCALA_X
                    vid = f"{pid}_{info['vulcoes'][i].get('id', i)}"
                    
                    if vid not in self.suave_vx: 
                        self.suave_vx[vid] = target_vx
                    
                    self.suave_vx[vid] += (target_vx - self.suave_vx[vid]) * 0.45 
                    
                    vx = int(self.suave_vx[vid])
                    ay_px = int(v['abertura_y'] * self.ESCALA_Y)
                    margem = int(15 * self.ESCALA_Y)
                    
                    self.win.blit(self.VOLCANO_TOP, (vx - 60, ay_px - margem - 500))
                    self.win.blit(self.VOLCANO_BOTTOM, (vx - 60, ay_px + margem))
                    novos_vids.append(vid)
                    
                self.suave_vx = {k: v for k, v in self.suave_vx.items() if k in novos_vids}

        # 2. DESENHAR PRIOLOS 
        for pid, info in estado['jogadores'].items():
            px = int(info['x'] * self.ESCALA_X)
            target_y = info['y'] * self.ESCALA_Y
            
            if pid not in self.suave_y: 
                self.suave_y[pid] = target_y
            last_y = self.suave_y[pid]
            
            if abs(target_y - self.suave_y[pid]) > 25 * self.ESCALA_Y:
                self.suave_y[pid] = target_y
            else:
                self.suave_y[pid] += (target_y - self.suave_y[pid]) * 0.45
            
            vel_visual = self.suave_y[pid] - last_y
            
            if vel_visual < -0.2: 
                img_idx = (tempo // 150) % 2 
                img_base = self.PRIOLO_IMGS[img_idx]
                target_tilt = 15 
            elif vel_visual > 0.2: 
                img_base = self.PRIOLO_IMGS[2] 
                target_tilt = -25 
            else: 
                img_base = self.PRIOLO_IMGS[1] 
                target_tilt = 0

            if isinstance(img_base, list):
                img_surface = img_base[(tempo // 100) % len(img_base)]
            else:
                img_surface = img_base

            if pid not in self.tilt: self.tilt[pid] = 0
            self.tilt[pid] += (target_tilt - self.tilt[pid]) * 0.25
            
            if info['nome'] != meu_nome:
                img_surface = img_surface.copy()
                img_surface.set_alpha(128)
            
            rotated = pygame.transform.rotate(img_surface, self.tilt[pid])
            rect = rotated.get_rect(center=(px, int(self.suave_y[pid])))
            self.win.blit(rotated, rect.topleft)
            
            cor = YELLOW if info['nome'] == meu_nome else WHITE
            draw_text_shadow(self.win, info['nome'], self.SMALL_FONT, cor, px - 35, int(self.suave_y[pid]) - 50)

        # 3. LEADERBOARD
        self.win.blit(self.LEADERBOARD_BG, (WIDTH - 210, 10))
        draw_text_shadow(self.win, "TOP PLAYERS", self.SMALL_FONT, YELLOW, WIDTH - 200, 15)
        
        sorted_players = sorted(estado['jogadores'].items(), key=lambda x: x[1]['score'], reverse=True)
        for i, (p_id, p_data) in enumerate(sorted_players[:5]):
            txt = f"{i+1}. {p_data['nome'][:8]}: {p_data['score']}"
            cor = YELLOW if p_data['nome'] == meu_nome else WHITE
            draw_text_shadow(self.win, txt, self.SMALL_FONT, cor, WIDTH - 200, 45 + (i * 22))

        # 4. PAUSA OVERLAY
        if self.paused:
            self.win.blit(self.PAUSE_BG, (0, 0))
            draw_text_shadow(self.win, "PAUSA", self.BIG_FONT, WHITE, WIDTH//2 - 90, 150)
            draw_styled_button(self.win, pygame.Rect(WIDTH//2-100, 250, 200, 50), "RETOMAR", self.FONT, GREEN, GREEN_HOVER, WHITE)
            draw_styled_button(self.win, pygame.Rect(WIDTH//2-100, 320, 200, 50), "SAIR", self.FONT, RED, RED_HOVER, WHITE)

        pygame.display.update()

    def execute(self):
        btn_multi = pygame.Rect(WIDTH//2 - 150, 280, 300, 60)
        btn_quit = pygame.Rect(WIDTH//2 - 150, 360, 300, 60)
        bg_idx = 0
        
        menu_running = True
        while menu_running:
            bg_idx = (pygame.time.get_ticks() // 100) % len(self.BACKGROUND_FRAMES)
            self.win.blit(self.BACKGROUND_FRAMES[bg_idx], (0,0))
            draw_text_shadow(self.win, "FLAPPY PRIOLO", self.BIG_FONT, WHITE, WIDTH//2 - 210, 100)
            
            draw_styled_button(self.win, btn_multi, "MULTIPLAYER", self.BUTTON_FONT, GREEN, GREEN_HOVER, WHITE)
            draw_styled_button(self.win, btn_quit, "QUIT", self.BUTTON_FONT, RED, RED_HOVER, WHITE)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_multi.collidepoint(event.pos): menu_running = False
                    if btn_quit.collidepoint(event.pos): sys.exit()

        meu_nome = self.ask_for_name(bg_idx)
        
        self.win.blit(self.BACKGROUND_FRAMES[bg_idx], (0,0))
        draw_text_shadow(self.win, "A conectar ao servidor...", self.FONT, YELLOW, WIDTH//2 - 160, HEIGHT//2)
        pygame.display.update()
        
        try:
            self.connection.connect((cliente.SERVER_ADDRESS, cliente.PORT))
            self.connection.send(meu_nome.encode())
        except ConnectionRefusedError:
            self.win.blit(self.PAUSE_BG, (0,0))
            draw_text_shadow(self.win, "ERRO: Servidor Desligado!", self.FONT, RED, WIDTH//2 - 180, HEIGHT//2)
            pygame.display.update()
            pygame.time.delay(3000)
            sys.exit()

        receiver = BroadcastReceiver(self.connection)
        receiver.start()

        clock = pygame.time.Clock()
        bg_timer = 0

        while True:
            clock.tick(60)
            
            if not self.paused:
                bg_timer += 1
                if bg_timer >= 10:
                    bg_idx = (bg_idx + 1) % len(self.BACKGROUND_FRAMES)
                    bg_timer = 0
            
            if not receiver.ativo:
                self.win.blit(self.PAUSE_BG, (0, 0))
                draw_text_shadow(self.win, "LIGAÇÃO RECUSADA/PERDIDA", self.FONT, RED, WIDTH//2 - 200, HEIGHT//2 - 50)
                draw_text_shadow(self.win, "(O servidor caiu, ou o teu nome já existe)", self.SMALL_FONT, WHITE, WIDTH//2 - 220, HEIGHT//2 + 10)
                pygame.display.update()
                pygame.time.delay(4000)
                sys.exit()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.connection.send("END".encode())
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: self.paused = not self.paused
                    
                    if not self.paused and (event.key == pygame.K_SPACE or event.key == pygame.K_UP):
                        self.connection.send("FLAP".encode())
                
                if self.paused and event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    if WIDTH//2-100 <= mx <= WIDTH//2+100:
                        if 250 <= my <= 300: self.paused = False
                        if 320 <= my <= 370: sys.exit()

            if hasattr(receiver, 'estado_atual'):
                self.draw_game(receiver.estado_atual, meu_nome, bg_idx)