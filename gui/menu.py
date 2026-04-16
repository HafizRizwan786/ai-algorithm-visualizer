# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  CIPHER AI  —  Computational Intelligence Platform for Heuristic       ║
# ║               Exploration & Research                                   ║
# ║  gui/menu.py  ·  Full-Screen Professional Menu                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝
"""
Animations included
───────────────────
  Boot sequence   — 4 loading bars (shown ONCE only; skipped on return)
  Shooting stars  — diagonal streak comets with glowing tail, start ~1-2s in
  Matrix rain     — falling glyphs on left/right margins
  Hex grid        — pulsing honeycomb background
  Particle net    — 90 nodes + proximity connection lines
  Glitch title    — periodic character-scramble on "CIPHER AI"
  Scan-line       — cyan-tinted sweep top-to-bottom
  Typewriter      — subtitle animates in after boot
  HUD             — live clock, session ID, corner brackets
  Card hover      — border glow, fill bar, number colour, arrow reveal
  Pulse dot       — breathing status indicator
  Vignette        — radial dark gradient on every frame

Keyboard shortcuts
──────────────────
  F11 / F  →  toggle full-screen / windowed
  Esc      →  quit
"""

import tkinter as tk
import math, random, time

# ── One-time boot flag (persists across menu re-opens) ───────────────────────
_BOOT_DONE = False

# ── Colour palette ────────────────────────────────────────────────────────────
C = {
    'bg':       '#020b0f',
    'surface':  '#061520',
    'card':     '#071a26',
    'card_h':   '#0c2438',
    'border':   '#0e2a3f',
    'cyan':     '#00d4ff',
    'cyan_dim': '#003a4d',
    'amber':    '#f0a500',
    'amber_dim':'#3a2800',
    'blue':     '#0a3d6b',
    'text':     '#c0e8f8',
    'muted':    '#1a4a60',
    'dim':      '#0a1e2c',
    'rain_col': '#006080',
    'star':     '#e0f4ff',
    'star_tail':'#004060',
}

GLYPHS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789αβγδεζ∑∫∂∇#@&%01'
APP_NAME     = 'CIPHER'
APP_SUBTITLE = 'Computational Intelligence Platform for Heuristic Exploration & Research'
APP_TAGLINE  = 'Search Algorithms  ·  Heuristic Methods  ·  Game Intelligence'


# ─────────────────────────────────────────────────────────────────────────────
# Shooting Star
# ─────────────────────────────────────────────────────────────────────────────
class ShootingStar:
    TAIL_LEN   = 18      # number of tail segments
    SPEED_MIN  = 14
    SPEED_MAX  = 22

    def __init__(self, W, H):
        self.reset(W, H)

    def reset(self, W, H):
        # start from top-left quadrant or top edge
        self.x   = random.uniform(W * 0.05, W * 0.80)
        self.y   = random.uniform(-20, H * 0.25)
        angle    = random.uniform(30, 55)          # degrees from horizontal
        speed    = random.uniform(self.SPEED_MIN, self.SPEED_MAX)
        rad      = math.radians(angle)
        self.vx  = math.cos(rad) * speed
        self.vy  = math.sin(rad) * speed
        self.len = random.randint(10, self.TAIL_LEN)
        self.alive = True
        self.W, self.H = W, H
        # tail: list of (x, y) positions
        self.tail = [(self.x, self.y)] * self.len
        self.brightness = random.uniform(0.6, 1.0)

    def update(self):
        self.tail.pop()
        self.tail.insert(0, (self.x, self.y))
        self.x += self.vx
        self.y += self.vy
        if self.x > self.W + 60 or self.y > self.H + 60:
            self.alive = False

    def draw(self, canvas):
        n = len(self.tail)
        for i in range(n - 1):
            frac = 1.0 - i / n
            a    = int(frac * frac * self.brightness * 220)
            a    = max(0, min(255, a))
            # head is bright white-cyan, tail fades to dark blue
            r = int(180 + frac * 75)
            g = int(220 + frac * 35)
            b = 255
            r, g, b = min(255, r), min(255, g), min(255, b)
            # scale colour by alpha manually (blend toward bg)
            bg = (2, 11, 15)
            r = int(bg[0] + (r - bg[0]) * a / 255)
            g = int(bg[1] + (g - bg[1]) * a / 255)
            b = int(bg[2] + (b - bg[2]) * a / 255)
            col = f'#{r:02x}{g:02x}{b:02x}'
            x1, y1 = self.tail[i]
            x2, y2 = self.tail[i + 1]
            lw = max(0.5, 2.0 * frac)
            canvas.create_line(x1, y1, x2, y2, fill=col, width=lw)


