import logging
from .map import GameMap
from .player import Player
from .input_handler import InputHandler
from .demo_handler import DemoHandler
from .game_renderer import GameRenderer
from ..ui.message_pane import MessagePane, MessageCategory
from ..ui.header_bar import HeaderBar
from ..ui.loading_overlay import AsyncOperationManager, LoadingStyle
from ..ui.layout_manager import LayoutManager
from ..core.state import GameState, GamePhase
from ..core.terminal import BlessedTerminal, Position, Color
from ..core.config import get_config, ConfigSection
from ..core.logging_config import LoggingConfig


def run_game():
    # Initialize logging
    debug_config = get_config(ConfigSection.DEBUG)
    LoggingConfig.setup_logging(
        log_level="DEBUG",  # Always use DEBUG for now to debug connectivity
        log_to_console=False,  # Don't interfere with game display
        log_to_file=True,
        detailed_format=True  # Use detailed format to see where messages come from
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting MageMines game loop")
    
    # Load configuration
    ui_config = get_config(ConfigSection.UI)
    display_config = get_config(ConfigSection.DISPLAY)
    game_config = get_config(ConfigSection.GAME)
    
    # Create terminal adapter first to get terminal dimensions
    terminal_adapter = BlessedTerminal()
    
    # Setup terminal
    terminal_adapter.setup()
    
    try:
        # Create layout manager
        layout_manager = LayoutManager(
            terminal_adapter.width,
            terminal_adapter.height,
            ui_config.message_pane_width
        )
        
        # Calculate layout
        layout = layout_manager.calculate_layout()
        
        # Create header bar at the top
        header_bar = HeaderBar(
            terminal_adapter,
            layout.header_position,
            layout.header_width
        )
        
        # Create game components with appropriate sizes
        # Enable multi-level dungeons
        game_map = GameMap(
            layout.map_width, 
            layout.map_height, 
            x_offset=layout.map_position.x, 
            y_offset=layout.map_position.y, 
            use_levels=True
        )
        
        # Get starting position from the generated map
        start_x, start_y = game_map.get_starting_position()
        player = Player(1, start_x, start_y)  # Entity ID 1 for player
        game_state = GameState()
        game_state.phase = GamePhase.PLAYING
        input_handler = InputHandler()
        
        # Create async operation manager for loading indicators
        async_manager = AsyncOperationManager(terminal_adapter)
        
        # Create message pane on the right side of the screen, below header
        message_pane = MessagePane(
            terminal_adapter, 
            layout.message_position, 
            layout.message_width, 
            layout.message_height
        )
        input_handler.set_message_pane(message_pane)
        message_pane._current_turn = game_state.turn.turn_number
        
        # Pass message pane to game map for debug output
        game_map.set_message_pane(message_pane)
        
        # Create demo handler
        demo_handler = DemoHandler(async_manager, message_pane)
        
        # Create game renderer
        renderer = GameRenderer(terminal_adapter, header_bar, message_pane, async_manager)
        
        # Set initial header stats
        header_bar.set_stat("turn", "Turn", game_state.turn.turn_number, Color(255, 255, 100))
        header_bar.set_stat("depth", "Depth", game_map.get_current_depth(), Color(100, 200, 255))
        
        # Initial render
        renderer.render_initial_screen(game_map, player)
        
        # Welcome messages
        add_welcome_messages(message_pane, game_map.get_current_depth())
        demo_handler.add_help_messages()

        # Main game loop
        while True:
            did_full_redraw = False
            
            # Update demo progress
            demo_handler.update()
            
            # Check if we need a full redraw
            if async_manager.needs_full_redraw:
                renderer.render_full_redraw(game_map, player)
                async_manager.needs_full_redraw = False
                did_full_redraw = True
            
            # Get key with timeout to prevent buffer overflow
            key = terminal_adapter._term.inkey(timeout=0.01)
            
            # Skip if no key pressed or input is locked
            if not key or async_manager.input_locked:
                renderer.render_frame(game_map, player, did_full_redraw)
                continue
                
            # Handle demo keys
            if demo_handler.handle_key(str(key)):
                continue
                
            # Clear player from old position
            game_map.clear_player(terminal_adapter._term, player)
            
            # Process game input
            result = input_handler.process_input(str(key), player, game_map, game_state)
            
            if result == "QUIT":
                break
            
            # Handle level changes
            if result == "LEVEL_CHANGE":
                header_bar.set_stat("depth", "Depth", game_map.get_current_depth(), Color(100, 200, 255))
                renderer.handle_level_change(game_map, player)
                did_full_redraw = True
            
            # Handle inventory toggle
            if result == "SHOW_INVENTORY":
                renderer.toggle_inventory()
                did_full_redraw = True
            
            # Update turn counter if action was taken
            if result and result not in ["SCROLL", "LEVEL_CHANGE"]:
                game_state.turn.turn_number += 1
                message_pane._current_turn = game_state.turn.turn_number
                header_bar.set_stat("turn", "Turn", game_state.turn.turn_number, Color(255, 255, 100))
            
            # Render frame
            renderer.render_frame(game_map, player, did_full_redraw)
            
            # Clear any remaining input to prevent buffer overflow
            while terminal_adapter._term.inkey(timeout=0):
                pass
    finally:
        # Cleanup terminal
        terminal_adapter.cleanup()


def add_welcome_messages(message_pane: MessagePane, current_depth: int) -> None:
    """Add welcome messages to the message pane.
    
    Args:
        message_pane: The message pane to add messages to
        current_depth: The current dungeon depth
    """
    message_pane.add_message("Welcome to MageMines!", MessageCategory.SYSTEM)
    message_pane.add_message("Movement: hjkl (vim-style), yubn (diagonals)", MessageCategory.SYSTEM)
    message_pane.add_message("Commands: . (wait), q (quit), o (open door), g (gather), i (inventory)", MessageCategory.SYSTEM)
    message_pane.add_message("Stairs: < (go up), > (go down)", MessageCategory.SYSTEM)
    message_pane.add_message("Messages: -/+ to scroll", MessageCategory.SYSTEM)
    message_pane.add_message(f"You are on level {current_depth}", MessageCategory.INFO)
