from blessed import Terminal
from .map import GameMap
from .player import Player
from .input_handler import handle_input

term = Terminal()

def run_game():
    game_map = GameMap(80, 24)
    player = Player(10, 10)

    with term.fullscreen(), term.cbreak(), term.hidden_cursor():
        game_map.draw_static(term)  # Draw map once
        game_map.draw_player(term, player)

        while True:
            key = term.inkey()
            if key == 'q':
                break
            game_map.clear_player(term, player)
            handle_input(key, player, game_map)
            game_map.draw_player(term, player)
