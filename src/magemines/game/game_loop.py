from .map import GameMap
from .player import Player
from .input_handler import InputHandler
from ..ui.message_pane import MessagePane, MessageCategory
from ..core.state import GameState
from ..core.terminal import BlessedTerminal, Position


def run_game():
    game_map = GameMap(80, 24)
    player = Player(10, 10)
    game_state = GameState()
    input_handler = InputHandler()
    
    # Create terminal adapter
    terminal_adapter = BlessedTerminal()
    
    # Create message pane at the bottom of the screen
    message_pane = MessagePane(terminal_adapter, Position(0, 19), 80, 5)
    input_handler.set_message_pane(message_pane)

    # Setup terminal
    terminal_adapter.setup()
    
    try:
        game_map.draw_static(terminal_adapter._term)  # Draw map once
        game_map.draw_player(terminal_adapter._term, player)
        message_pane.render()
        
        # Welcome message
        message_pane.add_message("Welcome to MageMines! Use hjkl to move, q to quit.", MessageCategory.SYSTEM)

        while True:
            key = terminal_adapter._term.inkey()
            
            game_map.clear_player(terminal_adapter._term, player)
            
            result = input_handler.process_input(key, player, game_map, game_state)
            
            if result == "QUIT":
                break
            
            game_map.draw_player(terminal_adapter._term, player)
            message_pane.render()
    finally:
        # Cleanup terminal
        terminal_adapter.cleanup()