# ─────────────────────────────────────────────────────────────────────────────
# Background canvas
# ─────────────────────────────────────────────────────────────────────────────
class BGCanvas(tk.Canvas):
    FPS        = 40
    N_PART     = 85
    CONN       = 140
    SCAN_SPEED = 2.8
    RAIN_COLS  = 3
    MAX_STARS  = 6
    STAR_DELAY = 80        # frames before first star (~2 s at 40 fps)

    def __init__(self, master, **kw):
        super().__init__(master, bg=C['bg'], highlightthickness=0, **kw)
        self._W = self._H = 1
        self._t       = 0
        self._scan    = 0
        self._alive   = True
        self._parts   = []
        self._drops   = []
        self._hex_cache = []
        self._stars   = []           # active ShootingStars
        self._next_star_frame = self.STAR_DELAY + random.randint(0, 40)
        self.bind('<Configure>', self._on_resize)

    # ── resize ────────────────────────────────────────────────────────────────
    def _on_resize(self, e):
        self._W, self._H = e.width, e.height
        self._parts     = [self._new_part() for _ in range(self.N_PART)]
        col_w = 16
        side_x = []
        for i in range(self.RAIN_COLS):
            side_x.append(8 + i * col_w)
        for i in range(self.RAIN_COLS):
            side_x.append(self._W - 8 - i * col_w)
        self._rain_x = side_x
        self._drops  = [random.uniform(-80, 0) for _ in side_x]
        self._hex_cache = self._build_hex_positions()

    def _new_part(self):
        col = random.choice([C['cyan'], C['amber'],
                             '#0a3d6b', '#0a3d6b', '#0a3d6b'])
        return dict(x=random.uniform(0, self._W),
                    y=random.uniform(0, self._H),
                    vx=random.uniform(-0.36, 0.36),
                    vy=random.uniform(-0.36, 0.36),
                    r=random.uniform(1.4, 2.8),
                    col=col)

    def _build_hex_positions(self):
        r = 36
        dx = r * math.sqrt(3)
        dy = r * 1.5
        hexes, row, y = [], 0, -dy
        while y < self._H + dy:
            col, x = 0, -dx + (dx / 2 if row % 2 else 0)
            while x < self._W + dx:
                hexes.append((x, y, row, col))
                x += dx; col += 1
            y += dy; row += 1
        return hexes

    # ── main draw ─────────────────────────────────────────────────────────────
    def _draw(self):
        if not self._alive:
            return
        W, H = self._W, self._H
        if W < 2 or H < 2:
            self.after(200, self._draw); return

        self.delete('all')
        self._t += 1

        self._draw_hex(W, H)
        self._draw_rain(W, H)
        self._draw_particles(W, H)
        self._update_stars(W, H)
        self._draw_scan(W, H)
        self._draw_vignette(W, H)
        self._draw_corners(W, H)

        self.after(1000 // self.FPS, self._draw)

    # ── hex grid ──────────────────────────────────────────────────────────────
    def _draw_hex(self, W, H):
        r = 36
        for (cx, cy, row, col) in self._hex_cache:
            phase = self._t * 0.014 + row * 0.26 + col * 0.33
            pulse = (math.sin(phase) + 1) / 2
            dist  = math.hypot(cx - W / 2, cy - H / 2) / (W * 0.65)
            alpha = max(0.0, (1.0 - dist) * 0.20 * pulse)
            if alpha < 0.005:
                continue
            pts = []
            for i in range(6):
                a = math.radians(60 * i - 30)
                pts += [cx + (r - 1) * math.cos(a), cy + (r - 1) * math.sin(a)]
            lo, hi = (4, 14, 22), (8, 30, 48)
            rv = int(lo[0] + pulse * (hi[0] - lo[0]))
            gv = int(lo[1] + pulse * (hi[1] - lo[1]))
            bv = int(lo[2] + pulse * (hi[2] - lo[2]))
            self.create_polygon(*pts, outline=f'#{rv:02x}{gv:02x}{bv:02x}', fill='')

    # ── matrix rain ───────────────────────────────────────────────────────────
    def _draw_rain(self, W, H):
        for i, x in enumerate(self._rain_x):
            ch  = random.choice(GLYPHS)
            y   = self._drops[i] * 16
            edge = min(i, len(self._rain_x) - 1 - i) + 1
            b   = min(255, 40 + edge * 22)
            col = f'#{b // 6:02x}{b // 2:02x}{b:02x}'
            self.create_text(x, y, text=ch,
                             font=('Courier', 10), fill=col, anchor='n')
            if y > H and random.random() > 0.96:
                self._drops[i] = 0
            else:
                self._drops[i] += 0.44

    # ── particles ─────────────────────────────────────────────────────────────
    def _draw_particles(self, W, H):
        for p in self._parts:
            p['x'] = (p['x'] + p['vx']) % W
            p['y'] = (p['y'] + p['vy']) % H
        pts = self._parts
        for i, a in enumerate(pts):
            for b in pts[i + 1:]:
                d = math.hypot(a['x'] - b['x'], a['y'] - b['y'])
                if d < self.CONN:
                    self.create_line(a['x'], a['y'], b['x'], b['y'],
                                     fill='#081828', width=0.5)
        for p in pts:
            r = p['r']
            self.create_oval(p['x'] - r, p['y'] - r,
                             p['x'] + r, p['y'] + r,
                             fill=p['col'], outline='')

    # ── shooting stars ────────────────────────────────────────────────────────
    def _update_stars(self, W, H):
        # spawn new star after delay
        if self._t >= self._next_star_frame and len(self._stars) < self.MAX_STARS:
            self._stars.append(ShootingStar(W, H))
            # next star in 1.5 – 5 s
            self._next_star_frame = (self._t
                                     + int(random.uniform(1.5, 5.0) * self.FPS))

        alive = []
        for star in self._stars:
            star.update()
            star.draw(self)
            if star.alive:
                alive.append(star)
        self._stars = alive

    # ── scan-line ─────────────────────────────────────────────────────────────
    def _draw_scan(self, W, H):
        self._scan = (self._scan + self.SCAN_SPEED) % H
        s = self._scan
        for dy, col in [(0, '#001520'), (1, '#000d14'),
                        (2, '#00080c'), (-1, '#000c10')]:
            y = s + dy
            if 0 <= y < H:
                self.create_line(0, y, W, y, fill=col, width=1)

    # ── vignette ──────────────────────────────────────────────────────────────
    def _draw_vignette(self, W, H):
        cx, cy = W / 2, H / 2
        for i in range(10):
            frac = (i + 1) / 10
            rw   = cx * (0.35 + frac * 0.95)
            rh   = cy * (0.35 + frac * 0.95)
            if frac > 0.80:
                g = int(frac ** 2.5 * 80)
                col = f'#{2:02x}{max(2, g//6):02x}{max(4, g//4):02x}'
                self.create_oval(cx - rw, cy - rh, cx + rw, cy + rh,
                                 outline=col, fill='')

    # ── HUD corners ───────────────────────────────────────────────────────────
    def _draw_corners(self, W, H):
        s, p, lw = 36, 8, 2
        corners = [
            [(p, p + s), (p, p), (p + s, p)],
            [(W - p - s, p), (W - p, p), (W - p, p + s)],
            [(p, H - p - s), (p, H - p), (p + s, H - p)],
            [(W - p - s, H - p), (W - p, H - p), (W - p, H - p - s)],
        ]
        for pts in corners:
            flat = [v for pt in pts for v in pt]
            self.create_line(*flat, fill=C['cyan'], width=lw, joinstyle='miter')

    def start(self):
        self.after(120, self._draw)

    def stop(self):
        self._alive = False


# ─────────────────────────────────────────────────────────────────────────────
# Typewriter label
# ─────────────────────────────────────────────────────────────────────────────
class Typewriter(tk.Label):
    def __init__(self, parent, text, speed=50, delay=0, on_done=None, **kw):
        super().__init__(parent, text='', **kw)
        self._full = text; self._speed = speed
        self._on_done = on_done; self._i = 0
        self.after(delay, self._tick)

    def _tick(self):
        cursor = '▌' if self._i < len(self._full) else ''
        self.config(text=self._full[:self._i] + cursor)
        if self._i <= len(self._full):
            self._i += 1
            self.after(self._speed, self._tick)
        elif self._on_done:
            self._on_done()


# ─────────────────────────────────────────────────────────────────────────────
# Glitch label
# ─────────────────────────────────────────────────────────────────────────────
class GlitchLabel(tk.Label):
    def __init__(self, parent, text, glitch_interval=5500,
                 glitch_steps=18, glitch_speed=32, **kw):
        super().__init__(parent, text=text, **kw)
        self._final = text; self._steps = glitch_steps
        self._speed = glitch_speed; self._interval = glitch_interval
        self.after(glitch_interval, self._start_glitch)

    def _start_glitch(self):
        self._gi = 0; self._glitch_frame()

    def _glitch_frame(self):
        if self._gi >= self._steps:
            self.config(text=self._final)
            self.after(self._interval, self._start_glitch)
            return
        frac = self._gi / self._steps
        scrambled = ''.join(
            c if random.random() < frac or not c.strip()
            else random.choice(GLYPHS)
            for c in self._final)
        self.config(text=scrambled)
        self._gi += 1
        self.after(self._speed, self._glitch_frame)


# ─────────────────────────────────────────────────────────────────────────────
# Pulsing ring dot
# ─────────────────────────────────────────────────────────────────────────────
class PulseDot(tk.Canvas):
    def __init__(self, parent, color, size=14, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=C['bg'], highlightthickness=0, **kw)
        self._sz = size; self._t = 0.0
        cx = size / 2; r = cx - 3
        self.create_oval(cx-r, cx-r, cx+r, cx+r, fill=color, outline='')
        self._ring = self.create_oval(2, 2, size-2, size-2,
                                      outline=color, width=1)
        self._color = color
        self._animate()

    def _animate(self):
        self._t += 0.07
        v = (math.sin(self._t) + 1) / 2
        cx = self._sz / 2
        r  = cx * (0.85 + v * 0.65)
        self.coords(self._ring, cx-r, cx-r, cx+r, cx+r)
        self.after(42, self._animate)


# ─────────────────────────────────────────────────────────────────────────────
# Animated game card
# ─────────────────────────────────────────────────────────────────────────────
class GameCard(tk.Frame):
    BAR_SPEED = 16

    def __init__(self, parent, number, title, subtitle, tag,
                 accent, on_click, **kw):
        super().__init__(parent, bg=C['card'],
                         highlightthickness=1,
                         highlightbackground=C['border'],
                         cursor='hand2', **kw)
        self._accent = accent; self._hovered = False
        self._bar_pct = 0; self._bar_job = None

        tk.Frame(self, bg=accent, width=4).pack(side=tk.LEFT, fill=tk.Y)

        body = tk.Frame(self, bg=C['card'], padx=24, pady=18)
        body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        top_row = tk.Frame(body, bg=C['card'])
        top_row.pack(fill=tk.X)

        self._title_lbl = tk.Label(top_row, text=title,
                                   font=('Courier', 17, 'bold'),
                                   fg=accent, bg=C['card'])
        self._title_lbl.pack(side=tk.LEFT)

        self._tag_lbl = tk.Label(top_row, text=f'  {tag}  ',
                                 font=('Courier', 7, 'bold'),
                                 fg=accent, bg=C['dim'], padx=2, pady=2)
        self._tag_lbl.pack(side=tk.LEFT, padx=(12, 0), pady=(5, 0))

        self._sub_lbl = tk.Label(body, text=subtitle,
                                 font=('Courier', 9),
                                 fg=C['muted'], bg=C['card'])
        self._sub_lbl.pack(anchor='w', pady=(7, 0))

        bar_track = tk.Frame(body, bg=C['dim'], height=2)
        bar_track.pack(fill=tk.X, pady=(12, 0))
        self._bar_fill  = tk.Frame(bar_track, bg=accent, height=2, width=0)
        self._bar_fill.place(x=0, y=0, relheight=1)
        self._bar_track = bar_track

        right = tk.Frame(self, bg=C['card'], padx=22)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        self._num_lbl = tk.Label(right, text=number,
                                 font=('Courier', 34, 'bold'),
                                 fg=C['dim'], bg=C['card'])
        self._num_lbl.pack(expand=True)

        self._arrow_lbl = tk.Label(right, text='⟶',
                                   font=('Courier', 18),
                                   fg=accent, bg=C['card'])

        self._all = []
        self._collect(self)
        for w in self._all:
            w.bind('<Enter>',    self._enter)
            w.bind('<Leave>',    self._leave)
            w.bind('<Button-1>', lambda e: on_click())
        self.bind('<Enter>', self._enter)
        self.bind('<Leave>', self._leave)
        self.bind('<Button-1>', lambda e: on_click())

    def _collect(self, w):
        self._all.append(w)
        for c in w.winfo_children():
            self._collect(c)

    def _set_bg(self, bg):
        for w in self._all:
            try: w.config(bg=bg)
            except Exception: pass
        try: self._bar_track.config(bg=C['dim'])
        except Exception: pass

    def _step_bar(self, forward):
        if not forward and self._bar_pct <= 0: return
        if forward and self._bar_pct >= 100: return
        self._bar_pct += 4 if forward else -6
        self._bar_pct  = max(0, min(100, self._bar_pct))
        try:
            tw = self._bar_track.winfo_width()
            self._bar_fill.place(x=0, y=0,
                                 width=int(tw * self._bar_pct / 100),
                                 relheight=1)
        except Exception: pass
        self._bar_job = self.after(self.BAR_SPEED,
                                   lambda: self._step_bar(forward))

    def _cancel_bar(self):
        if self._bar_job:
            self.after_cancel(self._bar_job); self._bar_job = None

    def _enter(self, _=None):
        if self._hovered: return
        self._hovered = True
        self.config(highlightbackground=self._accent)
        self._set_bg(C['card_h'])
        self._num_lbl.config(fg=self._accent)
        self._sub_lbl.config(fg='#4a9aba')
        self._tag_lbl.config(bg=self._accent, fg=C['bg'])
        self._arrow_lbl.config(bg=C['card_h'])
        self._arrow_lbl.pack(expand=True)
        self._cancel_bar(); self._step_bar(True)

    def _leave(self, _=None):
        if not self._hovered: return
        self._hovered = False
        self.config(highlightbackground=C['border'])
        self._set_bg(C['card'])
        self._num_lbl.config(fg=C['dim'])
        self._sub_lbl.config(fg=C['muted'])
        self._tag_lbl.config(bg=C['dim'], fg=self._accent)
        self._arrow_lbl.pack_forget()
        self._cancel_bar(); self._step_bar(False)


# ─────────────────────────────────────────────────────────────────────────────
# Boot screen  (shown once only)
# ─────────────────────────────────────────────────────────────────────────────
class BootScreen(tk.Frame):
    ITEMS = [
        ('CORE ALGORITHMS ', 500),
        ('SEARCH ENGINE   ', 440),
        ('MINIMAX MODULE  ', 580),
        ('NEURAL INTERFACE', 380),
    ]

    def __init__(self, master, on_complete, **kw):
        super().__init__(master, bg=C['bg'], **kw)
        self._on_complete = on_complete

        tk.Label(self, text=APP_NAME,
                 font=('Courier', 52, 'bold'),
                 fg=C['cyan'], bg=C['bg']).pack(pady=(0, 4))
        tk.Label(self, text=APP_SUBTITLE,
                 font=('Courier', 7), fg=C['muted'],
                 bg=C['bg']).pack(pady=(0, 40))

        self._bars, self._oks = [], []
        for label, _ in self.ITEMS:
            row = tk.Frame(self, bg=C['bg'])
            row.pack(fill=tk.X, pady=5)

            tk.Label(row, text=label, font=('Courier', 9),
                     fg=C['muted'], bg=C['bg'],
                     width=20, anchor='w').pack(side=tk.LEFT)

            track = tk.Frame(row, bg=C['dim'], height=2, width=160)
            track.pack(side=tk.LEFT, padx=(10, 0))
            track.pack_propagate(False)
            fill = tk.Frame(track, bg=C['cyan'], height=2, width=0)
            fill.place(x=0, y=0, relheight=1)
            self._bars.append((fill, track))

            ok = tk.Label(row, text='', font=('Courier', 8, 'bold'),
                          fg=C['amber'], bg=C['bg'], width=4)
            ok.pack(side=tk.LEFT, padx=(8, 0))
            self._oks.append(ok)

        self._status = tk.Label(self, text='INITIALIZING SYSTEMS...',
                                font=('Courier', 8),
                                fg=C['cyan'], bg=C['bg'])
        self._status.pack(pady=(28, 0))
        self._blink()
        self.after(300, lambda: self._animate_bar(0))

    def _blink(self):
        cur = self._status.cget('fg')
        self._status.config(fg=C['cyan'] if cur == C['bg'] else C['bg'])
        self.after(520, self._blink)

    def _animate_bar(self, idx, pct=0.0):
        if idx >= len(self._bars):
            self._status.config(text='BOOT COMPLETE', fg=C['amber'])
            self.after(700, self._on_complete)
            return
        fill, track = self._bars[idx]
        _, dur = self.ITEMS[idx]
        steps = 60
        delay = dur // steps
        if pct <= 100:
            tw = max(1, track.winfo_width())
            fill.place(x=0, y=0, width=int(tw * pct / 100), relheight=1)
            self.after(delay,
                       lambda: self._animate_bar(idx, pct + 100 / steps))
        else:
            fill.place(x=0, y=0, relwidth=1, relheight=1)
            self._oks[idx].config(text='OK')
            self.after(100, lambda: self._animate_bar(idx + 1))


# ─────────────────────────────────────────────────────────────────────────────
# HUD overlay
# ─────────────────────────────────────────────────────────────────────────────
def _make_hud(root):
    kw = dict(font=('Courier', 8), fg=C['muted'], bg=C['bg'])
    clock = tk.Label(root, **kw)
    clock.place(relx=1, x=-55, y=20, anchor='ne')
    tk.Label(root, text=f'{APP_NAME} v3.0  ·  KERNEL:ACTIVE',
             **kw).place(x=55, y=20)
    tk.Label(root, text='SESSION:AI-LAB-2025',
             **kw).place(x=55, rely=1, y=-18, anchor='sw')
    tk.Label(root, text='ESC:EXIT  F11:WINDOW',
             **kw).place(relx=1, rely=1, x=-55, y=-18, anchor='se')

    def _tick():
        clock.config(text=time.strftime('%H:%M:%S'))
        root.after(1000, _tick)
    _tick()


# ─────────────────────────────────────────────────────────────────────────────
# Main menu UI  (built after boot)
# ─────────────────────────────────────────────────────────────────────────────
def _build_main(root, bg_canvas):
    SW    = root.winfo_screenwidth()
    MAX_W = min(680, int(SW * 0.56))

    ov = tk.Frame(root, bg=C['bg'])
    ov.place(relx=.5, rely=.5, anchor='center', width=MAX_W)

    # brand row
    br = tk.Frame(ov, bg=C['bg'])
    br.pack(fill=tk.X, pady=(0, 12))
    tk.Frame(br, bg=C['dim'], height=1).pack(
        side=tk.LEFT, fill=tk.X, expand=True, pady=8)
    tk.Label(br, text=f'  ◆  {APP_NAME} AI RESEARCH  ◆  ',
             font=('Courier', 8, 'bold'),
             fg=C['bg'], bg=C['cyan'],
             padx=4, pady=3).pack(side=tk.LEFT, padx=10)
    tk.Label(br, text='v3.0',
             font=('Courier', 8), fg=C['muted'],
             bg=C['bg']).pack(side=tk.LEFT, padx=(0, 10))
    tk.Frame(br, bg=C['dim'], height=1).pack(
        side=tk.LEFT, fill=tk.X, expand=True, pady=8)

    # eyebrow
    tk.Label(ov, text='◆   ARTIFICIAL INTELLIGENCE LABORATORY   ◆',
             font=('Courier', 8), fg=C['dim'],
             bg=C['bg']).pack(pady=(0, 10))

    # glitch title
    title_sz = max(26, min(44, int(SW * 0.030)))
    GlitchLabel(ov, text=f'{APP_NAME} AI',
                glitch_interval=5500,
                glitch_steps=18,
                glitch_speed=32,
                font=('Courier', title_sz, 'bold'),
                fg=C['text'], bg=C['bg']).pack()

    # typewriter subtitle
    Typewriter(ov,
               text=APP_TAGLINE,
               speed=18, delay=200,
               font=('Courier', 9), fg=C['muted'],
               bg=C['bg']).pack(pady=(8, 4))

    tk.Label(ov,
             text='BUILD 2025.3  ·  SEARCH & GAME INTELLIGENCE PLATFORM',
             font=('Courier', 8), fg=C['dim'],
             bg=C['bg']).pack(pady=(0, 28))

    # divider
    dv = tk.Frame(ov, bg=C['bg'])
    dv.pack(fill=tk.X, pady=(0, 16))
    tk.Frame(dv, bg=C['dim'], height=1).pack(
        side=tk.LEFT, fill=tk.X, expand=True, pady=8)
    tk.Label(dv, text='  ◈  SELECT MODULE  ◈  ',
             font=('Courier', 8), fg=C['muted'],
             bg=C['bg']).pack(side=tk.LEFT)
    tk.Frame(dv, bg=C['dim'], height=1).pack(
        side=tk.LEFT, fill=tk.X, expand=True, pady=8)

    # launchers
    def launch(opener):
        bg_canvas.stop()
        root.destroy()
        opener()

    def open_puzzle():
        from gui.puzzle_gui import PuzzleApp
        r2 = tk.Tk()
        r2.attributes('-fullscreen', True)
        PuzzleApp(r2)
        r2.mainloop()
        # after puzzle closes, reopen menu WITHOUT boot
        start_menu()

    def open_ttt():
        from gui.tictactoe_gui import TicTacToeApp
        r2 = tk.Tk()
        r2.attributes('-fullscreen', True)
        TicTacToeApp(r2)
        r2.mainloop()
        # after TTT closes, reopen menu WITHOUT boot
        start_menu()

    games = [
        ('01', '15-PUZZLE SOLVER',
         'BFS  ·  DFS  ·  A* Manhattan  ·  A* Misplaced Tiles',
         'SEARCH ENGINE',     C['cyan'],  lambda: launch(open_puzzle)),
        ('02', 'TIC-TAC-TOE ENGINE',
         'Minimax  ·  Alpha-Beta Pruning  ·  Optimal Decision Tree',
         'GAME INTELLIGENCE', C['amber'], lambda: launch(open_ttt)),
    ]

    for num, title, sub, tag, accent, cmd in games:
        GameCard(ov, num, title, sub, tag, accent, cmd
                 ).pack(fill=tk.X, pady=9, ipady=4)

    # status bar
    sf = tk.Frame(ov, bg=C['bg'])
    sf.pack(fill=tk.X, pady=(24, 0))
    tk.Frame(sf, bg=C['dim'], height=1).pack(fill=tk.X, pady=(0, 10))

    row = tk.Frame(sf, bg=C['bg'])
    row.pack(fill=tk.X)

    PulseDot(row, C['cyan'], size=12).pack(side=tk.LEFT, padx=(0, 8))
    tk.Label(row, text='ALL SYSTEMS ONLINE',
             font=('Courier', 8), fg='#0a4a5a',
             bg=C['bg']).pack(side=tk.LEFT)

    for txt in ['GROUP ≤ 5', 'VIVA + CODE + REPORT']:
        tk.Frame(row, bg=C['dim'], width=1,
                 height=12).pack(side=tk.LEFT, padx=14)
        tk.Label(row, text=txt,
                 font=('Courier', 8), fg=C['dim'],
                 bg=C['bg']).pack(side=tk.LEFT)

    tk.Label(row, text='[ESC] QUIT   [F11] TOGGLE',
             font=('Courier', 7), fg=C['dim'],
             bg=C['bg']).pack(side=tk.RIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point  — boot shown only on first call
# ─────────────────────────────────────────────────────────────────────────────
def start_menu():
    global _BOOT_DONE

    root = tk.Tk()
    root.title(f"{APP_NAME} AI — Artificial Intelligence Research Platform")
    root.configure(bg=C['bg'])
    root.attributes('-fullscreen', True)
    root.bind('<Escape>', lambda e: root.destroy())
    root.bind('<F11>',    lambda e: root.attributes(
        '-fullscreen', not root.attributes('-fullscreen')))
    root.bind('<f>',      lambda e: root.attributes(
        '-fullscreen', not root.attributes('-fullscreen')))

    SW = root.winfo_screenwidth()
    SH = root.winfo_screenheight()

    bg = BGCanvas(root, width=SW, height=SH)
    bg.place(x=0, y=0, relwidth=1, relheight=1)
    bg.start()

    _make_hud(root)

    if not _BOOT_DONE:
        # ── first launch: show boot screen ───────────────────────────────────
        _BOOT_DONE = True
        boot_frame = tk.Frame(root, bg=C['bg'])
        boot_frame.place(relx=.5, rely=.5, anchor='center',
                         width=min(500, int(SW * 0.42)))

        def on_boot_done():
            boot_frame.destroy()
            _build_main(root, bg)

        BootScreen(boot_frame, on_complete=on_boot_done).pack(fill=tk.BOTH)
    else:
        # ── returning from a game: skip straight to menu ──────────────────────
        _build_main(root, bg)

    root.mainloop()


if __name__ == '__main__':
    start_menu()