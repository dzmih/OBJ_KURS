from game_master import MasterClass
import os

def setup_phase(game):
    # Для прикладу розставимо кораблі автоматично або фіксовано для швидкості,
    # Або запитаємо для Humans. Для демо зробимо хардкод розстановки для обох.
    ships_to_place = [('carrier', 0, 0, True), ('destroyer', 0, 2, True), ('submarine', 0, 4, True)]
    
    print("Auto-placing ships for demo purposes...")
    for s_type, x, y, h in ships_to_place:
        game.place_ship_for_player('A', s_type, x, y, h)
        # Дзеркально для B
        game.place_ship_for_player('B', s_type, x, y, h)

def main():
    print("=== SEA BATTLE PATTERNS EDITION ===")
    
    action = input("1. New Game\n2. Load Game\nSelect: ").strip()
    
    if action == '2':
        fname = input("Filename: ")
        try:
            game = MasterClass.load_game(fname)
            print("Game loaded!")
        except Exception as e:
            print(f"Load failed: {e}. Starting new.")
            game = MasterClass()
    else:
        game = MasterClass()
        print("Select player types (1: Human, 2: AI):")
        t1 = 'human' if input("Player A (1/2): ") == '1' else 'ai'
        t2 = 'human' if input("Player B (1/2): ") == '1' else 'ai'
        game.set_players(t1, t2)
        setup_phase(game)

    attacker = 'A'
    
    while not game.winner:
        print(f"\n--- Turn: Player {attacker} ---")
        # Для людини можна показати карту
        if isinstance(game.players[attacker], game.players[attacker].__class__): # Hack check
            # game.map.print_boards() # Cheat view for debugging
            pass

        result = game.process_turn(attacker)
        
        if result == 'save':
            fname = input("Save filename: ")
            game.save_game(fname)
            print("Game saved.")
            continue

        if game.winner:
            break
            
        attacker = 'B' if attacker == 'A' else 'A'

if __name__ == "__main__":
    main()