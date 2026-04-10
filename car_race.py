#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║         NeonRush — Python Car Race           ║
║         Built with Pygame  (Python 3.8+)     ║
╚══════════════════════════════════════════════╝

Controls:
  Arrow Keys or W A S D — steer / accelerate / brake
  ESC                   — pause / resume
"""

import pygame
import random
import math
import sys
import json
import os

# ──────────────────────────────────────────────
#  PYGAME INIT
# ──────────────────────────────────────────────
pygame.init()
pygame.font.init()

# ──────────────────────────────────────────────
#  CONSTANTS
# ──────────────────────────────────────────────
W, H   = 900, 700
FPS    = 60

# Road geometry
ROAD_L  = 190
ROAD_R  = 710
ROAD_W  = ROAD_R - ROAD_L        # 520 px
N_LANES = 4
LANE_W  = ROAD_W // N_LANES      # 130 px

# Colour palette
C = {
    "bg":         ( 8,   8,  20),
    "road":       (25,  28,  45),
    "lane":       (55,  60,  85),
    "white":      (255, 255, 255),
    "black":      (  0,   0,   0),
    "cyan":       (  0, 230, 255),
    "pink":       (255,  30, 140),
    "green":      (  0, 255, 145),
    "yellow":     (255, 220,   0),
    "orange":     (255, 135,   0),
    "red":        (255,  55,  55),
    "shield":     ( 80, 185, 255),
    "gray":       (110, 120, 145),
    "dark":       ( 12,  14,  30),
    "dark2":      ( 18,  22,  45),
}

SAVE_FILE = os.path.join(os.path.dirname(__file__), "race_save.json")

# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────
def lerp(a, b, t):
    return a + (b - a) * t

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def rand_lane_x():
    lane = random.randint(0, N_LANES - 1)
    return ROAD_L + lane * LANE_W + LANE_W // 2

def load_best():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE) as f:
                d = json.load(f)
                return d.get("best", 0), d.get("top_level", 1)
        except Exception:
            pass
    return 0, 1

def save_best(score, level):
    best, top = load_best()
    if score > best:
        best = score
    if level > top:
        top = level
    with open(SAVE_FILE, "w") as f:
        json.dump({"best": best, "top_level": top}, f)

# ──────────────────────────────────────────────
#  FONTS  (fallback chain)
# ──────────────────────────────────────────────
def make_font(size, bold=False):
    for name in ["Consolas", "Courier New", "Lucida Console", "Monospace"]:
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        except Exception:
            pass
    return pygame.font.Font(None, size)

F_HUGE  = make_font(76, bold=True)
F_BIG   = make_font(42, bold=True)
F_MED   = make_font(28, bold=True)
F_BODY  = make_font(22)
F_SMALL = make_font(18)
F_BTN   = make_font(26, bold=True)

# ──────────────────────────────────────────────
#  BUTTON
# ──────────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, col, col_hover):
        self.rect      = pygame.Rect(x, y, w, h)
        self.text      = text
        self.col       = col
        self.col_hover = col_hover
        self.hovered   = False

    def update(self):
        mx, my = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mx, my)

    def draw(self, surf):
        col = self.col_hover if self.hovered else self.col
        # outer glow when hovered
        if self.hovered:
            gs = pygame.Surface((self.rect.w + 24, self.rect.h + 24), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*col, 55), gs.get_rect(), border_radius=14)
            surf.blit(gs, (self.rect.x - 12, self.rect.y - 12))
        # border
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        # dark fill
        inner = self.rect.inflate(-4, -4)
        dark = tuple(max(0, c - 130) for c in col)
        pygame.draw.rect(surf, dark, inner, border_radius=8)
        # label
        scale = 1.06 if self.hovered else 1.0
        raw   = F_BTN.render(self.text, True, col)
        txt   = pygame.transform.smoothscale(
            raw, (int(raw.get_width() * scale), int(raw.get_height() * scale))
        )
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )

# ──────────────────────────────────────────────
#  PARTICLE
# ──────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(70, 240)
        self.x     = x
        self.y     = y
        self.vx    = math.cos(angle) * speed
        self.vy    = math.sin(angle) * speed
        self.life  = random.uniform(0.4, 1.1)
        self.maxl  = self.life
        self.r     = random.randint(2, 7)
        self.color = color[:3]

    def update(self, dt):
        self.x  += self.vx * dt
        self.y  += self.vy * dt
        self.vy += 100 * dt        # gravity
        self.life -= dt

    def draw(self, surf):
        ratio = max(0.0, self.life / self.maxl)
        r     = max(1, int(self.r * ratio))
        alpha = int(255 * ratio)
        s     = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        surf.blit(s, (int(self.x) - r, int(self.y) - r))

# ──────────────────────────────────────────────
#  POWER-UP
# ──────────────────────────────────────────────
class PowerUp:
    """kind = 'star' | 'shield'"""
    def __init__(self, kind, x, y):
        self.kind  = kind
        self.x     = float(x)
        self.y     = float(y)
        self.r     = 18
        self.t     = 0.0

    def update(self, dt, road_speed):
        self.y += (road_speed + 190) * dt
        self.t += dt

    def draw(self, surf):
        pulse = 0.85 + 0.15 * math.sin(self.t * 5.0)
        r     = int(self.r * pulse)
        ix, iy = int(self.x), int(self.y)

        if self.kind == "star":
            col = C["yellow"]
            # glow
            _draw_circle_alpha(surf, (*col, 50), ix, iy, r * 2)
            _draw_star(surf, ix, iy, r, 5, col)
        else:
            col = C["shield"]
            # glow
            _draw_circle_alpha(surf, (*col, 50), ix, iy, r * 2)
            pygame.draw.circle(surf, col, (ix, iy), r, 3)
            # shield symbol
            mid = iy + r // 4
            pygame.draw.line(surf, col, (ix - r // 2, iy - r // 3), (ix,      mid), 3)
            pygame.draw.line(surf, col, (ix + r // 2, iy - r // 3), (ix,      mid), 3)
            pygame.draw.line(surf, col, (ix - r // 2, iy - r // 3), (ix + r // 2, iy - r // 3), 3)

def _draw_circle_alpha(surf, color, cx, cy, r):
    s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    pygame.draw.circle(s, color, (r, r), r)
    surf.blit(s, (cx - r, cy - r))

def _draw_star(surf, cx, cy, r, points, col):
    inner = r * 0.44
    pts   = []
    for i in range(points * 2):
        angle = math.pi / points * i - math.pi / 2
        rad   = r if i % 2 == 0 else inner
        pts.append((cx + math.cos(angle) * rad,
                    cy + math.sin(angle) * rad))
    pygame.draw.polygon(surf, col, pts)

# ──────────────────────────────────────────────
#  CAR DRAWING
# ──────────────────────────────────────────────
# (body_color, accent_color)
CAR_PALETTE = [
    (C["cyan"],   (  0, 100, 140)),
    (C["pink"],   (130,   0,  80)),
    (C["green"],  (  0, 120,  65)),
    (C["orange"], (130,  55,   0)),
    (C["red"],    (120,  20,  20)),
    ((180, 110, 255), (80, 30, 130)),   # purple
]

def draw_car(surf, cx, cy, body, accent, w=46, h=82, flipped=False, shielded=False):
    """Draw a top-down stylised car onto surf centred at (cx, cy)."""
    bw, bh = w, h

    # ── build on a temporary surface ──────────
    s = pygame.Surface((bw + 20, bh + 20), pygame.SRCALPHA)
    ox, oy = 10, 10   # local origin

    # Shadow
    sh_s = pygame.Surface((bw, bh), pygame.SRCALPHA)
    pygame.draw.ellipse(sh_s, (0, 0, 0, 70), (0, 0, bw, bh))
    s.blit(sh_s, (ox + 4, oy + 6))

    # Body base
    pygame.draw.rect(s, body,   (ox + 4,  oy + 8,  bw - 8, bh - 16), border_radius=10)
    pygame.draw.ellipse(s, body, (ox + 6,  oy + 2,  bw - 12, 26))          # nose
    pygame.draw.ellipse(s, body, (ox + 6,  oy + bh - 28, bw - 12, 26))     # tail

    # Windshields
    wsh = (190, 235, 255, 210)
    pygame.draw.ellipse(s, wsh, (ox + 9,  oy + 14, bw - 18, 20))
    pygame.draw.ellipse(s, wsh, (ox + 9,  oy + bh - 34, bw - 18, 16))

    # centre stripe
    pygame.draw.rect(s, (*accent, 230),
                     (ox + bw // 2 - 3, oy + 10, 6, bh - 20), border_radius=3)

    # Headlights
    hl = (255, 255, 200, 240) if not flipped else (*accent, 200)
    pygame.draw.ellipse(s, hl, (ox + 5,  oy + 2,  14,  9))
    pygame.draw.ellipse(s, hl, (ox + bw - 19, oy + 2, 14, 9))

    # Tail-lights
    tl = (*accent, 220) if not flipped else (255, 55, 55, 230)
    pygame.draw.ellipse(s, tl, (ox + 5,  oy + bh - 11, 14, 9))
    pygame.draw.ellipse(s, tl, (ox + bw - 19, oy + bh - 11, 14, 9))

    # Wheels
    for wy in [bh // 4, 3 * bh // 4]:
        for wx in [0, bw - 10]:
            pygame.draw.rect(s, (35, 35, 35), (ox + wx, oy + wy - 11, 10, 22), border_radius=3)
            pygame.draw.rect(s, (170, 175, 195), (ox + wx + 2, oy + wy - 8, 6, 16), border_radius=2)

    if flipped:
        s = pygame.transform.flip(s, False, True)

    # ── shield ring ───────────────────────────
    if shielded:
        r  = max(bw, bh) // 2 + 12
        sg = pygame.Surface((s.get_width() + 30, s.get_height() + 30), pygame.SRCALPHA)
        gx, gy = sg.get_width() // 2, sg.get_height() // 2
        pygame.draw.ellipse(sg, (*C["shield"], 70), (gx - r, gy - r, r * 2, r * 2))
        pygame.draw.ellipse(sg, (*C["shield"], 180), (gx - r, gy - r, r * 2, r * 2), 3)
        surf.blit(sg, (cx - sg.get_width() // 2, cy - sg.get_height() // 2))

    surf.blit(s, (cx - s.get_width() // 2, cy - s.get_height() // 2))

# ──────────────────────────────────────────────
#  ENEMY CAR
# ──────────────────────────────────────────────
class EnemyCar:
    def __init__(self, y_start=-120):
        self.lane  = random.randint(0, N_LANES - 1)
        self.x     = float(ROAD_L + self.lane * LANE_W + LANE_W // 2)
        self.y     = float(y_start)
        ci         = random.randint(0, len(CAR_PALETTE) - 1)
        self.body, self.accent = CAR_PALETTE[ci]
        self.w, self.h         = 46, 82
        self.drift = random.uniform(-35, 25)   # speed offset

    def update(self, dt, road_speed):
        self.y += (road_speed + self.drift) * dt

    def draw(self, surf):
        draw_car(surf, int(self.x), int(self.y), self.body, self.accent, flipped=True)

    def hit_rect(self):
        return pygame.Rect(
            self.x - self.w // 2 + 7,
            self.y - self.h // 2 + 10,
            self.w - 14,
            self.h - 20,
        )

# ──────────────────────────────────────────────
#  LANE STRIPE
# ──────────────────────────────────────────────
class LaneStripe:
    def __init__(self, x, y):
        self.x = x
        self.y = float(y)

    def update(self, dt, road_speed):
        self.y += road_speed * dt
        if self.y > H + 45:
            self.y -= H + 90 + 80

    def draw(self, surf):
        pygame.draw.rect(surf, C["lane"],
                         (self.x - 3, int(self.y), 6, 42), border_radius=3)

# ──────────────────────────────────────────────
#  SCROLLING BACKGROUND STARS
# ──────────────────────────────────────────────
class StarField:
    def __init__(self, count=130):
        self.stars = [
            (random.randint(0, W), random.uniform(0, H), random.uniform(0.3, 1.6))
            for _ in range(count)
        ]
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        for sx, sy, sz in self.stars:
            ny = (sy + self.t * 22 * sz) % H
            a  = int(70 + 120 * sz / 1.6)
            r  = max(1, int(sz * 0.9))
            pygame.draw.circle(surf, (a, a, min(255, a + 20)), (int(sx), int(ny)), r)

# ──────────────────────────────────────────────
#  GAME STATES
# ──────────────────────────────────────────────
S_MENU     = 0
S_PLAYING  = 1
S_PAUSED   = 2
S_GAMEOVER = 3
S_HOWTO    = 4

# ──────────────────────────────────────────────
#  MAIN GAME CLASS
# ──────────────────────────────────────────────
class NeonRush:

    def __init__(self):
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("NeonRush — Car Race")
        self.clock    = pygame.time.Clock()
        self.state    = S_MENU
        self.stars    = StarField()
        self.best, self.top_level = load_best()
        self._build_buttons()
        self._reset()

    # ── Button layout ─────────────────────────
    def _build_buttons(self):
        cx = W // 2
        self.b_start  = Button(cx-155, 455, 310, 58, "START RACE",  C["cyan"],  C["green"])
        self.b_howto  = Button(cx-155, 525, 310, 52, "HOW TO PLAY", C["pink"],  (255, 110, 190))
        self.b_back   = Button(cx-130, 598, 260, 52, "← BACK",      C["gray"],  C["white"])
        self.b_retry  = Button(cx-165, 490, 310, 58, "PLAY AGAIN",  C["cyan"],  C["green"])
        self.b_menu   = Button(cx-165, 562, 310, 52, "MAIN MENU",   C["pink"],  (255, 110, 190))
        self.b_resume = Button(cx-150, 340, 300, 58, "RESUME",      C["green"], C["cyan"])
        self.b_quit   = Button(cx-150, 412, 300, 52, "QUIT TO MENU",C["pink"],  (255, 110, 190))

    # ── Game reset ────────────────────────────
    def _reset(self):
        self.score       = 0
        self.disp_score  = 0
        self.lives       = 3
        self.level       = 1
        self.road_speed  = 255.0
        self.invincible  = 0.0
        self.shield      = False
        self.shield_t    = 0.0
        # Player position
        self.px, self.py = float(W // 2), float(H - 115)
        self.pvx = self.pvy = 0.0
        # Entities
        self.enemies:   list[EnemyCar]  = []
        self.powerups:  list[PowerUp]   = []
        self.particles: list[Particle]  = []
        # Road stripes
        self.stripes: list[LaneStripe] = []
        for lane in range(1, N_LANES):
            sx = ROAD_L + lane * LANE_W
            for j in range(9):
                self.stripes.append(LaneStripe(sx, j * (H // 7)))
        # Spawn timers
        self.enemy_t    = 0.0
        self.enemy_ivl  = 1.8
        self.powerup_t  = 0.0
        self.powerup_ivl = 9.0
        self.score_t    = 0.0
        # FX
        self.flash_t    = 0.0
        self.flash_col  = C["red"]
        self.shake      = 0.0

    # ──────────────────────────────────────────
    #  MAIN LOOP
    # ──────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            self._events()
            self._update(dt)
            self._draw()

    # ── Events ────────────────────────────────
    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if   self.state == S_PLAYING:  self.state = S_PAUSED
                    elif self.state == S_PAUSED:   self.state = S_PLAYING
                    elif self.state == S_MENU:     pygame.quit(); sys.exit()

            if self.state == S_MENU:
                if self.b_start.clicked(ev): self._start()
                if self.b_howto.clicked(ev): self.state = S_HOWTO

            elif self.state == S_HOWTO:
                if self.b_back.clicked(ev): self.state = S_MENU

            elif self.state == S_GAMEOVER:
                if self.b_retry.clicked(ev): self._start()
                if self.b_menu.clicked(ev):
                    self.best, self.top_level = load_best()
                    self.state = S_MENU

            elif self.state == S_PAUSED:
                if self.b_resume.clicked(ev): self.state = S_PLAYING
                if self.b_quit.clicked(ev):
                    self.best, self.top_level = load_best()
                    self.state = S_MENU

    def _start(self):
        self._reset()
        self.state = S_PLAYING

    # ── Update ────────────────────────────────
    def _update(self, dt):
        self.stars.update(dt)

        if self.state == S_MENU:
            self.b_start.update(); self.b_howto.update()
        elif self.state == S_HOWTO:
            self.b_back.update()
        elif self.state == S_GAMEOVER:
            self.b_retry.update(); self.b_menu.update()
        elif self.state == S_PAUSED:
            self.b_resume.update(); self.b_quit.update()
        elif self.state == S_PLAYING:
            self._update_game(dt)

    def _update_game(self, dt):
        keys = pygame.key.get_pressed()

        # ── Player movement (reduced sensitivity) ──
        spd = 320.0          # was 530 — lower = less twitchy
        ax  = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) * spd \
            - (keys[pygame.K_LEFT]  or keys[pygame.K_a]) * spd
        ay  = (keys[pygame.K_DOWN]  or keys[pygame.K_s]) * spd * 0.50 \
            - (keys[pygame.K_UP]    or keys[pygame.K_w]) * spd * 0.50
        fric = 0.26          # was 0.16 — higher = snappier stop, less sliding
        self.pvx = self.pvx * (1 - fric) + ax * dt
        self.pvy = self.pvy * (1 - fric) + ay * dt
        self.px  = clamp(self.px + self.pvx, ROAD_L + 23, ROAD_R - 23)
        self.py  = clamp(self.py + self.pvy, H // 2,      H - 50)

        # ── Road stripes ──
        for s in self.stripes:
            s.update(dt, self.road_speed)

        # ── Spawn enemies ──
        self.enemy_t += dt
        if self.enemy_t >= self.enemy_ivl:
            self.enemy_t = 0.0
            count = 1 + (1 if self.level >= 5 else 0)
            for _ in range(count):
                self.enemies.append(EnemyCar(random.randint(-160, -60)))
            self.enemy_ivl = max(0.45, 1.8 - self.level * 0.13)

        for e in self.enemies:
            e.update(dt, self.road_speed)
        self.enemies = [e for e in self.enemies if e.y < H + 130]

        # ── Spawn power-ups ──
        self.powerup_t += dt
        if self.powerup_t >= self.powerup_ivl:
            self.powerup_t = 0.0
            kind = random.choice(["star", "star", "shield"])
            self.powerups.append(PowerUp(kind, rand_lane_x(), -30))
        for p in self.powerups:
            p.update(dt, self.road_speed)
        self.powerups = [p for p in self.powerups if p.y < H + 70]

        # ── Particles ──
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

        # ── Timers ──
        self.invincible = max(0.0, self.invincible - dt)
        if self.shield_t > 0:
            self.shield_t -= dt
            if self.shield_t <= 0:
                self.shield = False
        self.flash_t = max(0.0, self.flash_t - dt * 3)
        self.shake   = max(0.0, self.shake   - dt * 9)

        # ── Score accrual ──
        self.score_t += dt
        if self.score_t >= 0.08:
            self.score_t = 0.0
            self.score  += self.level
        self.disp_score = int(lerp(self.disp_score, self.score, 0.2))

        # ── Level up ──
        threshold = self.level * 500
        if self.score >= threshold:
            self.level     += 1
            self.road_speed = min(720, 255 + self.level * 48)
            self._burst(W // 2, H // 3, C["yellow"], 35)
            self.flash_t  = 1.0
            self.flash_col = C["yellow"]

        # ── Collision: enemies ──
        pr = pygame.Rect(self.px - 17, self.py - 35, 34, 70)
        for e in self.enemies[:]:
            if pr.colliderect(e.hit_rect()):
                if self.shield or self.invincible > 0:
                    self._burst(e.x, e.y, C["shield"], 22)
                    self.enemies.remove(e)
                else:
                    self._crash(e.x, e.y)
                    self.enemies.remove(e)

        # ── Collision: power-ups ──
        pc = pygame.Rect(self.px - 22, self.py - 42, 44, 84)
        for p in self.powerups[:]:
            if pc.colliderect(pygame.Rect(p.x - p.r, p.y - p.r, p.r * 2, p.r * 2)):
                self.powerups.remove(p)
                if p.kind == "star":
                    self.score   += 50 * self.level
                    self.flash_t  = 0.35
                    self.flash_col = C["yellow"]
                    self._burst(p.x, p.y, C["yellow"], 28)
                else:
                    self.shield   = True
                    self.shield_t = 6.0
                    self.flash_t  = 0.3
                    self.flash_col = C["shield"]
                    self._burst(p.x, p.y, C["shield"], 28)

    def _crash(self, ex, ey):
        self.lives -= 1
        self._burst(ex,     ey,     C["orange"], 45)
        self._burst(self.px, self.py, C["red"],   30)
        self.shake   = 1.6
        self.flash_t  = 0.9
        self.flash_col = C["red"]
        self.invincible = 2.2
        if self.lives <= 0:
            save_best(self.score, self.level)
            self.best, self.top_level = load_best()
            self.state = S_GAMEOVER

    def _burst(self, x, y, color, n=20):
        for _ in range(n):
            self.particles.append(Particle(x, y, color))

    # ──────────────────────────────────────────
    #  DRAW DISPATCH
    # ──────────────────────────────────────────
    def _draw(self):
        if   self.state == S_MENU:     self._draw_menu()
        elif self.state == S_HOWTO:    self._draw_howto()
        elif self.state == S_GAMEOVER: self._draw_gameover()
        elif self.state in (S_PLAYING, S_PAUSED):
            self._draw_game()
            if self.state == S_PAUSED:
                self._draw_pause()
        pygame.display.flip()

    # ── Background ────────────────────────────
    def _draw_bg(self, surf=None):
        s = surf or self.screen
        s.fill(C["bg"])
        self.stars.draw(s)

    # ── Road ──────────────────────────────────
    def _draw_road(self, surf=None):
        s = surf or self.screen
        # Road body
        pygame.draw.rect(s, C["road"], (ROAD_L, 0, ROAD_W, H))
        # Animated kerbs
        ks = 62
        for i in range(H // ks + 3):
            yy = (i * ks + int(self.stars.t * self.road_speed)) % (H + ks) - ks
            kc = C["white"] if i % 2 == 0 else C["red"]
            pygame.draw.rect(s, kc, (ROAD_L - 14, yy, 14, ks))
            pygame.draw.rect(s, kc, (ROAD_R,      yy, 14, ks))
        # Lane stripes
        for stripe in self.stripes:
            stripe.draw(s)
        # Edge glow lines
        pygame.draw.line(s, C["cyan"], (ROAD_L, 0), (ROAD_L, H), 2)
        pygame.draw.line(s, C["cyan"], (ROAD_R, 0), (ROAD_R, H), 2)

    # ── Game frame ────────────────────────────
    def _draw_game(self):
        ox = int(math.sin(self.shake * 38) * self.shake * 7) if self.shake > 0 else 0
        oy = int(math.cos(self.shake * 32) * self.shake * 4) if self.shake > 0 else 0

        # Render scene onto temporary surface so we can shake it
        scene = pygame.Surface((W, H))
        self._draw_bg(scene)
        self._draw_road(scene)

        for p in self.powerups:
            p.draw(scene)
        for e in self.enemies:
            e.draw(scene)
        for p in self.particles:
            p.draw(scene)

        # Player (blink during invincibility)
        if self.invincible <= 0 or int(self.invincible * 10) % 2 == 0:
            draw_car(scene, int(self.px), int(self.py),
                     C["cyan"], (0, 105, 150), shielded=self.shield)

        self.screen.blit(scene, (ox, oy))

        # Flash overlay
        if self.flash_t > 0:
            fl = pygame.Surface((W, H), pygame.SRCALPHA)
            fl.fill((*self.flash_col, min(110, int(self.flash_t * 120))))
            self.screen.blit(fl, (0, 0))

        self._draw_hud()

    # ── HUD ───────────────────────────────────
    def _draw_hud(self):
        bar = pygame.Surface((W, 72), pygame.SRCALPHA)
        bar.fill((*C["dark"], 215))
        self.screen.blit(bar, (0, 0))
        pygame.draw.line(self.screen, C["cyan"], (0, 72), (W, 72), 2)

        pad = 32
        self._hud_item(pad,         "SCORE", str(self.disp_score), C["cyan"])
        self._hud_item(W // 2 - 80, "LIVES", "♥ " * self.lives + "♡ " * (3 - self.lives), C["pink"])
        self._hud_item(W // 2 + 70, "LEVEL", str(self.level),        C["yellow"])
        kmh = int(80 + self.road_speed * 0.45)
        self._hud_item(W - 130,     "SPEED", f"{kmh} kmh",            C["green"])

        # Shield bar
        if self.shield and self.shield_t > 0:
            frac = self.shield_t / 6.0
            bw   = 210
            bx   = W // 2 - bw // 2
            pygame.draw.rect(self.screen, C["dark2"], (bx, 78, bw, 11), border_radius=5)
            pygame.draw.rect(self.screen, C["shield"], (bx, 78, int(bw * frac), 11), border_radius=5)
            lbl = F_SMALL.render("SHIELD", True, C["shield"])
            self.screen.blit(lbl, (bx + bw + 8, 76))

    def _hud_item(self, x, label, value, col):
        l = F_SMALL.render(label, True, C["gray"])
        v = F_BODY.render(value,  True, col)
        self.screen.blit(l, (x, 9))
        self.screen.blit(v, (x, 32))

    # ── Pause overlay ─────────────────────────
    def _draw_pause(self):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 18, 185))
        self.screen.blit(ov, (0, 0))
        cx = W // 2
        box = pygame.Rect(cx - 185, 215, 370, 265)
        pygame.draw.rect(self.screen, C["dark"],  box, border_radius=18)
        pygame.draw.rect(self.screen, C["cyan"],  box, 2, border_radius=18)
        t = F_BIG.render("PAUSED", True, C["cyan"])
        self.screen.blit(t, t.get_rect(center=(cx, 278)))
        self.b_resume.draw(self.screen)
        self.b_quit.draw(self.screen)

    # ── Menu ──────────────────────────────────
    def _draw_menu(self):
        self._draw_bg()
        # faint road strip
        rd = pygame.Surface((ROAD_W + 28, H), pygame.SRCALPHA)
        rd.fill((*C["road"], 90))
        self.screen.blit(rd, (ROAD_L - 14, 0))

        cx = W // 2
        self._draw_title(cx, 150)

        # Stat cards
        stats = [("🏆 BEST", str(self.best), C["cyan"]),
                 ("🔥 LVL",  str(self.top_level), C["pink"])]
        for i, (lbl, val, col) in enumerate(stats):
            bx = cx - 200 + i * 230
            cr = pygame.Rect(bx - 90, 295, 180, 84)
            pygame.draw.rect(self.screen, C["dark2"], cr, border_radius=12)
            pygame.draw.rect(self.screen, col,        cr, 2, border_radius=12)
            ls = F_SMALL.render(lbl, True, C["gray"])
            vs = F_MED.render(val,   True, col)
            self.screen.blit(ls, ls.get_rect(centerx=bx, top=cr.y + 12))
            self.screen.blit(vs, vs.get_rect(centerx=bx, top=cr.y + 42))

        self.b_start.draw(self.screen)
        self.b_howto.draw(self.screen)

        tip = F_SMALL.render("Arrow Keys / W A S D to drive  •  ESC to pause", True, C["gray"])
        self.screen.blit(tip, tip.get_rect(center=(cx, H - 28)))

    def _draw_title(self, cx, cy):
        # glow blob
        gb = pygame.Surface((540, 110), pygame.SRCALPHA)
        pygame.draw.ellipse(gb, (*C["cyan"], 22), gb.get_rect())
        self.screen.blit(gb, (cx - 270, cy - 55))
        # shadow
        sh = F_HUGE.render("NEONRUSH", True, (0, 50, 75))
        self.screen.blit(sh, sh.get_rect(center=(cx + 3, cy + 3)))
        # two-tone title
        t1 = F_HUGE.render("NEON", True, C["cyan"])
        t2 = F_HUGE.render("RUSH", True, C["pink"])
        tw = t1.get_width() + t2.get_width()
        self.screen.blit(t1, (cx - tw // 2,                     cy - t1.get_height() // 2))
        self.screen.blit(t2, (cx - tw // 2 + t1.get_width(),    cy - t2.get_height() // 2))
        # tagline
        tag = F_BODY.render("⚡  HIGH-SPEED NEON RACING  ⚡", True, C["yellow"])
        self.screen.blit(tag, tag.get_rect(center=(cx, cy + 58)))

    # ── How-to-play ───────────────────────────
    def _draw_howto(self):
        self._draw_bg()
        cx = W // 2
        th = F_BIG.render("HOW TO PLAY", True, C["cyan"])
        self.screen.blit(th, th.get_rect(center=(cx, 70)))
        pygame.draw.line(self.screen, C["cyan"], (cx - 200, 103), (cx + 200, 103), 2)

        tips = [
            ("🚗", "Arrow Keys / W A S D  —  steer & accelerate"),
            ("💥", "Avoid crashing into oncoming traffic cars"),
            ("⭐", "Collect gold STARS for big bonus points"),
            ("🛡", "Grab SHIELDS for 6 seconds of invincibility"),
            ("🔥", "Speed ramps up every 500 points — survive!"),
            ("❤", "You have 3 lives. Each crash costs one life"),
            ("⏸", "Press ESC to pause / resume the game"),
        ]
        for i, (icon, text) in enumerate(tips):
            y   = 125 + i * 56
            row = pygame.Rect(cx - 330, y, 660, 48)
            col = C["cyan"] if i % 2 == 0 else C["pink"]
            pygame.draw.rect(self.screen, C["dark2"], row, border_radius=8)
            pygame.draw.rect(self.screen, (*col, 90), row, 1, border_radius=8)
            ic_s = F_BODY.render(icon, True, col)
            tx_s = F_SMALL.render(text, True, C["white"])
            self.screen.blit(ic_s, (row.x + 18, row.y + 11))
            self.screen.blit(tx_s, (row.x + 60, row.y + 14))

        self.b_back.draw(self.screen)

    # ── Game-Over ─────────────────────────────
    def _draw_gameover(self):
        self._draw_bg()
        cx = W // 2
        # overlay
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 10, 155))
        self.screen.blit(ov, (0, 0))

        # Title
        sh = F_HUGE.render("GAME OVER", True, (90, 0, 0))
        self.screen.blit(sh, sh.get_rect(center=(cx + 3, 118)))
        t  = F_HUGE.render("GAME OVER", True, C["red"])
        self.screen.blit(t,  t.get_rect(center=(cx,     115)))

        # Result cards
        results = [
            ("YOUR SCORE", str(self.score), C["cyan"]),
            ("BEST SCORE", str(self.best),  C["yellow"]),
            ("LEVEL",      str(self.level), C["pink"]),
        ]
        spacing = 220
        start_x = cx - spacing
        for i, (lbl, val, col) in enumerate(results):
            bx = start_x + i * spacing
            cr = pygame.Rect(bx - 95, 210, 190, 105)
            pygame.draw.rect(self.screen, C["dark2"], cr, border_radius=14)
            pygame.draw.rect(self.screen, col,        cr, 2, border_radius=14)
            ls = F_SMALL.render(lbl, True, C["gray"])
            vs = F_BIG.render(val,   True, col)
            self.screen.blit(ls, ls.get_rect(centerx=bx, top=cr.y + 14))
            self.screen.blit(vs, vs.get_rect(centerx=bx, top=cr.y + 50))

        # New record badge
        if self.score > 0 and self.score >= self.best:
            badge = F_MED.render("🏆  NEW RECORD!", True, C["yellow"])
            self.screen.blit(badge, badge.get_rect(center=(cx, 345)))

        self.b_retry.draw(self.screen)
        self.b_menu.draw(self.screen)

# ──────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    try:
        game = NeonRush()
        game.run()
    except ImportError:
        print("=" * 52)
        print("  Pygame not found.  Install it with:")
        print("      pip install pygame")
        print("=" * 52)
        sys.exit(1)
