# gui/tictactoe_gui.py
import tkinter as tk
 
from models.tictactoe   import check_winner, get_winning_line, is_full
from algorithms.minimax import best_move
 
 
C = {
    'bg':    '#0d0d1a',
    'panel': '#1a1a2e',
    'cell':  '#16213e',
    'x_col': '#e94560',
    'o_col': '#4ecca3',
    'line':  '#f5a623',
    'text':  '#eaeaea',
    'dim':   '#888888',
}
CELL = 130
 
 
class TicTacToeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic Tac Toe — Minimax AI")
        self.root.configure(bg=C['bg'])
        self.root.resizable(True, True)      # ✅ FIX 2: resizable
 
        self.board     = [''] * 9
        self.game_over = False
        self.scores    = {'X': 0, 'O': 0, 'Draw': 0}
 
        self._build_ui()
 
    # ── BUILD UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        wrap = tk.Frame(self.root, bg=C['bg'])
        wrap.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
 
        # ── Title row with BACK BUTTON ────────────────────────────────────
        top = tk.Frame(wrap, bg=C['bg'])
        top.pack(fill=tk.X, pady=(0, 8))
 
        # ✅ FIX 1: Clearly visible Back to Menu button
        tk.Button(
            top, text="⬅  Back to Menu",
            command=self._back,
            font=("Courier", 10, "bold"),
            fg='white', bg='#333355',
            relief=tk.FLAT, padx=10, pady=5,
            cursor='hand2'
        ).pack(side=tk.LEFT)
 
        tk.Label(top, text="   TIC  TAC  TOE",
                 font=("Courier", 20, "bold"),
                 fg=C['x_col'], bg=C['bg']).pack(side=tk.LEFT)
 
        tk.Label(wrap,
                 text="You = X    ·    AI = O  (Minimax + Alpha-Beta)",
                 font=("Courier", 9), fg=C['dim'], bg=C['bg']).pack(pady=(0, 10))
 
        # Score bar
        bar = tk.Frame(wrap, bg=C['panel'], pady=8)
        bar.pack(fill=tk.X)
        self.score_vars = {}
        for label, key, color in [
            ("You (X)", 'X',    C['x_col']),
            ("Draw",    'Draw', C['line']),
            ("AI (O)",  'O',    C['o_col']),
        ]:
            col = tk.Frame(bar, bg=C['panel'])
            col.pack(side=tk.LEFT, expand=True)
            tk.Label(col, text=label, font=("Courier", 9),
                     fg=C['text'], bg=C['panel']).pack()
            v = tk.StringVar(value="0")
            tk.Label(col, textvariable=v, font=("Courier", 20, "bold"),
                     fg=color, bg=C['panel']).pack()
            self.score_vars[key] = v
 
        # Canvas
        sz = 3 * CELL + 4
        self.canvas = tk.Canvas(wrap, width=sz, height=sz,
                                bg=C['bg'], highlightthickness=0)
        self.canvas.pack(pady=14)
        self.canvas.bind("<Button-1>", self._on_click)
 
        # Status
        self.status_var = tk.StringVar(value="Your turn!  Click a cell.")
        tk.Label(wrap, textvariable=self.status_var,
                 font=("Courier", 11, "bold"),
                 fg=C['line'], bg=C['bg']).pack(pady=4)
 
        # Buttons
        btn_row = tk.Frame(wrap, bg=C['bg'])
        btn_row.pack(pady=(4, 4))
        for txt, cmd, color in [
            ("🔄  New Game",  self._new_game, C['x_col']),
            ("🤖  AI First",  self._ai_first, C['o_col']),
        ]:
            tk.Button(btn_row, text=txt, command=cmd,
                      font=("Courier", 10, "bold"),
                      fg='white', bg=color, relief=tk.FLAT,
                      padx=10, pady=6, cursor='hand2').pack(side=tk.LEFT, padx=6)
 
        self._draw_board()
 
    # ── DRAW ──────────────────────────────────────────────────────────────────
    def _draw_board(self, winning_line=None):
        self.canvas.delete("all")
        sz = 3 * CELL + 4
 
        for i in range(1, 3):
            pos = i * CELL + 2
            self.canvas.create_line(pos, 4, pos, sz-4, fill='#2a2a4a', width=3)
            self.canvas.create_line(4, pos, sz-4, pos, fill='#2a2a4a', width=3)
 
        for i, cell in enumerate(self.board):
            r, c = divmod(i, 3)
            x0 = c*CELL+6;  y0 = r*CELL+6
            x1 = x0+CELL-8; y1 = y0+CELL-8
            fill = '#1f2e50' if winning_line and i in winning_line else C['cell']
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline='')
            if cell == 'X':
                pad = 22
                self.canvas.create_line(x0+pad, y0+pad, x1-pad, y1-pad,
                                        fill=C['x_col'], width=7, capstyle=tk.ROUND)
                self.canvas.create_line(x1-pad, y0+pad, x0+pad, y1-pad,
                                        fill=C['x_col'], width=7, capstyle=tk.ROUND)
            elif cell == 'O':
                pad = 18
                cx, cy = (x0+x1)//2, (y0+y1)//2
                rd = (x1-x0)//2 - pad
                self.canvas.create_oval(cx-rd, cy-rd, cx+rd, cy+rd,
                                        outline=C['o_col'], width=7)
 
        if winning_line:
            coords = []
            for idx in winning_line:
                rr, cc = divmod(idx, 3)
                coords += [cc*CELL + CELL//2 + 2, rr*CELL + CELL//2 + 2]
            self.canvas.create_line(*coords, fill=C['line'], width=6,
                                    capstyle=tk.ROUND)
 
    # ── EVENTS ────────────────────────────────────────────────────────────────
    def _on_click(self, event):
        if self.game_over: return
        col = event.x // CELL
        row = event.y // CELL
        if not (0 <= col < 3 and 0 <= row < 3): return
        idx = row*3 + col
        if self.board[idx] != '': return
        self.board[idx] = 'X'
        self._draw_board()
        if not self._check_end():
            self.status_var.set("AI is thinking…")
            self.root.after(200, self._ai_move)
 
    def _ai_move(self):
        move = best_move(self.board)
        if move != -1:
            self.board[move] = 'O'
            self._draw_board()
            self._check_end()
 
    def _ai_first(self):
        self._new_game()
        self.root.after(300, self._ai_move)
 
    def _check_end(self):
        winner = check_winner(self.board)
        wline  = get_winning_line(self.board)
        if winner:
            self._draw_board(winning_line=wline)
            self.game_over = True
            if winner == 'X':
                self.status_var.set("🎉  You Win!")
                self.scores['X'] += 1
            else:
                self.status_var.set("🤖  AI Wins!")
                self.scores['O'] += 1
            self._refresh_scores()
            return True
        elif is_full(self.board):
            self.game_over = True
            self.status_var.set("🤝  It's a Draw!")
            self.scores['Draw'] += 1
            self._refresh_scores()
            return True
        else:
            self.status_var.set("Your turn!  Click a cell.")
            return False
 
    def _refresh_scores(self):
        for key, var in self.score_vars.items():
            var.set(str(self.scores[key]))
 
    def _new_game(self):
        self.board     = [''] * 9
        self.game_over = False
        self.status_var.set("Your turn!  Click a cell.")
        self._draw_board()
 
    def _back(self):
        self.root.destroy()
        import importlib, gui.menu as m
        importlib.reload(m)
        m.start_menu()
 