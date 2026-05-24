import tkinter as tk
from tkinter import font as tkfont
from tkinter import scrolledtext
import tkinter.ttk as ttk

from game_master import MasterClass
from players import HumanPlayer
from sound_manager import SoundManager


class GUIObserver:
    def __init__(self, text_widget, status_var=None, sound=None):
        self.text_widget = text_widget
        self.status_var = status_var
        self.sound = sound

    def update(self, event_type, **kwargs):
        if event_type == 'shot':
            player = kwargs.get('player')
            x = kwargs.get('x')
            y = kwargs.get('y')
            hit = kwargs.get('hit')
            ship_type = kwargs.get('ship_type')
            message = f"Player {player} {'HIT' if hit else 'MISSED'} at ({x},{y})"
            if ship_type:
                message += f" -> {ship_type}"
            if self.sound:
                if ship_type and 'SUNK' in str(ship_type):
                    self.sound.play('sunk')
                elif hit:
                    self.sound.play('hit')
                else:
                    self.sound.play('miss')
                self.sound.play('shot')
        elif event_type == 'win':
            message = f"Player {kwargs.get('winner')} WON the game!"
        elif event_type == 'error':
            message = f"ERROR: {kwargs.get('message')}"
        else:
            message = f"{event_type}: {kwargs}"

        def insert_message():
            self.text_widget.insert(tk.END, message + '\n')
            self.text_widget.see(tk.END)
            if self.status_var is not None:
                self.status_var.set(message)

        try:
            self.text_widget.after(0, insert_message)
        except Exception:
            pass


class PlacementController:
    def __init__(self, game, fleet_specs, player_order=None):
        self.game = game
        self.fleet_specs = fleet_specs
        self.player_order = player_order if player_order is not None else ['A', 'B']
        self.player_index = 0
        self.ship_index_by_player = {p: 0 for p in self.player_order}
        self.horizontal = True
        self._clear_boards()

    def _clear_boards(self):
        size = self.game.map.size
        self.game.winner = None
        # Only clear boards for players who need manual placement (are in player_order)
        for player in self.player_order:
            if player == 'A':
                self.game.map.shipsA.clear()
                self.game.map.mapA = [['.' for _ in range(size)] for _ in range(size)]
            else:
                self.game.map.shipsB.clear()
                self.game.map.mapB = [['.' for _ in range(size)] for _ in range(size)]

    @property
    def current_player(self):
        return self.player_order[self.player_index]

    @property
    def current_ship_spec(self):
        index = self.ship_index_by_player[self.current_player]
        return self.fleet_specs[index]

    def current_ship_number(self):
        return self.ship_index_by_player[self.current_player] + 1

    def total_ships(self):
        return len(self.fleet_specs)

    def rotate(self):
        self.horizontal = not self.horizontal

    def reset(self):
        self.player_index = 0
        self.ship_index_by_player = {p: 0 for p in self.player_order}
        self.horizontal = True
        self._clear_boards()

    def place_at(self, x, y):
        ship_type = self.current_ship_spec['ship_type']
        player = self.current_player
        success = self.game.place_ship_for_player(player, ship_type, x, y, self.horizontal)
        if not success:
            return False, 'invalid'

        self.ship_index_by_player[player] += 1
        if self.ship_index_by_player[player] >= len(self.fleet_specs):
            if self.player_index < len(self.player_order) - 1:
                self.player_index += 1
                return True, 'next_player'
            return True, 'done'

        return True, 'placed'

    def placement_complete(self):
        return all(self.ship_index_by_player.get(p, 0) >= len(self.fleet_specs) for p in self.player_order)


