import tkinter as tk
from tkinter import ttk
import threading
import math
import time

from models.puzzle import generate_puzzle, get_blank, GOAL
from algorithms.bfs   import bfs
from algorithms.dfs   import dfs
from algorithms.astar import astar

# ── CIPHER AI palette ─────────────────────────────────────────────────────────
C = {
    'bg':       '#020b0f',
    'surface':  '#061520',
    'card':     '#071a26',
    'card_h':   '#0c2438',
    'border':   '#0e2a3f',
    'cyan':     '#00d4ff',
    'amber':    '#f0a500',
    'text':     '#c0e8f8',
    'muted':    '#1a4a60',
    'dim':      '#0a1e2c',
    'red':      '#ff5d73',
    'green':    '#00f2c3',
    'shadow':   '#010608',
    'tile':     '#071e30',
    'tile_sol': '#031a0e',
    'blank':    '#020d14',
}

TILE = 118          # large tile → fills the left half of the screen
FONT = 'Courier New'

ALGO_COLOR = {
    'BFS':   '#3b82f6',
    'DFS':   '#8b5cf6',
    'A* h1': '#f0a500',
    'A* h2': '#00f2c3',
}


class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("15-Puzzle Solver")
        self.root.configure(bg=C['bg'])
        self.root.resizable(True, True)

        self.algo_var  = tk.StringVar(value="A* h2")
        self.state     = generate_puzzle()
        self.sol_path  = []
        self.anim_step = 0
        self.anim_id   = None
        self.solving   = False

        self._build_ui()
        self._draw_board()
        self._clock_tick()
        self._pulse_tick()

    # ─────────────────────────────────────────────────────────────────────────
    #  Helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _clock_tick(self):
        try:
            self._clock_lbl.config(text=time.strftime('%H:%M:%S'))
            self.root.after(1000, self._clock_tick)
        except tk.TclError:
            pass

    def _pulse_tick(self, t=0):
        try:
            v = (math.sin(t * 0.12) + 1) / 2
            r = 3 + v * 3.5
            cx, cy = 5.5, 6.5
            self._pc.coords(self._prg, cx-r, cy-r, cx+r, cy+r)
            self.root.after(50, lambda: self._pulse_tick(t + 1))
        except tk.TclError:
            pass

    def _section(self, parent, label):
        f = tk.Frame(parent, bg=C['bg'])
        f.pack(fill=tk.X, pady=(10, 4))
        tk.Label(f, text=label, font=(FONT, 8, 'bold'),
                 fg=C['cyan'], bg=C['bg']).pack(side=tk.LEFT)
        tk.Frame(f, bg=C['border'], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0), pady=6)

    def _draw_corners(self, canvas, W, H, color):
        s, p, lw = 20, 7, 2
        segs = [
            [(p, p+s), (p, p),         (p+s, p)],
            [(W-p-s, p), (W-p, p),     (W-p, p+s)],
            [(p, H-p-s), (p, H-p),     (p+s, H-p)],
            [(W-p-s, H-p), (W-p, H-p), (W-p, H-p-s)],
        ]
        for pts in segs:
            flat = [v for xy in pts for v in xy]
            canvas.create_line(*flat, fill=color, width=lw, joinstyle='miter')

    # ─────────────────────────────────────────────────────────────────────────
    #  BUILD UI
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root_pad = tk.Frame(self.root, bg=C['bg'], padx=22, pady=16)
        root_pad.pack(fill=tk.BOTH, expand=True)

        # ── Full-width top HUD bar ────────────────────────────────────────
        self._build_hud(root_pad)

        # ── Cyan underline under HUD ──────────────────────────────────────
        ul = tk.Canvas(root_pad, height=2, bg=C['bg'], highlightthickness=0)
        ul.pack(fill=tk.X, pady=(0, 14))
        ul.bind('<Configure>',
                lambda e: (ul.delete('all'),
                           ul.create_line(0, 1, e.width, 1,
                                          fill=C['cyan'], width=2)))

        # ── Upper section: board LEFT  |  gap  |  controls RIGHT ─────────
        upper = tk.Frame(root_pad, bg=C['bg'])
        upper.pack(fill=tk.BOTH, expand=True)

        self._build_board_col(upper)    # side=LEFT
        self._build_right_col(upper)    # side=RIGHT  (packed before spacer)
        # Transparent middle gap
        tk.Frame(upper, bg=C['bg']).pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ── Divider ───────────────────────────────────────────────────────
        tk.Frame(root_pad, bg=C['border'], height=1).pack(
            fill=tk.X, pady=(14, 10))

        # ── Full-width history table at bottom ────────────────────────────
        self._build_history(root_pad)
        self._build_hud_bottom(root_pad)

    # ── Full-width top HUD ────────────────────────────────────────────────────
    def _build_hud(self, parent):
        f = tk.Frame(parent, bg=C['bg'])
        f.pack(fill=tk.X, pady=(0, 0))

        # Back
        tk.Button(f, text='← MENU',
                  command=self._back,
                  font=(FONT, 9, 'bold'),
                  fg=C['muted'], bg=C['card'],
                  activeforeground=C['text'],
                  activebackground=C['border'],
                  relief=tk.FLAT,
                  highlightthickness=1,
                  highlightbackground=C['border'],
                  padx=10, pady=4,
                  cursor='hand2').pack(side=tk.LEFT)

        # Logo + pulse
        tk.Label(f, text='CIPHER',
                 font=(FONT, 11, 'bold'),
                 fg=C['cyan'], bg=C['bg']).pack(side=tk.LEFT, padx=(14, 0))

        self._pc = tk.Canvas(f, width=76, height=14,
                             bg=C['bg'], highlightthickness=0)
        self._pc.pack(side=tk.LEFT, padx=(10, 0))
        self._pc.create_oval(2, 3, 9, 10, fill=C['cyan'], outline='')
        self._prg = self._pc.create_oval(0, 1, 11, 12,
                                         outline=C['cyan'], width=1)
        self._pc.create_text(15, 7, text='ONLINE',
                             font=(FONT, 8), fill=C['muted'], anchor='w')

        # Centred page title
        tk.Label(f, text='15 - P U Z Z L E   S O L V E R',
                 font=(FONT, 14, 'bold'),
                 fg=C['text'], bg=C['bg']).pack(side=tk.LEFT, expand=True)

        # Clock
        self._clock_lbl = tk.Label(f, text='00:00:00',
                                   font=(FONT, 8),
                                   fg=C['muted'], bg=C['bg'])
        self._clock_lbl.pack(side=tk.RIGHT)

    # ── LEFT column: big puzzle board ─────────────────────────────────────────
    def _build_board_col(self, parent):
        col = tk.Frame(parent, bg=C['bg'])
        col.pack(side=tk.LEFT, anchor='n')

        # Section label
        sh = tk.Frame(col, bg=C['bg'])
        sh.pack(fill=tk.X, pady=(0, 10))
        tk.Label(sh, text='PUZZLE BOARD',
                 font=(FONT, 8, 'bold'),
                 fg=C['cyan'], bg=C['bg']).pack(side=tk.LEFT)
        tk.Frame(sh, bg=C['border'], height=1).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0), pady=6)

        sz = 4 * TILE   # e.g. 472

        # Three-layer decorative border
        outer = tk.Frame(col, bg=C['amber'], padx=3, pady=3)
        outer.pack()
        mid   = tk.Frame(outer, bg=C['border'], padx=1, pady=1)
        mid.pack()
        inner = tk.Frame(mid, bg=C['surface'], padx=10, pady=10)
        inner.pack()

        # Decoration canvas with HUD corners
        deco = tk.Canvas(inner, width=sz + 22, height=sz + 22,
                         bg=C['surface'], highlightthickness=0)
        deco.pack()
        self._draw_corners(deco, sz + 22, sz + 22, C['cyan'])

        # Actual board canvas
        self.canvas = tk.Canvas(deco, width=sz, height=sz,
                                bg=C['blank'], highlightthickness=0,
                                cursor='hand2')
        deco.create_window(11, 11, anchor='nw', window=self.canvas)
        self.canvas.bind('<Button-1>', self._on_click)

        # Status label under board
        self._board_lbl = tk.Label(col,
                                   text='CLICK TILE ADJACENT TO BLANK TO MOVE',
                                   font=(FONT, 8),
                                   fg=C['muted'], bg=C['bg'])
        self._board_lbl.pack(pady=(10, 0))

    # ── RIGHT column: controls flush to the right edge ────────────────────────
    def _build_right_col(self, parent):
        col = tk.Frame(parent, bg=C['bg'], width=230)
        col.pack(side=tk.RIGHT, fill=tk.Y, anchor='n')
        col.pack_propagate(False)

        # Algorithm selector
        self._section(col, 'SELECT ALGORITHM')

        radio_frame = tk.Frame(col, bg=C['card'],
                               highlightthickness=1,
                               highlightbackground=C['border'])
        radio_frame.pack(fill=tk.X, pady=(0, 6))

        for algo in ['BFS', 'DFS', 'A* h1', 'A* h2']:
            accent = ALGO_COLOR[algo]
            row = tk.Frame(radio_frame, bg=C['card'], padx=10, pady=7)
            row.pack(fill=tk.X)
            tk.Frame(row, bg=accent, width=3).pack(
                side=tk.LEFT, fill=tk.Y, padx=(0, 8))
            tk.Radiobutton(row, text=algo,
                           variable=self.algo_var, value=algo,
                           font=(FONT, 10),
                           fg=accent, bg=C['card'],
                           selectcolor=C['surface'],
                           activebackground=C['card'],
                           activeforeground=accent,
                           cursor='hand2').pack(side=tk.LEFT)

        # Action buttons
        self._section(col, 'CONTROLS')

        for txt, cmd, accent in [
            ('🔀  NEW PUZZLE',  self._new_puzzle, C['muted']),
            ('▶   SOLVE',       self._solve,      C['green']),
            ('⏹   STOP',        self._stop,       C['red']),
            ('▶▶  COMPARE ALL', self._compare_all, C['amber']),
        ]:
            tk.Button(col, text=txt, command=cmd,
                      font=(FONT, 9, 'bold'),
                      fg=accent, bg=C['card'],
                      activeforeground=C['text'],
                      activebackground=C['card_h'],
                      relief=tk.FLAT,
                      highlightthickness=1,
                      highlightbackground=accent,
                      padx=12, pady=7,
                      cursor='hand2', anchor='w').pack(fill=tk.X, pady=2)

        # Live stats
        self._section(col, 'LAST RUN STATS')

        stats_frame = tk.Frame(col, bg=C['card'],
                               highlightthickness=1,
                               highlightbackground=C['border'])
        stats_frame.pack(fill=tk.X)

        self.sv = {}
        for label, key, color in [
            ('STATUS', 'Status', C['text']),
            ('NODES',  'Nodes',  '#3b82f6'),
            ('STEPS',  'Steps',  C['green']),
            ('TIME',   'Time',   C['amber']),
        ]:
            r = tk.Frame(stats_frame, bg=C['card'], padx=10, pady=6)
            r.pack(fill=tk.X)
            tk.Label(r, text=label + ':',
                     font=(FONT, 8, 'bold'),
                     fg=C['muted'], bg=C['card'],
                     width=8, anchor='w').pack(side=tk.LEFT)
            v = tk.StringVar(value='-')
            tk.Label(r, textvariable=v,
                     font=(FONT, 9, 'bold'),
                     fg=color, bg=C['card']).pack(side=tk.LEFT)
            self.sv[key] = v

    # ── Full-width history table at the bottom ────────────────────────────────
    def _build_history(self, parent):
        hdr = tk.Frame(parent, bg=C['bg'])
        hdr.pack(fill=tk.X, pady=(0, 6))
        tk.Label(hdr, text='ALGORITHM RUN HISTORY',
                 font=(FONT, 10, 'bold'),
                 fg=C['cyan'], bg=C['bg']).pack(side=tk.LEFT)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('CIPHER.Treeview',
                        background=C['card'],
                        foreground=C['text'],
                        fieldbackground=C['card'],
                        rowheight=28, borderwidth=0,
                        font=(FONT, 9))
        style.configure('CIPHER.Treeview.Heading',
                        background=C['surface'],
                        foreground=C['amber'],
                        font=(FONT, 9, 'bold'),
                        relief='flat')
        style.map('CIPHER.Treeview',
                  background=[('selected', '#0c2438')],
                  foreground=[('selected', C['text'])])

        cols = ('Algorithm', 'Nodes', 'Steps', 'Time (s)', 'Result')

        tv_wrap = tk.Frame(parent, bg=C['card'],
                           highlightthickness=1,
                           highlightbackground=C['border'])
        tv_wrap.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(tv_wrap, orient=tk.VERTICAL)
        self.tree = ttk.Treeview(tv_wrap, columns=cols,
                                 show='headings', height=5,
                                 style='CIPHER.Treeview',
                                 yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)

        for col, w in zip(cols, [140, 130, 110, 120, 120]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor='center', minwidth=w)

        for algo, color in ALGO_COLOR.items():
            self.tree.tag_configure(algo, foreground=color)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _build_hud_bottom(self, parent):
        f = tk.Frame(parent, bg=C['bg'])
        f.pack(fill=tk.X, pady=(8, 0))
        tk.Label(f, text='CIPHER AI  ·  SEARCH ENGINE MODULE',
                 font=(FONT, 8), fg=C['muted'], bg=C['bg']).pack(side=tk.LEFT)
        tk.Label(f, text='BUILD 2025.3',
                 font=(FONT, 8), fg=C['muted'], bg=C['bg']).pack(side=tk.RIGHT)

    # ─────────────────────────────────────────────────────────────────────────
    #  DRAW BOARD  — logic unchanged
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_board(self):
        self.canvas.delete("all")
        solved = (self.state == GOAL)
        for i, val in enumerate(self.state):
            r, c = divmod(i, 4)
            x0 = c * TILE + 4;  y0 = r * TILE + 4
            x1 = x0 + TILE - 4; y1 = y0 + TILE - 4

            color = (C['blank'] if val == 0 else
                     C['tile_sol'] if solved else
                     C['tile'])

            if val != 0:
                self.canvas.create_rectangle(x0+3, y0+3, x1+3, y1+3,
                                             fill=C['shadow'], outline='')

            self.canvas.create_rectangle(x0, y0, x1, y1,
                                         fill=color,
                                         outline=C['border'], width=1)
            if val:
                self.canvas.create_oval(x1-12, y0+6, x1-6, y0+12,
                                        fill=C['green'] if solved else C['cyan'],
                                        outline='')
                self.canvas.create_text(
                    (x0+x1)//2, (y0+y1)//2,
                    text=str(val),
                    font=(FONT, 26, 'bold'),
                    fill=C['green'] if solved else C['text'])

        if solved:
            self._board_lbl.config(
                text='SOLVED  ✔  PUZZLE COMPLETE', fg=C['green'])
        else:
            self._board_lbl.config(
                text='CLICK TILE ADJACENT TO BLANK TO MOVE', fg=C['muted'])

    # ─────────────────────────────────────────────────────────────────────────
    #  ALL EVENTS & SOLVER LOGIC — unchanged from original
    # ─────────────────────────────────────────────────────────────────────────
    def _on_click(self, event):
        if self.solving: return
        col = event.x // TILE
        row = event.y // TILE
        if not (0 <= col < 4 and 0 <= row < 4): return
        idx = row * 4 + col
        blank = get_blank(self.state)
        br, bc = divmod(blank, 4)
        tr, tc = divmod(idx, 4)
        if abs(br-tr) + abs(bc-tc) == 1:
            s = list(self.state)
            s[blank], s[idx] = s[idx], s[blank]
            self.state = tuple(s)
            self._draw_board()

    def _new_puzzle(self):
        self._stop()
        self.state = generate_puzzle()
        self._draw_board()
        for v in self.sv.values(): v.set("-")

    def _solve(self):
        if self.solving: return
        self._stop()
        self.solving = True
        algo = self.algo_var.get()
        self.sv["Status"].set("Solving…")
        self.root.update()

        def run():
            try:
                snap = self.state
                if algo == "BFS":
                    path, nodes, t = bfs(snap)
                elif algo == "DFS":
                    path, nodes, t = dfs(snap)
                elif algo == "A* h1":
                    path, nodes, t = astar(snap, heuristic='h1')
                else:
                    path, nodes, t = astar(snap, heuristic='h2')

                def update():
                    if path:
                        steps = len(path) - 1
                        self.sol_path  = path
                        self.sv["Status"].set("✔ Found!")
                        self.sv["Nodes"].set(str(nodes))
                        self.sv["Steps"].set(str(steps))
                        self.sv["Time"].set(f"{t:.3f}s")
                        self.tree.insert("", tk.END,
                                         values=(algo, nodes, steps,
                                                 f"{t:.3f}", "✔ Found"),
                                         tags=(algo,))
                        self.anim_step = 0
                        self._animate()
                    else:
                        self.sv["Status"].set("✘ Limit Reached")
                        self.sv["Nodes"].set(str(nodes))
                        self.sv["Steps"].set("-")
                        self.tree.insert("", tk.END,
                                         values=(algo, nodes, "N/A",
                                                 f"{t:.3f}", "✘ Limit"),
                                         tags=(algo,))
                    self.tree.yview_moveto(1)
                    self.solving = False

                self.root.after(0, update)
            except Exception as e:
                self.root.after(0, lambda: self.sv["Status"].set(f"Error: {e}"))
                self.solving = False

        threading.Thread(target=run, daemon=True).start()

    def _animate(self):
        if self.anim_step < len(self.sol_path):
            self.state = self.sol_path[self.anim_step]
            self._draw_board()
            self.anim_step += 1
            self.anim_id = self.root.after(200, self._animate)

    def _stop(self):
        if self.anim_id:
            self.root.after_cancel(self.anim_id)
            self.anim_id = None
        self.solving = False

    def _compare_all(self):
        if self.solving: return
        self._stop()
        self.sv["Status"].set("Running all…")
        self.root.update()
        snap = self.state

        def run():
            results = []
            for name, fn in [
                ("BFS",   lambda s=snap: bfs(s)),
                ("DFS",   lambda s=snap: dfs(s)),
                ("A* h1", lambda s=snap: astar(s, heuristic='h1')),
                ("A* h2", lambda s=snap: astar(s, heuristic='h2')),
            ]:
                path, nodes, elapsed = fn()
                steps  = str(len(path)-1) if path else "N/A"
                result = "✔ Found" if path else "✘ Limit"
                results.append((name, str(nodes), steps, f"{elapsed:.3f}", result))

            def insert_rows():
                for vals in results:
                    self.tree.insert("", tk.END, values=vals, tags=(vals[0],))
                self.sv["Status"].set("✔ Done")
                self.tree.yview_moveto(1)

            self.root.after(0, insert_rows)

        threading.Thread(target=run, daemon=True).start()

    def _back(self):
        self._stop()
        self.root.destroy()
        import importlib, gui.menu as m
        importlib.reload(m)
        m.start_menu()