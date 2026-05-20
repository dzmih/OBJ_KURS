from game_map import Map
from game_logger import GameLogger
from ships import ShipFactory
from players import HumanPlayer, AIPlayer, CheaterPlayer
import pickle

# --- Subject for Observer ---
class GameSubject:
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def notify(self, event_type, **kwargs):
        for observer in self._observers:
            observer.update(event_type, **kwargs)

class MasterClass(GameSubject):
    def __init__(self):
        super().__init__()
        self.map = Map(10)
        # Автоматично підписуємо логер
        self.attach(GameLogger())
        self.players = {}
        self.winner = None

    def set_players(self, type_a, type_b):
        p_classes = {'human': HumanPlayer, 'ai': AIPlayer, 'cheater': CheaterPlayer}
        self.players['A'] = p_classes[type_a]('A')
        self.players['B'] = p_classes[type_b]('B')

    def place_ship_for_player(self, player_mark, ship_type, x, y, horizontal):
        # Factory usage
        try:
            ship = ShipFactory.create_ship(ship_type, player_mark)
            return self.map.place_ship(player_mark, ship, x, y, horizontal)
        except Exception as e:
            self.notify("error", message=str(e))
            return False

    def process_turn(self, attacker_mark):
        defender_mark = 'B' if attacker_mark == 'A' else 'A'
        player_obj = self.players[attacker_mark]
        
        # Отримуємо masked карту ворога для прийняття рішення
        enemy_view = self.map.get_masked_map(defender_mark)
        
        # Strategy usage (поліморфний виклик)
        x, y = player_obj.make_move(self.map.size, enemy_view)

        if x == 'save':
            return 'save'

        # Делегуємо логіку пострілу на Map.process_shot
        try:
            hit_success, sunk_ship_type = self.map.process_shot(defender_mark, x, y)
        except ValueError as e:
            self.notify("error", message=str(e))
            return

        # Сповіщення спостерігачів (Logger)
        self.notify("shot", player=attacker_mark, x=x, y=y, hit=hit_success, ship_type=sunk_ship_type)

        # Перевірка перемоги
        if self.map.check_loss(defender_mark):
            self.winner = attacker_mark
            self.notify("win", winner=attacker_mark)

    def save_game(self, filename):
        # Видаляємо обсервери перед серіалізацією (logger не піклиться)
        obs = self._observers
        self._observers = []
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
        self._observers = obs # відновлюємо
        # Перепідключаємо новий логер після завантаження, бо старий файл закритий

    @staticmethod
    def load_game(filename):
        with open(filename, 'rb') as f:
            game = pickle.load(f)
            # Re-attach logger
            game.attach(GameLogger()) 
            return game