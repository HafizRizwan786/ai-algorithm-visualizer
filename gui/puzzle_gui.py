import tkinter as tk
from tkinter import ttk
import threading
import math
import time

from models.puzzle import GOAL, get_blank, generate_puzzle
from algorithms.bfs import bfs
from algorithms.dfs import dfs
from algorithms.astar import astar

C = {
    'bg':      '#020b0f',
    'surface': '#061520',
    'card':    '#071a26',
    'card_h':  '#0c2438',
    'border':  '#0e2a3f',
    'cyan':    '#00d4ff',
    'amber':   '#f0a500',
    'text':    '#c0e8f8',
    'muted':   '#1a4a60',
    'red':     '#ff5d73',
    'green':   '#00f2c3',
    'shadow':  '#010608',
    'tile':    '#071e30',
    'blank':   '#020d14',
}

TILE = 72
FONT = 'Courier New'
ALGO_COLOR = {'BFS':'#3b82f6','DFS':'#8b5cf6','A* h1':'#f0a500','A* h2':'#00f2c3'}


class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("15-Puzzle Solver — CIPHER AI")
        self.root.configure(bg=C['bg'])
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight() - 40
        self.root.geometry(f"{w}x{h}+0+0")
        self.root.resizable(False, False)

        self.algo_var  = tk.StringVar(value='A* h2')
        self.state     = generate_puzzle()
        self.sol_path  = []; self.anim_step=0; self.anim_id=None; self.solving=False

        self._build()
        self._draw_board()
        self._tick_clock()
        self._tick_pulse()

    def _tick_clock(self):
        try: self._clk.config(text=time.strftime('%H:%M:%S')); self.root.after(1000,self._tick_clock)
        except tk.TclError: pass

    def _tick_pulse(self,t=0):
        try:
            v=(math.sin(t*0.12)+1)/2; r=3+v*3.5; cx,cy=5.5,6.5
            self._pc.coords(self._prg,cx-r,cy-r,cx+r,cy+r)
            self.root.after(50,lambda:self._tick_pulse(t+1))
        except tk.TclError: pass

    def _sec(self,p,label):
        f=tk.Frame(p,bg=C['bg']); f.pack(fill=tk.X,pady=(10,5))
        tk.Label(f,text=label,font=(FONT,9,'bold'),fg=C['cyan'],bg=C['bg']).pack(side=tk.LEFT)
        tk.Frame(f,bg=C['border'],height=1).pack(side=tk.LEFT,fill=tk.X,expand=True,padx=(8,0),pady=5)

    def _build(self):
        W = tk.Frame(self.root, bg=C['bg'], padx=20, pady=10)
        W.pack(fill=tk.BOTH, expand=True)

        top = tk.Frame(W, bg=C['bg']); top.pack(fill=tk.X)
        tk.Button(top,
                text='← MENU',
                command=self._back,
                font=(FONT, 10, 'bold'),
                fg=C['cyan'], bg=C['card'],
                activeforeground=C['bg'], activebackground=C['cyan'],
                relief=tk.FLAT, highlightthickness=2, highlightbackground=C['cyan'],
                padx=15, pady=6, cursor='hand2').pack(side=tk.LEFT)
        tk.Label(top,text='CIPHER',font=(FONT,12,'bold'),fg=C['cyan'],bg=C['bg']).pack(side=tk.LEFT,padx=(15,0))
        self._pc=tk.Canvas(top,width=76,height=13,bg=C['bg'],highlightthickness=0)
        self._pc.pack(side=tk.LEFT,padx=(7,0))
        self._pc.create_oval(2,2,9,10,fill=C['cyan'],outline='')
        self._prg=self._pc.create_oval(0,1,11,12,outline=C['cyan'],width=1)
        self._pc.create_text(15,6,text='ONLINE',font=(FONT,10),fill=C['cyan'],anchor='w')
        tk.Label(top,text='15 - P U Z Z L E   S O L V E R',
                 font=(FONT,18,'bold'),fg=C['text'],bg=C['bg']).pack(side=tk.LEFT,expand=True)
        self._clk=tk.Label(top,text='00:00:00',font=(FONT,9),fg=C['muted'],bg=C['bg'])
        self._clk.pack(side=tk.RIGHT)

        sep=tk.Canvas(W,height=2,bg=C['bg'],highlightthickness=0); sep.pack(fill=tk.X,pady=(5,10))
        sep.bind('<Configure>',lambda e:(sep.delete('all'),
            sep.create_line(0,1,e.width,1,fill=C['cyan'],width=2)))

        mid = tk.Frame(W, bg=C['bg']); mid.pack(fill=tk.X)

        bcol = tk.Frame(mid, bg=C['bg']); bcol.pack(side=tk.LEFT, anchor='n')
        self._sec(bcol, 'PUZZLE BOARD')
        sz = 4*TILE
        f1=tk.Frame(bcol,bg=C['amber'],padx=3,pady=3); f1.pack()
        f2=tk.Frame(f1,bg=C['border'],padx=1,pady=1); f2.pack()
        f3=tk.Frame(f2,bg=C['surface'],padx=10,pady=10); f3.pack()
        deco=tk.Canvas(f3,width=sz+20,height=sz+20,bg=C['surface'],highlightthickness=0); deco.pack()
        s2,p2,lw=16,6,2
        for pts in [[(p2,p2+s2),(p2,p2),(p2+s2,p2)],
                    [(sz+20-p2-s2,p2),(sz+20-p2,p2),(sz+20-p2,p2+s2)],
                    [(p2,sz+20-p2-s2),(p2,sz+20-p2),(p2+s2,sz+20-p2)],
                    [(sz+20-p2-s2,sz+20-p2),(sz+20-p2,sz+20-p2),(sz+20-p2,sz+20-p2-s2)]]:
            deco.create_line(*[v for xy in pts for v in xy],fill=C['cyan'],width=lw,joinstyle='miter')
        self.canvas=tk.Canvas(deco,width=sz,height=sz,bg=C['blank'],highlightthickness=0,cursor='hand2')
        deco.create_window(10,10,anchor='nw',window=self.canvas)
        self.canvas.bind('<Button-1>',self._click)
        self._blbl=tk.Label(bcol,text='CLICK TILE ADJACENT TO BLANK TO MOVE', font=(FONT,8),fg=C['muted'],bg=C['bg'])
        self._blbl.pack(pady=(8,0))

        right_col = tk.Frame(mid, bg=C['bg'])
        right_col.pack(side=tk.LEFT, anchor='n', padx=(25,0), fill=tk.BOTH, expand=True)

        self._sec(right_col, 'SELECT SEARCH ALGORITHM')
        algo_box = tk.Frame(right_col, bg=C['card'], highlightthickness=1, highlightbackground=C['border'], pady=20)
        algo_box.pack(fill=tk.X)
        for algo in ['BFS','DFS','A* h1','A* h2']:
            ac = ALGO_COLOR[algo]
            f = tk.Frame(algo_box, bg=C['card'], padx=15); f.pack(side=tk.LEFT, expand=True)
            tk.Radiobutton(f, text=algo, variable=self.algo_var, value=algo,
                           font=(FONT, 10, 'bold'), fg=ac, bg=C['card'], selectcolor=C['surface'],
                           activebackground=C['card'], activeforeground=ac, cursor='hand2').pack()

        bottom_right = tk.Frame(right_col, bg=C['bg'])
        bottom_right.pack(fill=tk.BOTH, pady=(20, 0))

        ctrl_frame = tk.Frame(bottom_right, bg=C['bg'])
        ctrl_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._sec(ctrl_frame, 'CONTROLS')

        btn_grid = tk.Frame(ctrl_frame, bg=C['card'], highlightthickness=1, highlightbackground=C['border'], pady=15, padx=10)
        btn_grid.pack(fill=tk.BOTH, expand=True)

        btns = [
            ('🔀 NEW PUZZLE',  self._new_puzzle, C['text']),
            ('▶ START SOLVE',  self._solve,      C['green']),
            ('⏹ STOP ENGINE', self._stop_btn,   C['red']),
            ('▶▶ COMPARE ALL', self._compare,    C['amber'])
        ]
        for i, (txt, cmd, clr) in enumerate(btns):
            b = tk.Button(btn_grid, text=txt, command=cmd, font=(FONT, 9, 'bold'), fg=clr, bg=C['bg'],
                          activebackground=C['card_h'], activeforeground=C['text'],
                          relief=tk.FLAT, highlightthickness=1, highlightbackground=clr,
                          padx=10, pady=18, cursor='hand2', width=16)
            b.grid(row=i//2, column=i%2, padx=10, pady=10, sticky='nsew')
            btn_grid.grid_columnconfigure(i%2, weight=1)
            btn_grid.grid_rowconfigure(i//2, weight=1)

        stat_frame = tk.Frame(bottom_right, bg=C['bg'])
        stat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20,0))
        self._sec(stat_frame, 'LAST RUN STATISTICS')

        sbox = tk.Frame(stat_frame, bg=C['card'], highlightthickness=1, highlightbackground=C['border'], padx=20, pady=25)
        sbox.pack(fill=tk.BOTH, expand=True)

        self.sv = {}
        for lbl, key, clr in [('STATUS:', 'Status', C['text']), ('NODES:', 'Nodes', "#337bef"),
                               ('STEPS:', 'Steps', C['green']), ('TIME:', 'Time', C['amber'])]:
            row = tk.Frame(sbox, bg=C['card'], pady=8); row.pack(fill=tk.X)
            tk.Label(row, text=lbl, font=(FONT, 9, 'bold'), fg=C['cyan'], bg=C['card'], width=10, anchor='w').pack(side=tk.LEFT)
            v = tk.StringVar(value='-'); self.sv[key] = v
            tk.Label(row, textvariable=v, font=(FONT, 11, 'bold'), fg=clr, bg=C['card']).pack(side=tk.LEFT)

        tk.Frame(W, bg=C['border'], height=1).pack(fill=tk.X, pady=(20, 10))
        hdr = tk.Frame(W, bg=C['bg']); hdr.pack(fill=tk.X)
        tk.Label(hdr, text='ALGORITHM RUN HISTORY', font=(FONT, 10, 'bold'), fg=C['cyan'], bg=C['bg']).pack(side=tk.LEFT)
        tk.Button(hdr, text='CLEAR LOGS', command=self._clear, font=(FONT, 8), fg=C['cyan'], bg=C['card'],
                  relief=tk.FLAT, highlightthickness=1, highlightbackground=C['border'], padx=10, cursor='hand2').pack(side=tk.RIGHT)

        style = ttk.Style(); style.theme_use('clam')
        style.configure('C.Treeview', background=C['card'], foreground=C['text'], fieldbackground=C['card'], rowheight=30, font=(FONT, 10))
        style.configure('C.Treeview.Heading', background=C['surface'], foreground=C['amber'], font=(FONT, 10, 'bold'))

        cols = ('Algorithm', 'Nodes Explored', 'Steps Taken', 'Execution Time', 'Result Status')
        wrap = tk.Frame(W, bg=C['card'], highlightthickness=1, highlightbackground=C['border'])
        wrap.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.tree = ttk.Treeview(wrap, columns=cols, show='headings', height=5, style='C.Treeview')
        for c in cols:
            self.tree.heading(c, text=c); self.tree.column(c, anchor='center', width=150)
        for algo, color in ALGO_COLOR.items(): self.tree.tag_configure(algo, foreground=color)

        sb = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _draw_board(self):
        self.canvas.delete('all')
        solved = (self.state == GOAL)
        for i, val in enumerate(self.state):
            r, c = divmod(i, 4)
            x0, y0 = c * TILE + 4, r * TILE + 4
            x1, y1 = x0 + TILE - 5, y0 + TILE - 5
            bg = C['blank'] if val == 0 else C['tile']
            if val: self.canvas.create_rectangle(x0+3, y0+3, x1+3, y1+3, fill=C['shadow'], outline='')
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=bg, outline=C['border'], width=1)
            if val:
                dot = C['green'] if solved else C['cyan']
                self.canvas.create_oval(x1-12, y0+5, x1-7, y0+10, fill=dot, outline='')
                txt_clr = C['green'] if solved else C['text']
                self.canvas.create_text((x0+x1)//2, (y0+y1)//2, text=str(val), font=(FONT, 20, 'bold'), fill=txt_clr)
        self._blbl.config(text='SOLVED ✔' if solved else 'CLICK TILE TO MOVE', fg=C['green'] if solved else C['muted'])

    def _click(self, event):
        if self.solving: return
        c, r = event.x // TILE, event.y // TILE
        if not (0 <= c < 4 and 0 <= r < 4): return
        idx, blank = r * 4 + c, get_blank(self.state)
        if abs(blank // 4 - r) + abs(blank % 4 - c) == 1:
            s = list(self.state); s[blank], s[idx] = s[idx], s[blank]
            self.state = tuple(s); self._draw_board()

    def _new_puzzle(self):
        self._stop(); self.state = generate_puzzle(); self._draw_board()
        for v in self.sv.values(): v.set('-')

    def _solve(self):
        if self.solving: return
        self._stop()
        if self.state == GOAL: self.sv['Status'].set('Already Solved'); return
        self.solving = True; algo = self.algo_var.get()
        self.sv['Status'].set('Running…'); self.root.update()
        def run():
            snap = self.state
            if   algo == 'BFS':    path, nodes, t = bfs(snap)
            elif algo == 'DFS':    path, nodes, t = dfs(snap)
            elif algo == 'A* h1':  path, nodes, t = astar(snap, 'h1')
            else:                  path, nodes, t = astar(snap, 'h2')
            def done():
                if path:
                    steps = len(path)-1; self.sol_path = path
                    self.sv['Status'].set('✔ Found!'); self.sv['Nodes'].set(f'{nodes:,}')
                    self.sv['Steps'].set(str(steps)); self.sv['Time'].set(f'{t:.3f}s')
                    self.tree.insert('', 0, values=(algo, f'{nodes:,}', steps, f'{t:.3f}s', 'Success'), tags=(algo,))
                    self.anim_step = 0; self._animate()
                else:
                    self.sv['Status'].set('✘ Failed / Timeout'); self.solving = False
            self.root.after(0, done)
        threading.Thread(target=run, daemon=True).start()

    def _animate(self):
        if self.anim_step < len(self.sol_path):
            self.state = self.sol_path[self.anim_step]; self._draw_board()
            self.anim_step += 1; self.anim_id = self.root.after(150, self._animate)
        else: self.solving = False

    def _stop(self):
        if self.anim_id: self.root.after_cancel(self.anim_id); self.anim_id = None
        self.solving = False

    def _stop_btn(self): self._stop(); self.sv['Status'].set('Stopped')

    def _compare(self):
        if self.solving: return
        self._stop(); self.sv['Status'].set('Comparing…'); self.root.update()
        snap = self.state
        def run():
            results = []
            for name, fn in [('BFS',   lambda: bfs(snap)),
                              ('DFS',   lambda: dfs(snap)),
                              ('A* h1', lambda: astar(snap, 'h1')),
                              ('A* h2', lambda: astar(snap, 'h2'))]:
                p, n, e = fn()
                results.append((name, f'{n:,}', str(len(p)-1) if p else 'N/A', f'{e:.3f}s', 'Done' if p else 'Limit'))
            self.root.after(0, lambda: [self.tree.insert('', 0, values=r, tags=(r[0],)) for r in results])
            self.root.after(0, lambda: self.sv['Status'].set('Done'))
        threading.Thread(target=run, daemon=True).start()

    def _clear(self):
        for item in self.tree.get_children(): self.tree.delete(item)

    def _back(self):
        self._stop(); self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    PuzzleApp(root)
    root.mainloop()