class SeaBattleGUI(tk.Tk):
    CELL_SIZE = 360

    def __init__(self):
        super().__init__()
        self.title('Sea Battle — GUI v2')
        self.configure(bg='#f0f4f8')

        self.app_font = tkfont.Font(family='Segoe UI', size=10)
        self.title_font = tkfont.Font(family='Segoe UI', size=12, weight='bold')

        self.master_game = None
        self.placement = None
        self.phase = 'placement'
        self.attacker = 'A'
        self.auto_run = False
        self.after_id = None
        self.timer_id = None
        self.timer_seconds = 15
        self.timer_var = tk.StringVar(value='')

        self.status_var = tk.StringVar(value='Ready')
        self.sound = SoundManager()

        self._build_toolbar()
        self._build_views()
        self._build_log()
        self._build_status_bar()

        self.gui_observer = GUIObserver(self.log, self.status_var, self.sound)
        self.start_new_game()

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bg='#f0f4f8')
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)

        ttk.Label(toolbar, text='Player A:', font=self.app_font).pack(side=tk.LEFT, padx=(0, 2))
        self.varA = tk.StringVar(value='human')
        ttk.OptionMenu(toolbar, self.varA, 'human', 'human', 'ai', 'cheater').pack(side=tk.LEFT)

        ttk.Label(toolbar, text='Player B:', font=self.app_font).pack(side=tk.LEFT, padx=(8, 2))
        self.varB = tk.StringVar(value='human')
        ttk.OptionMenu(toolbar, self.varB, 'human', 'human', 'ai', 'cheater').pack(side=tk.LEFT)

        ttk.Button(toolbar, text='New Game', command=self.start_new_game).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text='Rotate', command=self.rotate_orientation).pack(side=tk.LEFT)
        ttk.Button(toolbar, text='Auto Place', command=self.auto_place_current).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text='Step', command=self.step).pack(side=tk.LEFT, padx=6)

        self.auto_btn = ttk.Button(toolbar, text='Auto Run', command=self.toggle_auto)
        self.auto_btn.pack(side=tk.LEFT)

        ttk.Button(toolbar, text='Clear Log', command=self.clear_log).pack(side=tk.RIGHT)
        ttk.Button(toolbar, text='Quit', command=self.quit).pack(side=tk.RIGHT, padx=6)
        self.music_btn = ttk.Button(toolbar, text='🎵 ON', command=self.toggle_music)
        self.music_btn.pack(side=tk.RIGHT, padx=2)
        self.sfx_btn = ttk.Button(toolbar, text='🔊 ON', command=self.toggle_sfx)
        self.sfx_btn.pack(side=tk.RIGHT, padx=2)

    def _build_views(self):
        self.root_frame = tk.Frame(self, bg='#f0f4f8')
        self.root_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False)

        self.placement_frame = tk.Frame(self.root_frame, bg='#f0f4f8')
        self.placement_title = ttk.Label(self.placement_frame, text='Placement', font=self.title_font)
        self.placement_title.pack(pady=(0, 6))
        self.placement_info = ttk.Label(self.placement_frame, text='', font=self.app_font)
        self.placement_info.pack(pady=(0, 6))
        self.placement_canvas = tk.Canvas(self.placement_frame, width=self.CELL_SIZE, height=self.CELL_SIZE, bg='white', bd=2, relief='sunken')
        self.placement_canvas.pack(padx=8, pady=8)
        self.placement_canvas.bind('<Button-1>', self.on_placement_click)

        # кнопки підтвердження авторозстановки (приховані поки не натиснуто Auto Place)
        self.auto_confirm_frame = tk.Frame(self.placement_frame, bg='#f0f4f8')
        ttk.Button(self.auto_confirm_frame, text='✓ Прийняти', command=self.confirm_auto_place).pack(side=tk.LEFT, padx=8)
        ttk.Button(self.auto_confirm_frame, text='🔀 Ще раз', command=self.reroll_auto_place).pack(side=tk.LEFT, padx=8)

        self.battle_frame = tk.Frame(self.root_frame, bg='#f0f4f8')
        battle_top = tk.Frame(self.battle_frame, bg='#f0f4f8')
        battle_top.pack(side=tk.TOP)

        left_frame = tk.Frame(battle_top, bg='#f0f4f8')
        left_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(left_frame, text='Player A Board', font=self.title_font).pack()
        self.canvasA = tk.Canvas(left_frame, width=self.CELL_SIZE, height=self.CELL_SIZE, bg='white', bd=2, relief='sunken')
        self.canvasA.pack(padx=4, pady=6)

        right_frame = tk.Frame(battle_top, bg='#f0f4f8')
        right_frame.pack(side=tk.LEFT, padx=10)
        ttk.Label(right_frame, text='Player B Board', font=self.title_font).pack()
        self.canvasB = tk.Canvas(right_frame, width=self.CELL_SIZE, height=self.CELL_SIZE, bg='white', bd=2, relief='sunken')
        self.canvasB.pack(padx=4, pady=6)

        self.canvasA.bind('<Button-1>', self.on_battle_click)
        self.canvasB.bind('<Button-1>', self.on_battle_click)

    def _build_log(self):
        self.log = scrolledtext.ScrolledText(self, height=10, font=self.app_font)
        self.log.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)

    def _build_status_bar(self):
        bar = tk.Frame(self, bg='#e9eef3')
        bar.pack(fill=tk.X)
        status = tk.Label(bar, textvariable=self.status_var, anchor='w', bg='#e9eef3')
        status.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.timer_label = tk.Label(bar, textvariable=self.timer_var,
                                    bg='#e9eef3', fg='#c0392b',
                                    font=tkfont.Font(family='Segoe UI', size=11, weight='bold'),
                                    width=10, anchor='e')
        self.timer_label.pack(side=tk.RIGHT, padx=8)

    def fleet_specs(self):
        return [
            {'ship_type': 'carrier', 'title': 'Carrier', 'length': 4},
            {'ship_type': 'submarine', 'title': 'Submarine', 'length': 3},
            {'ship_type': 'submarine', 'title': 'Submarine', 'length': 3},
            {'ship_type': 'destroyer', 'title': 'Destroyer', 'length': 2},
            {'ship_type': 'destroyer', 'title': 'Destroyer', 'length': 2},
            {'ship_type': 'destroyer', 'title': 'Destroyer', 'length': 2},
            {'ship_type': 'patrol', 'title': 'Patrol Boat', 'length': 1},
            {'ship_type': 'patrol', 'title': 'Patrol Boat', 'length': 1},
            {'ship_type': 'patrol', 'title': 'Patrol Boat', 'length': 1},
            {'ship_type': 'patrol', 'title': 'Patrol Boat', 'length': 1},
        ]

    def toggle_music(self):
        on = self.sound.toggle_music()
        self.music_btn.config(text='🎵 ON' if on else '🎵 OFF')

    def toggle_sfx(self):
        on = self.sound.toggle_sfx()
        self.sfx_btn.config(text='🔊 ON' if on else '🔊 OFF')

    def clear_log(self):
        self.log.delete('1.0', tk.END)

    def start_new_game(self):
        self.stop_auto()
        self.stop_turn_timer()
        self.master_game = MasterClass()
        self.master_game.attach(self.gui_observer)
        self.master_game.set_players(
            self.varA.get(),
            self.varB.get()
        )
        self.attacker = 'A'
        human_players = [p for p in ('A', 'B') if isinstance(self.master_game.players[p], HumanPlayer)]
        print(f"DEBUG: varA={self.varA.get()}, varB={self.varB.get()}, human_players={human_players}")

        if human_players:
            self.placement = PlacementController(
                self.master_game,
                self.fleet_specs(),
                player_order=human_players
            )
            for p in ('A', 'B'):
                if p not in human_players:
                    self.master_game.auto_place_ships(p)
            self.phase = 'placement'
            self.show_placement_view()
        else:
            self.placement = None
            self.master_game.auto_place_ships('A')
            self.master_game.auto_place_ships('B')
            self.phase = 'battle'
            self.show_battle_view()
            self.start_turn_timer()
        self.refresh_views()
        self.log.insert(tk.END, 'New game started.\n')
        self.log.see(tk.END)

    def show_placement_view(self):
        self.battle_frame.pack_forget()
        self.placement_frame.pack(side=tk.TOP, pady=(4, 0))

    def show_battle_view(self):
        self.placement_frame.pack_forget()
        self.battle_frame.pack(side=tk.TOP, pady=(4, 0))

    def auto_place_current(self):
        if self.phase != 'placement' or not self.placement:
            return
        self._do_auto_place_preview()

    def _do_auto_place_preview(self):
        player = self.placement.current_player
        size = self.master_game.map.size

        if player == 'A':
            self.master_game.map.shipsA.clear()
            self.master_game.map.mapA = [['.' for _ in range(size)] for _ in range(size)]
        else:
            self.master_game.map.shipsB.clear()
            self.master_game.map.mapB = [['.' for _ in range(size)] for _ in range(size)]

        self.placement.ship_index_by_player[player] = 0
        self.master_game.auto_place_ships(player)

        self.placement_canvas.unbind('<Button-1>')
        self.auto_confirm_frame.pack(pady=(0, 8))
        self.placement_info.config(text=f'Player {player}: перегляньте розстановку — прийняти чи перегенерувати?')
        board = self.master_game.map.mapA if player == 'A' else self.master_game.map.mapB
        self.placement_canvas.delete('all')
        self._draw_board(self.placement_canvas, board, show_ships=True)

    def confirm_auto_place(self):
        if not self.placement:
            return
        player = self.placement.current_player
        self.placement.ship_index_by_player[player] = len(self.placement.fleet_specs)
        self.auto_confirm_frame.pack_forget()
        self.placement_canvas.bind('<Button-1>', self.on_placement_click)
        self.log.insert(tk.END, f'Player {player}: авторозстановку прийнято.\n')
        self.log.see(tk.END)

        self.placement.player_index += 1
        if self.placement.player_index >= len(self.placement.player_order):
            self.phase = 'battle'
            self.show_battle_view()
            self.log.insert(tk.END, 'Placement complete. Battle starts now.\n')
            self.log.see(tk.END)
            self.refresh_views()
            self.start_turn_timer()
        else:
            self.refresh_views()

    def reroll_auto_place(self):
        if not self.placement:
            return
        self._do_auto_place_preview()

    def rotate_orientation(self):
        if self.phase != 'placement' or not self.placement:
            return
        self.placement.rotate()
        self.refresh_views()

    def refresh_views(self):
        if self.phase == 'placement':
            self.draw_placement_board()
        else:
            self.draw_battle_boards()

    def draw_placement_board(self):
        if not self.placement:
            return
        self.placement_canvas.delete('all')
        player = self.placement.current_player
        board = self.master_game.map.mapA if player == 'A' else self.master_game.map.mapB
        current = self.placement.current_ship_spec
        orientation = 'Horizontal' if self.placement.horizontal else 'Vertical'
        self.placement_title.config(text=f'Placement for Player {player}')
        self.placement_info.config(
            text=f"Ship {self.placement.current_ship_number()}/{self.placement.total_ships()}: {current['title']} ({current['length']}) | {orientation} | Click to place"
        )
        self._draw_board(self.placement_canvas, board, show_ships=True)

    def draw_battle_boards(self):
        self.canvasA.delete('all')
        self.canvasB.delete('all')
        self._draw_board(self.canvasA, self.master_game.map.mapA, show_ships=False)
        self._draw_board(self.canvasB, self.master_game.map.mapB, show_ships=False)
        self.status_var.set(f"Phase: battle | Attacker: {self.attacker}")

    def _draw_board(self, canvas, board, show_ships):
        size = self.master_game.map.size
        cell = self.CELL_SIZE // size
        for y in range(size):
            for x in range(size):
                value = board[y][x]
                color = '#cfe7ff' if (x + y) % 2 == 0 else '#eaf4ff'
                if value == 'S' and show_ships:
                    color = '#bdbdbd'
                elif value == 'X':
                    color = '#ff8a80'
                elif value == 'o':
                    color = '#90caf9'

                x1 = x * cell
                y1 = y * cell
                x2 = x1 + cell
                y2 = y1 + cell
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='#78909c')

                if value == 'X':
                    canvas.create_line(x1 + 4, y1 + 4, x2 - 4, y2 - 4, fill='darkred', width=2)
                    canvas.create_line(x1 + 4, y2 - 4, x2 - 4, y1 + 4, fill='darkred', width=2)
                elif value == 'o':
                    canvas.create_oval(x1 + 6, y1 + 6, x2 - 6, y2 - 6, outline='navy', width=2)

    def on_placement_click(self, event):
        if self.phase != 'placement' or not self.placement:
            return
        size = self.master_game.map.size
        cell = self.CELL_SIZE // size
        x = event.x // cell
        y = event.y // cell
        placed_player = self.placement.current_player

        success, state = self.placement.place_at(x, y)
        if not success:
            self.log.insert(tk.END, 'Cannot place ship here. Try another cell.\n')
            self.log.see(tk.END)
            return

        self.log.insert(tk.END, f"Player {placed_player} placed ship at ({x},{y}).\n")
        self.log.see(tk.END)

        if state == 'next_player':
            self.log.insert(tk.END, 'Player A finished. Now place ships for Player B.\n')
            self.log.see(tk.END)
        elif state == 'done':
            self.phase = 'battle'
            self.show_battle_view()
            self.log.insert(tk.END, 'Placement complete. Battle starts now.\n')
            self.log.see(tk.END)
            self.refresh_views()
            self.start_turn_timer()
            return

        self.refresh_views()

    def on_battle_click(self, event):
        if self.phase != 'battle' or not self.master_game or self.master_game.winner:
            return

        canvas = event.widget
        expected_canvas = self.canvasB if self.attacker == 'A' else self.canvasA
        if canvas != expected_canvas:
            return

        size = self.master_game.map.size
        cell = self.CELL_SIZE // size
        x = event.x // cell
        y = event.y // cell
        defender = 'B' if self.attacker == 'A' else 'A'

        if not (0 <= x < size and 0 <= y < size):
            return

        try:
            hit, ship_type = self.master_game.map.process_shot(defender, x, y)
        except ValueError as e:
            self.log.insert(tk.END, f'ERROR: {e}\n')
            self.log.see(tk.END)
            return

        self.master_game.notify('shot', player=self.attacker, x=x, y=y, hit=hit, ship_type=ship_type)

        if self.master_game.map.check_loss(defender):
            self.master_game.winner = self.attacker
            self.master_game.notify('win', winner=self.attacker)

        self.refresh_views()
        if self.master_game.winner:
            self.stop_turn_timer()
            self.log.insert(tk.END, f'Winner: {self.master_game.winner}\n')
            self.log.see(tk.END)
            human_marks = [p for p, obj in self.master_game.players.items() if isinstance(obj, HumanPlayer)]
            self.sound.play('victory' if self.master_game.winner in human_marks else 'defeat')
            return

        self.attacker = 'B' if self.attacker == 'A' else 'A'
        self.status_var.set(f'Phase: battle | Attacker: {self.attacker}')
        self.start_turn_timer()

    def step(self):
        if self.phase != 'battle' or not self.master_game or self.master_game.winner:
            return

        player_obj = self.master_game.players.get(self.attacker)
        if isinstance(player_obj, HumanPlayer):
            self.log.insert(tk.END, f'Player {self.attacker} is human. Click the opponent board.\n')
            self.log.see(tk.END)
            return

        self.master_game.process_turn(self.attacker)
        self.refresh_views()

        if self.master_game.winner:
            self.stop_turn_timer()
            self.log.insert(tk.END, f'Winner: {self.master_game.winner}\n')
            self.log.see(tk.END)
            human_marks = [p for p, obj in self.master_game.players.items() if isinstance(obj, HumanPlayer)]
            self.sound.play('victory' if self.master_game.winner in human_marks else 'defeat')
            return

        self.attacker = 'B' if self.attacker == 'A' else 'A'
        self.status_var.set(f'Phase: battle | Attacker: {self.attacker}')
        self.start_turn_timer()

    def auto_step(self):
        if not self.auto_run:
            return
        self.step()
        if self.phase == 'battle' and not self.master_game.winner:
            self.after_id = self.after(200, self.auto_step)
        else:
            self.auto_run = False
            self.auto_btn.config(text='Auto Run')

    def toggle_auto(self):
        if self.phase != 'battle' or not self.master_game:
            return
        self.auto_run = not self.auto_run
        if self.auto_run:
            self.auto_btn.config(text='Stop')
            self.auto_step()
        else:
            self.auto_btn.config(text='Auto Run')
            if self.after_id:
                self.after_cancel(self.after_id)
                self.after_id = None

    def stop_auto(self):
        self.auto_run = False
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        try:
            self.auto_btn.config(text='Auto Run')
        except Exception:
            pass


    def _auto_fire_and_continue(self):
        if self.phase != 'battle' or not self.master_game or self.master_game.winner:
            return
        self.master_game.process_turn(self.attacker)
        self.refresh_views()
        if self.master_game.winner:
            self.stop_turn_timer()
            self.log.insert(tk.END, f'Winner: {self.master_game.winner}\n')
            self.log.see(tk.END)
            return
        self.attacker = 'B' if self.attacker == 'A' else 'A'
        self.status_var.set(f'Phase: battle | Attacker: {self.attacker}')
        self.timer_var.set('')
        self.after(100, self.start_turn_timer)

    def start_turn_timer(self):
        self.stop_turn_timer()
        self._remaining = self.timer_seconds
        self._tick_timer()

    def _tick_timer(self):
        if self.phase != 'battle' or not self.master_game or self.master_game.winner:
            self.timer_var.set('')
            return
        player_obj = self.master_game.players.get(self.attacker)
        if not isinstance(player_obj, HumanPlayer):
            self.timer_var.set('')
            return

        self.timer_var.set(f'⏱ {self._remaining}s')
        self.timer_label.config(fg='#c0392b' if self._remaining <= 10 else '#2c3e50')

        if self._remaining <= 0:
            self.timer_var.set('⏱ Час вийшов!')
            self.log.insert(tk.END, f'Player {self.attacker}: час вийшов — хід пропущено!\n')
            self.log.see(tk.END)
            self.attacker = 'B' if self.attacker == 'A' else 'A'
            self.status_var.set(f'Phase: battle | Attacker: {self.attacker}')
            self.refresh_views()
            next_player = self.master_game.players.get(self.attacker)
            if not isinstance(next_player, HumanPlayer):
                self.after(100, self._auto_fire_and_continue)
            else:
                self.after(300, self.start_turn_timer)
            return

        self._remaining -= 1
        self.timer_id = self.after(1000, self._tick_timer)

    def stop_turn_timer(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.timer_var.set('')


if __name__ == '__main__':
    app = SeaBattleGUI()
    app.mainloop()