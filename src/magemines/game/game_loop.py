import time
from .map import GameMap
from .player import Player
from .input_handler import InputHandler
from ..ui.message_pane import MessagePane, MessageCategory
from ..ui.header_bar import HeaderBar
from ..ui.loading_overlay import AsyncOperationManager, LoadingStyle
from ..core.state import GameState, GamePhase
from ..core.terminal import BlessedTerminal, Position, Color
from ..core.config import get_config, ConfigSection


def run_game():
    # Load configuration
    ui_config = get_config(ConfigSection.UI)
    display_config = get_config(ConfigSection.DISPLAY)
    game_config = get_config(ConfigSection.GAME)
    debug_config = get_config(ConfigSection.DEBUG)
    
    # Create terminal adapter first to get terminal dimensions
    terminal_adapter = BlessedTerminal()
    
    # Setup terminal
    terminal_adapter.setup()
    
    try:
        # Get terminal dimensions
        term_width = terminal_adapter.width
        term_height = terminal_adapter.height
        
        # Define layout - header bar at top, map and message pane below
        header_height = 1
        
        # Use configured message pane width
        message_pane_width = ui_config.message_pane_width
        message_pane_x = term_width - message_pane_width  # Flush with right side
        message_pane_height = term_height - header_height - 2
        
        # Calculate map area using remaining space
        available_map_width = message_pane_x - 2  # Leave 2 chars margin between map and message pane
        available_map_height = term_height - header_height - 2  # Available height below header
        
        map_width = min(80, available_map_width)  # Larger map area, up to 80 chars wide
        map_height = min(40, available_map_height)  # Larger map area, up to 40 chars tall
        
        # Center the map in the available space
        map_x_offset = (available_map_width - map_width) // 2
        map_y_offset = header_height + ((available_map_height - map_height) // 2)
        
        # Create header bar at the top
        header_bar = HeaderBar(
            terminal_adapter,
            Position(0, 0),
            term_width
        )
        
        # Create game components with appropriate sizes
        # Enable multi-level dungeons
        game_map = GameMap(map_width, map_height, x_offset=map_x_offset, y_offset=map_y_offset, use_levels=True)
        
        # Get starting position from the generated map
        start_x, start_y = game_map.get_starting_position()
        player = Player(start_x, start_y)
        game_state = GameState()
        game_state.phase = GamePhase.PLAYING
        input_handler = InputHandler()
        
        # Create async operation manager for loading indicators
        async_manager = AsyncOperationManager(terminal_adapter)
        
        # Demo tracking
        demo_start_time = None
        demo_progress = 0.0
        
        # Create message pane on the right side of the screen, below header
        message_pane = MessagePane(
            terminal_adapter, 
            Position(message_pane_x, header_height), 
            message_pane_width, 
            message_pane_height
        )
        input_handler.set_message_pane(message_pane)
        message_pane._current_turn = game_state.turn.turn_number
        
        # Set initial header stats
        header_bar.set_stat("turn", "Turn", game_state.turn.turn_number, Color(255, 255, 100))
        header_bar.set_stat("depth", "Depth", game_map.get_current_depth(), Color(100, 200, 255))
        
        # Clear screen and draw initial state
        terminal_adapter.clear()
        header_bar.render(force=True)  # Draw header first (force after clear)
        game_map.draw_static(terminal_adapter._term)  # Draw map once
        game_map.draw_player(terminal_adapter._term, player)
        message_pane.render()
        
        # Welcome message
        message_pane.add_message("Welcome to MageMines!", MessageCategory.SYSTEM)
        message_pane.add_message("Movement: hjkl (vim-style), yubn (diagonals)", MessageCategory.SYSTEM)
        message_pane.add_message("Commands: . (wait), q (quit), o (open door)", MessageCategory.SYSTEM)
        message_pane.add_message("Stairs: < (go up), > (go down)", MessageCategory.SYSTEM)
        message_pane.add_message("Messages: -/+ to scroll", MessageCategory.SYSTEM)
        message_pane.add_message("Demo: L (spinner), P (progress), D (dots), C (cancel)", MessageCategory.SYSTEM)
        message_pane.add_message(f"You are on level {game_map.get_current_depth()}", MessageCategory.INFO)

        while True:
            did_full_redraw = False  # Track if we did a full redraw this iteration
            
            # Handle demo timeout/progress
            if async_manager.loading_overlay.active and demo_start_time:
                elapsed = time.time() - demo_start_time
                
                # Auto-complete demos after timeout or progress
                if async_manager.loading_overlay._indicator:
                    if async_manager.loading_overlay._indicator.style == LoadingStyle.SPINNER:
                        # Spinner demo lasts 3 seconds
                        if elapsed > 3.0:
                            message_pane.add_message("Divine energy channeled!", MessageCategory.DIVINE)
                            async_manager.end_operation()
                            demo_start_time = None
                    elif async_manager.loading_overlay._indicator.style == LoadingStyle.DOTS:
                        # Dots demo lasts 2 seconds
                        if elapsed > 2.0:
                            message_pane.add_message("The spirits have spoken!", MessageCategory.DIALOGUE)
                            async_manager.end_operation()
                            demo_start_time = None
                    elif async_manager.loading_overlay._indicator.style == LoadingStyle.PROGRESS_BAR:
                        # Progress bar advances over 4 seconds
                        demo_progress = min(1.0, elapsed / 4.0)
                        async_manager.update_progress(demo_progress)
                        if demo_progress >= 1.0:
                            message_pane.add_message("Ancient knowledge downloaded!", MessageCategory.SPELL)
                            async_manager.end_operation()
                            demo_start_time = None
                            demo_progress = 0.0
            
            # Render loading overlay if active
            async_manager.render()
            
            # Check if we need to redraw the entire screen
            if async_manager.needs_full_redraw:
                # Clear screen and redraw everything
                terminal_adapter.clear()
                header_bar.render(force=True)  # Force full redraw after clear
                game_map.draw_static(terminal_adapter._term)
                game_map.draw_player(terminal_adapter._term, player)
                message_pane.force_full_redraw()  # Properly reset message pane
                message_pane.render()
                async_manager.needs_full_redraw = False
                did_full_redraw = True
            
            # Get key with timeout to prevent buffer overflow
            key = terminal_adapter._term.inkey(timeout=0.01)
            
            # Skip if no key pressed or input is locked
            if not key or async_manager.input_locked:
                continue
                
            # Demo: Show loading indicator for certain commands (using uppercase to avoid conflicts)
            if str(key) == 'L' and not async_manager.loading_overlay.active:
                # Demo loading spinner
                async_manager.start_operation("Loading magical energies", LoadingStyle.SPINNER)
                message_pane.add_message("Channeling divine power...", MessageCategory.DIVINE)
                message_pane.render()  # Force message to show immediately
                async_manager.render()  # Force overlay to render immediately
                demo_start_time = time.time()
                demo_progress = 0.0
                continue
            elif str(key) == 'P' and not async_manager.loading_overlay.active:
                # Demo progress bar
                async_manager.start_operation("Downloading ancient knowledge", LoadingStyle.PROGRESS_BAR)
                message_pane.add_message("Connecting to the astral plane...", MessageCategory.SPELL)
                message_pane.render()  # Force message to show immediately
                async_manager.render()  # Force overlay to render immediately
                demo_start_time = time.time()
                demo_progress = 0.0
                continue
            elif str(key) == 'D' and not async_manager.loading_overlay.active:
                # Demo dots animation
                async_manager.start_operation("Thinking", LoadingStyle.DOTS)
                message_pane.add_message("The spirits are contemplating...", MessageCategory.DIALOGUE)
                message_pane.render()  # Force message to show immediately
                async_manager.render()  # Force overlay to render immediately
                demo_start_time = time.time()
                demo_progress = 0.0
                continue
            elif str(key) == 'C' and async_manager.loading_overlay.active:
                # Cancel/complete loading demo
                message_pane.add_message("Operation cancelled!", MessageCategory.SYSTEM)
                async_manager.end_operation()
                demo_start_time = None
                demo_progress = 0.0
                continue
                
            game_map.clear_player(terminal_adapter._term, player)
            
            result = input_handler.process_input(key, player, game_map, game_state)
            
            if result == "QUIT":
                break
            
            # Handle level changes
            if result == "LEVEL_CHANGE":
                # Need to redraw the entire map
                terminal_adapter.clear()
                header_bar.set_stat("depth", "Depth", game_map.get_current_depth(), Color(100, 200, 255))
                header_bar.render(force=True)  # Force full redraw after clear
                game_map.draw_static(terminal_adapter._term)
                game_map.draw_player(terminal_adapter._term, player)
                message_pane.force_full_redraw()
                message_pane.render()
                did_full_redraw = True
            
            # If an action was taken (movement, wait, etc), advance the turn
            if result and result not in ["SCROLL", "LEVEL_CHANGE"]:
                game_state.turn.turn_number += 1
                message_pane._current_turn = game_state.turn.turn_number
                # Update header turn counter
                header_bar.set_stat("turn", "Turn", game_state.turn.turn_number, Color(255, 255, 100))
            
            # Only render if we didn't do a full redraw
            if not did_full_redraw:
                game_map.draw_player(terminal_adapter._term, player)
                header_bar.render()  # Render header (only redraws if changed)
                message_pane.render()  # Render messages (only redraws if changed)
            
            # Clear any remaining input to prevent buffer overflow
            while terminal_adapter._term.inkey(timeout=0):
                pass
    finally:
        # Cleanup terminal
        terminal_adapter.cleanup()
