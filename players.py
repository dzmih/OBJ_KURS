from abc import ABC, abstractmethod
import random

# --- PATTERN: STRATEGY ---
# Context is the GameMaster utilizing these strategies, 
# or the Player class itself acting as the strategy interface.

class Player(ABC):
    def __init__(self, name):
        self.name = name
    
    @abstractmethod
    def make_move(self, game_map_size, enemy_map_view):
        """
        Повертає координати (x, y) для пострілу.
        enemy_map_view - це копія карти ворога, яку бачить гравець.
        """
        pass

class HumanPlayer(Player):
    def make_move(self, game_map_size, enemy_map_view):
        while True:
            try:
                s = input(f"Player {self.name}, enter attack coordinates (x y): ").strip()
                if s.lower() == 'save':
                    return 'save', 'save' # Signal to save
                
                parts = list(map(int, s.split()))
                if len(parts) != 2:
                    print("Please enter exactly two numbers.")
                    continue
                    
                x, y = parts
                if 0 <= x < game_map_size and 0 <= y < game_map_size:
                    return x, y
                print(f"Coordinates must be between 0 and {game_map_size-1}")
            except ValueError:
                print("Invalid input. Enter numbers.")

class AIPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.last_hit = None # Memory for smarter shots

    def make_move(self, game_map_size, enemy_map_view):
        print(f"AI {self.name} is thinking...")
        # Спрощена логіка: стріляємо випадково, але не туди, де вже стріляли
        available_moves = []
        for y in range(game_map_size):
            for x in range(game_map_size):
                # 'o' - промах, 'X'/'Y' - влучання. Стріляємо тільки по '.' (невідомо)
                if enemy_map_view[y][x] == '.':
                    available_moves.append((x, y))
        
        if not available_moves:
            return 0, 0 # Fallback

        return random.choice(available_moves)

class CheaterPlayer(Player):
    def make_move(self, game_map_size, enemy_map_view):
        # Чітер шукає кораблі безпосередньо у логіці гри (тут емуляція "удачі")
        print(f"Cheater {self.name} activates satellite scan...")
        # У реальній грі тут має бути доступ до прихованої карти, 
        # але в рамках патерну ми повертаємо просто наступну доступну клітинку, 
        # або реалізуємо логіку "scan" через MasterClass, якщо передати туди повний доступ.
        # Для простоти - стріляє як AI, але дуже швидко (random for demo)
        return random.randint(0, game_map_size-1), random.randint(0, game_map_size-1)