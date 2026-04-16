import tkinter as tk
from tkinter import ttk
import threading

from models.puzzle import generate_puzzle, get_blank, GOAL
from algorithms.bfs   import bfs
from algorithms.dfs   import dfs
from algorithms.astar import astar

# Refined, modern dark theme palette
C = {
    'bg':    '#1e1e2e',
    'panel': '#27293d',
    'tile':  '#32325d',
    'blank': '#141420',
    'text':  '#f8f8f2',
    'red':   '#ff5d73',
    'green': '#00f2c3',
    'gold':  '#ffb86c',
    'dim':   '#8b8b8b',
    'shadow':'#0a0a14'
}
TILE = 90

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

    # ── BUILD UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        wrap = tk.Frame(self.root, bg=C['bg'])
        wrap.pack(padx=25, pady=25, fill=tk.BOTH, expand=True)

        # ── Title row with BACK BUTTON ────────────────────────────────────
        title_row = tk.Frame(wrap, bg=C['bg'])
        title_row.pack(fill=tk.X, pady=(0, 18))

        tk.Button(
            title_row, text="⬅ Back to Menu",
            command=self._back,
            font=("Helvetica", 10, "bold"),
            fg=C['text'], bg='#3d3f54',
            activebackground='#4a4c66', activeforeground='white',
            relief=tk.FLAT, padx=12, pady=6, cursor='hand2'
        ).pack(side=tk.LEFT)

        tk.Label(
            title_row, text="  15-PUZZLE SOLVER",
            font=("Helvetica", 18, "bold"),
            fg=C['text'], bg=C['bg']
        ).pack(side=tk.LEFT)

        body = tk.Frame(wrap, bg=C['bg'])
        body.pack(fill=tk.BOTH, expand=True)

        # ── Board canvas ──────────────────────────────────────────────────
        bf = tk.Frame(body, bg=C['bg'])
        bf.pack(side=tk.LEFT, padx=(0, 25))

        sz = 4 * TILE + 8
        self.canvas = tk.Canvas(bf, width=sz, height=sz,
                                bg=C['blank'], highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)

        # ── Right panel ───────────────────────────────────────────────────
        pnl = tk.Frame(body, bg=C['panel'], padx=20, pady=20)
        pnl.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(pnl, text="ALGORITHM",
                 font=("Helvetica", 10, "bold"),
                 fg=C['dim'], bg=C['panel']).pack(anchor='w', pady=(0, 5))

        for algo in ["BFS", "DFS", "A* h1", "A* h2"]:
            tk.Radiobutton(pnl, text=algo, variable=self.algo_var, value=algo,
                           font=("Helvetica", 10), fg=C['text'],
                           bg=C['panel'], selectcolor=C['bg'],
                           activebackground=C['panel'], activeforeground=C['text']).pack(anchor='w', pady=2)

        tk.Frame(pnl, height=15, bg=C['panel']).pack()

        for txt, cmd, color, hover in [
            ("🔀  New Puzzle", self._new_puzzle, '#3d3f54', '#4a4c66'),
            ("▶   Solve",      self._solve,      C['green'],  '#1ae5bc'),
            ("⏹   Stop",       self._stop,       C['red'],    '#ff788a')
        ]:
            tk.Button(pnl, text=txt, command=cmd,
                      font=("Helvetica", 10, "bold"),
                      fg='#1e1e2e' if color == C['green'] else 'white', 
                      bg=color, activebackground=hover, activeforeground='white', 
                      relief=tk.FLAT, padx=8, pady=6, width=16,
                      cursor='hand2').pack(pady=4)

        tk.Frame(pnl, height=15, bg=C['panel']).pack()

        tk.Label(pnl, text="CURRENT STATS",
                 font=("Helvetica", 10, "bold"),
                 fg=C['dim'], bg=C['panel']).pack(anchor='w', pady=(0, 5))

        self.sv = {}
        for k in ["Status", "Nodes", "Steps", "Time"]:
            r = tk.Frame(pnl, bg=C['panel'])
            r.pack(fill=tk.X, pady=2)
            tk.Label(r, text=f"{k}:", font=("Helvetica", 9),
                     fg=C['gold'], bg=C['panel'],
                     width=7, anchor='w').pack(side=tk.LEFT)
            v = tk.StringVar(value="-")
            tk.Label(r, textvariable=v, font=("Consolas", 10),
                     fg=C['text'], bg=C['panel']).pack(side=tk.LEFT)
            self.sv[k] = v

        # ── Comparison table ──────────────────────────────────────────────
        table_container = tk.Frame(wrap, bg=C['bg'])
        table_container.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        tk.Label(table_container, text="ALGORITHM RUN HISTORY",
                 font=("Helvetica", 10, "bold"),
                 fg=C['dim'], bg=C['bg']).pack(anchor='w', pady=(0, 5))

        # Setup custom modern style for the treeview
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                        background=C['panel'], foreground=C['text'],
                        fieldbackground=C['panel'], rowheight=28, borderwidth=0,
                        font=("Consolas", 9))
        style.configure("Treeview.Heading",
                        background='#222436', foreground=C['gold'],
                        font=("Helvetica", 9, "bold"), borderwidth=0)
        style.map("Treeview", background=[('selected', '#3d3f54')])

        # Wrap in an inner frame to hold both the treeview and the scrollbar
        tv_inner = tk.Frame(table_container, bg=C['panel'])
        tv_inner.pack(fill=tk.BOTH, expand=True)

        cols = ("Algorithm", "Nodes", "Steps", "Time (s)", "Result")
        
        scroll_y = ttk.Scrollbar(tv_inner, orient=tk.VERTICAL)
        self.tree = ttk.Treeview(tv_inner, columns=cols, show='headings', height=5, yscrollcommand=scroll_y.set)
        scroll_y.config(command=self.tree.yview)

        for c, w in zip(cols, [110, 100, 80, 90, 90]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor='center', minwidth=w)
        
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Button(wrap,
                  text="▶▶ Run All Algorithms & Compare",
                  command=self._compare_all,
                  font=("Helvetica", 10, "bold"),
                  fg='#1e1e2e', bg=C['gold'], 
                  activebackground='#ffca8a', activeforeground='#1e1e2e',
                  relief=tk.FLAT, padx=10, pady=8, cursor='hand2').pack(pady=12)

    # ── DRAW ──────────────────────────────────────────────────────────────────
    def _draw_board(self):
        self.canvas.delete("all")
        solved = (self.state == GOAL)
        for i, val in enumerate(self.state):
            r, c = divmod(i, 4)
            x0 = c * TILE + 4;  y0 = r * TILE + 4
            x1 = x0 + TILE - 4; y1 = y0 + TILE - 4
            
            color = (C['blank'] if val == 0 else
                     '#00c49e'  if solved   else
                     C['tile'])
            
            # Subtle realistic drop shadow for tiles
            if val != 0:
                self.canvas.create_rectangle(x0+2, y0+2, x1+2, y1+2,
                                             fill=C['shadow'], outline='')

            self.canvas.create_rectangle(x0, y0, x1, y1,
                                         fill=color, outline='#45476a', width=1)
            if val:
                self.canvas.create_text((x0+x1)//2, (y0+y1)//2,
                                        text=str(val),
                                        font=("Helvetica", 24, "bold"),
                                        fill='#1e1e2e' if solved else C['text'])

    # ── EVENTS ────────────────────────────────────────────────────────────────
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

                # ✅ Updates UI & appends single runs to the history log
                def update():
                    if path:
                        steps = len(path) - 1
                        self.sol_path  = path
                        self.sv["Status"].set("✔ Found!")
                        self.sv["Nodes"].set(str(nodes))
                        self.sv["Steps"].set(str(steps))
                        self.sv["Time"].set(f"{t:.3f}s")
                        
                        # Add record to table
                        self.tree.insert("", tk.END, values=(algo, nodes, steps, f"{t:.3f}", "✔ Found"))
                        
                        self.anim_step = 0
                        self._animate()
                    else:
                        self.sv["Status"].set("✘ Limit Reached")
                        self.sv["Nodes"].set(str(nodes))
                        self.sv["Steps"].set("-")
                        
                        # Add record to table
                        self.tree.insert("", tk.END, values=(algo, nodes, "N/A", f"{t:.3f}", "✘ Limit"))
                    
                    self.tree.yview_moveto(1) # Scroll to bottom
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

            # ✅ Inserts rows consecutively WITHOUT deleting previous histories
            def insert_rows():
                for vals in results:
                    self.tree.insert("", tk.END, values=vals)
                self.sv["Status"].set("✔ Done")
                self.tree.yview_moveto(1) # Auto-scroll to the newest entries at the bottom

            self.root.after(0, insert_rows)

        threading.Thread(target=run, daemon=True).start()

    def _back(self):
        self._stop()
        self.root.destroy()
        import importlib, gui.menu as m
        importlib.reload(m)
        m.start_menu()