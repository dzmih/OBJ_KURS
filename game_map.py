class Map:
    def __init__(self, size):
        self.size = size
        self.mapA = [['.' for _ in range(size)] for _ in range(size)]
        self.mapB = [['.' for _ in range(size)] for _ in range(size)]
        self.shipsA = []
        self.shipsB = []

    def _get_board_and_ships(self, player_mark):
        board = self.mapA if player_mark == 'A' else self.mapB
        ships_list = self.shipsA if player_mark == 'A' else self.shipsB
        return board, ships_list

    def _is_within_bounds(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def _can_place_ship(self, board, coordinates):
        for ship_x, ship_y in coordinates:
            for check_y in range(ship_y - 1, ship_y + 2):
                for check_x in range(ship_x - 1, ship_x + 2):
                    if self._is_within_bounds(check_x, check_y) and board[check_y][check_x] != '.':
                        return False
        return True

    def place_ship(self, player_mark, ship, x, y, horizontal):
        board, ships_list = self._get_board_and_ships(player_mark)

        coordinates = []
        if horizontal:
            if x + ship.length > self.size:
                return False
            for i in range(ship.length):
                coordinates.append((x + i, y))
        else:
            if y + ship.length > self.size:
                return False
            for i in range(ship.length):
                coordinates.append((x, y + i))

        if not self._can_place_ship(board, coordinates):
            return False

        ship.place(x, y, horizontal)
        ships_list.append(ship)

        char_symbol = 'S'
        for ship_x, ship_y in coordinates:
            board[ship_y][ship_x] = char_symbol
        return True

    def get_masked_map(self, target_player_mark):
        real_map = self.mapA if target_player_mark == 'A' else self.mapB
        masked_map = []
        for row in real_map:
            new_row = []
            for cell in row:
                if cell == 'S':
                    new_row.append('.')
                else:
                    new_row.append(cell) # 'X', 'o', '.' залишаються
            masked_map.append(new_row)
        return masked_map

    def check_loss(self, player_mark):
        ships = self.shipsA if player_mark == 'A' else self.shipsB
        return all(ship.is_sunk for ship in ships)

    def print_boards(self):
        print("\n--- Current State ---")
        print("Player A Map (Real):")
        for row in self.mapA: print(" ".join(row))
        print("\nPlayer B Map (Real):")
        for row in self.mapB: print(" ".join(row))

    def process_shot(self, defender_mark, x, y):
        target_board = self.mapA if defender_mark == 'A' else self.mapB
        target_ships = self.shipsA if defender_mark == 'A' else self.shipsB

        hit_success = False
        sunk_ship_type = None

        cell = target_board[y][x]
        if cell == 'S':
            target_board[y][x] = 'X'
            hit_success = True

            for ship in target_ships:
                if (x, y) in ship.coordinates:
                    if ship.hit():
                        sunk_ship_type = f"{ship.name} (SUNK!)"
                    else:
                        sunk_ship_type = ship.name
                    break
        elif cell == '.':
            target_board[y][x] = 'o'
        else:
            raise ValueError(f"Player fired at {x},{y} again.")

        return hit_success, sunk_ship_type