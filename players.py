from abc import ABC, abstractmethod
import random

class Player(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def make_move(self, game_map_size, enemy_map_view):
        pass


class HumanPlayer(Player):
    def make_move(self, game_map_size, enemy_map_view):
        while True:
            try:
                s = input(f"Player {self.name}, enter attack coordinates (x y): ").strip()
                if s.lower() == 'save':
                    return 'save', 'save'  # Signal to save

                parts = list(map(int, s.split()))
                if len(parts) != 2:
                    print("Please enter exactly two numbers.")
                    continue

                x, y = parts
                if 0 <= x < game_map_size and 0 <= y < game_map_size:
                    return x, y
                print(f"Coordinates must be between 0 and {game_map_size - 1}")
            except ValueError:
                print("Invalid input. Enter numbers.")


class AIPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.last_hit = None

    def make_move(self, game_map_size, enemy_map_view):
        print(f"AI {self.name} is thinking...")
        available_moves = []
        for y in range(game_map_size):
            for x in range(game_map_size):
                if enemy_map_view[y][x] == '.':
                    available_moves.append((x, y))

        if not available_moves:
            return 0, 0

        return random.choice(available_moves)


class CheaterPlayer(Player):
    def make_move(self, game_map_size, enemy_map_view):
        print(f"Cheater {self.name} activates satellite scan... (2 shots!)")
        available = [(x, y) for y in range(game_map_size)
                     for x in range(game_map_size)
                     if enemy_map_view[y][x] == '.']
        if not available:
            return []
        shots = random.sample(available, min(2, len(available)))
        return shots