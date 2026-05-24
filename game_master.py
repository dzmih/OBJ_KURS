from game_map import Map
from game_logger import GameLogger
from ships import ShipFactory
from players import HumanPlayer, AIPlayer, CheaterPlayer
import pickle
import random

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
        self.attach(GameLogger())
        self.players = {}
        self.winner = None

    def auto_place_ships(self, player_mark):
        fleet = [
            'carrier',
            'submarine',
            'submarine',
            'destroyer',
            'destroyer',
            'destroyer',
            'patrol',
            'patrol',
            'patrol',
            'patrol'
        ]

        for ship_type in fleet:
            placed = False

            while not placed:
                x = random.randint(0, self.map.size - 1)
                y = random.randint(0, self.map.size - 1)
                horizontal = random.choice([True, False])

                placed = self.place_ship_for_player(
                    player_mark,
                    ship_type,
                    x,
                    y,
                    horizontal
                )

    def set_players(self, type_a, type_b):
        p_classes = {'human': HumanPlayer, 'ai': AIPlayer, 'cheater': CheaterPlayer}
        self.players['A'] = p_classes[type_a]('A')
        self.players['B'] = p_classes[type_b]('B')

    def place_ship_for_player(self, player_mark, ship_type, x, y, horizontal):
        try:
            ship = ShipFactory.create_ship(ship_type, player_mark)
            return self.map.place_ship(player_mark, ship, x, y, horizontal)
        except Exception as e:
            self.notify("error", message=str(e))
            return False

    def process_turn(self, attacker_mark):
        defender_mark = 'B' if attacker_mark == 'A' else 'A'
        player_obj = self.players[attacker_mark]

        enemy_view = self.map.get_masked_map(defender_mark)
        result = player_obj.make_move(self.map.size, enemy_view)

        if result == 'save' or result == ('save', 'save'):
            return 'save'

        if isinstance(result, list):
            shots = result
        else:
            shots = [result]

        for (x, y) in shots:
            try:
                hit_success, sunk_ship_type = self.map.process_shot(defender_mark, x, y)
            except ValueError as e:
                self.notify("error", message=str(e))
                continue

            self.notify("shot", player=attacker_mark, x=x, y=y, hit=hit_success, ship_type=sunk_ship_type)

            if self.map.check_loss(defender_mark):
                self.winner = attacker_mark
                self.notify("win", winner=attacker_mark)
                return

    def save_game(self, filename):
        obs = self._observers
        self._observers = []
        with open(filename, 'wb') as f:
            pickle.dump(self, f)
        self._observers = obs

    @staticmethod
    def load_game(filename):
        with open(filename, 'rb') as f:
            game = pickle.load(f)
            game.attach(GameLogger())
            return game
