from abc import ABC, abstractmethod

# Abstract Product
class Ship(ABC):
    def __init__(self, length, symbol, name):
        self.length = length
        self.symbol = symbol
        self.name = name
        self.health = length
        self.coordinates = []
        self.is_sunk = False

    def place(self, x, y, horizontal):
        self.coordinates = []
        if horizontal:
            for i in range(self.length):
                self.coordinates.append((x + i, y))
        else:
            for i in range(self.length):
                self.coordinates.append((x, y + i))

    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.is_sunk = True
        return self.is_sunk

# Concrete Products
class Destroyer(Ship):
    def __init__(self, symbol):
        super().__init__(2, symbol, "Destroyer")

class Submarine(Ship):
    def __init__(self, symbol):
        super().__init__(3, symbol, "Submarine")

class AircraftCarrier(Ship):
    def __init__(self, symbol):
        super().__init__(4, symbol, "AircraftCarrier")

class PatrolBoat(Ship):
    def __init__(self, symbol):
        super().__init__(1, symbol, "PatrolBoat")

# --- PATTERN: FACTORY METHOD ---
class ShipFactory:
    @staticmethod
    def create_ship(ship_type, symbol):
        if ship_type == 'destroyer':
            return Destroyer(symbol)
        elif ship_type == 'submarine':
            return Submarine(symbol)
        elif ship_type == 'carrier':
            return AircraftCarrier(symbol)
        elif ship_type == 'patrol':
            return PatrolBoat(symbol)
        else:
            raise ValueError(f"Unknown ship type: {ship_type}")