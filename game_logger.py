import logging
from datetime import datetime
from abc import ABC, abstractmethod

# --- PATTERN: OBSERVER ---

class Observer(ABC):
    @abstractmethod
    def update(self, event_type, **kwargs):
        pass

class GameLogger(Observer):
    def __init__(self):
        # Очищуємо файл при старті
        open("game_res.log", "w").close()
        
        logging.basicConfig(level=logging.INFO, filename="game_res.log", filemode="a", format='%(asctime)s - %(message)s')
        self.logger = logging.getLogger('SeaBattle')
        self.shots_history = []
        print("Logger initialized.")

    def update(self, event_type, **kwargs):
        if event_type == "shot":
            self._log_shot(kwargs.get('player'), kwargs.get('x'), kwargs.get('y'), 
                           kwargs.get('hit'), kwargs.get('ship_type'))
        elif event_type == "win":
            self._log_winner(kwargs.get('winner'))
        elif event_type == "error":
            self._log_error(kwargs.get('message'))

    def _log_shot(self, player, x, y, hit_success, ship_type=None):
        shot_data = {
            'player': player,
            'x': x, 'y': y,
            'hit': hit_success,
            'ship_type': ship_type,
            'timestamp': datetime.now()
        }
        self.shots_history.append(shot_data)

        if hit_success:
            msg = f"Player {player} HIT at ({x},{y}) -> {ship_type}"
            self.logger.info(msg)
            print(f"LOG: {msg}")
        else:
            msg = f"Player {player} MISSED at ({x},{y})"
            self.logger.info(msg)
            print(f"LOG: {msg}")

    def _log_winner(self, winner):
        msg = f"Player {winner} WON the game!"
        self.logger.info(msg)
        print(f"\n*** {msg} ***\n")

    def _log_error(self, message):
        self.logger.error(f"Error: {message}")