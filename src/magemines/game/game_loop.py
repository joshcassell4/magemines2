import logging
from .optimized_map import OptimizedGameMap
from .player import Player
from .input_handler import InputHandler
from .demo_handler import DemoHandler
from .game_renderer import GameRenderer
from .systems import AISystem
from .entities.mages import create_mage
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
        game_map = OptimizedGameMap(
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
        
        # Add player to entity manager
        game_map.add_entity(player)
        
        # Create AI system
        ai_system = AISystem(game_map.entity_manager, game_map)
        
        # Create message pane early so spawn_test_mages can use it
        message_pane = MessagePane(
            terminal_adapter, 
            layout.message_position, 
            layout.message_width, 
            layout.message_height
        )
        
        # Set message pane for AI system
        ai_system.set_message_pane(message_pane)
        
        # Spawn some test mages
        spawn_test_mages(game_map, message_pane)
        
        # Create async operation manager for loading indicators
        async_manager = AsyncOperationManager(terminal_adapter)
        
        # Set message pane for input handler
        input_handler.set_message_pane(message_pane)
        message_pane.set_current_turn(game_state.turn.turn_number)
        
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
                
            # Handle message log viewer keys if it's visible
            if renderer.message_log_viewer.visible:
                if renderer.message_log_viewer.handle_key(str(key)):
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
                # Don't set did_full_redraw here - let the async_manager handle it
            
            # Handle message log toggle
            if result == "SHOW_MESSAGE_LOG":
                renderer.toggle_message_log()
                # Don't set did_full_redraw here - let the async_manager handle it
            
            # Update turn counter if action was taken
            if result and result not in ["SCROLL", "LEVEL_CHANGE", "SHOW_INVENTORY", "SHOW_MESSAGE_LOG"]:
                game_state.turn.turn_number += 1
                message_pane.set_current_turn(game_state.turn.turn_number)
                header_bar.set_stat("turn", "Turn", game_state.turn.turn_number, Color(255, 255, 100))
                
                # Process AI turns
                ai_system.process_turn(player)
            
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
    message_pane.add_message("Welcome to MageMines!", MessageCategory.SYSTEM, turn=0)
    message_pane.add_message("Movement: hjkl (vim-style), yubn (diagonals)", MessageCategory.SYSTEM, turn=0)
    message_pane.add_message("Commands: . (wait), q (quit), o (open door), g (gather), i (inventory)", MessageCategory.SYSTEM, turn=0)
    message_pane.add_message("Stairs: < (go up), > (go down)", MessageCategory.SYSTEM, turn=0)
    message_pane.add_message("Messages: -/+ to scroll, L (view full log)", MessageCategory.SYSTEM, turn=0)
    message_pane.add_message(f"You are on level {current_depth}", MessageCategory.INFO, turn=0)


def spawn_test_mages(game_map, message_pane):
    """Spawn some test mages on the map."""
    import random
    from ..game.components import Name
    
    # Try to spawn a few mages in empty positions
    mage_types = ["apprentice", "elemental", "scholar", "hermit"]
    
    for i in range(3):  # Spawn 3 mages
        # Find an empty position
        attempts = 0
        while attempts < 50:
            x = random.randint(1, game_map.width - 2)
            y = random.randint(1, game_map.height - 2)
            
            # Check if position is empty
            if (game_map.get_tile_at(x, y) == '.' and 
                not game_map.is_blocked_by_entity(x, y)):
                
                # Create a mage
                mage_type = random.choice(mage_types)
                entity_id = game_map.entity_manager.next_id
                
                # Special handling for elemental mages
                if mage_type == "elemental":
                    element = random.choice(["fire", "ice", "lightning"])
                    mage = create_mage(mage_type, entity_id, x, y, element=element)
                else:
                    mage = create_mage(mage_type, entity_id, x, y)
                
                if mage:
                    game_map.add_entity(mage)
                    
                    # Get mage name for message
                    name_comp = mage.get_component(Name)
                    mage_name = name_comp.full_name if name_comp else f"{mage_type} mage"
                    
                    message_pane.add_message(
                        f"A {mage_name} appears in the dungeon!",
                        MessageCategory.INFO,
                        turn=0
                    )
                    
                    logger = logging.getLogger(__name__)
                    logger.info(f"Spawned {mage_type} mage at ({x}, {y})")
                break
            
            attempts += 1
