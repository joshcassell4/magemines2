"""Game Renderer handles all rendering operations."""

from typing import Optional
from .map import GameMap
from .player import Player
from ..ui.header_bar import HeaderBar
from ..ui.message_pane import MessagePane
from ..ui.loading_overlay import AsyncOperationManager
from ..core.terminal import BlessedTerminal


class GameRenderer:
    """Handles all game rendering operations."""
    
    def __init__(self, terminal: BlessedTerminal, header_bar: HeaderBar, 
                 message_pane: MessagePane, async_manager: AsyncOperationManager):
        """Initialize the game renderer.
        
        Args:
            terminal: Terminal adapter for rendering
            header_bar: Header bar UI component
            message_pane: Message pane UI component
            async_manager: Async operation manager for overlays
        """
        self.terminal = terminal
        self.header_bar = header_bar
        self.message_pane = message_pane
        self.async_manager = async_manager
        
    def render_initial_screen(self, game_map: GameMap, player: Player) -> None:
        """Render the initial game screen.
        
        Args:
            game_map: The game map to render
            player: The player to render
        """
        self.terminal.clear()
        self.header_bar.render(force=True)
        game_map.draw_static(self.terminal._term)
        game_map.draw_player(self.terminal._term, player)
        self.message_pane.render()
        
    def render_full_redraw(self, game_map: GameMap, player: Player) -> None:
        """Perform a full screen redraw.
        
        Args:
            game_map: The game map to render
            player: The player to render
        """
        self.terminal.clear()
        self.header_bar.render(force=True)
        game_map.draw_static(self.terminal._term)
        game_map.draw_player(self.terminal._term, player)
        self.message_pane.force_full_redraw()
        self.message_pane.render()
        
    def render_frame(self, game_map: GameMap, player: Player, 
                     did_full_redraw: bool = False) -> None:
        """Render a single frame update.
        
        Args:
            game_map: The game map to render
            player: The player to render
            did_full_redraw: Whether a full redraw was already performed
        """
        # Render loading overlay if active
        self.async_manager.render()
        
        # Check if we need a full redraw
        if self.async_manager.needs_full_redraw:
            self.render_full_redraw(game_map, player)
            self.async_manager.needs_full_redraw = False
        elif not did_full_redraw:
            # Normal frame update - only redraw changed elements
            game_map.draw_player(self.terminal._term, player)
            self.header_bar.render()  # Only redraws if changed
            self.message_pane.render()  # Only redraws if changed
            
    def handle_level_change(self, game_map: GameMap, player: Player) -> None:
        """Handle rendering after a level change.
        
        Args:
            game_map: The game map to render
            player: The player to render
        """
        self.render_full_redraw(game_map, player)