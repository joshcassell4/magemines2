"""Optimized map rendering with dirty region tracking."""

import logging
from typing import Optional, Dict, Tuple, Set
from .map import GameMap
from .entities import Entity
from .components import Position
from ..core.performance import DirtyRegionTracker, BatchRenderer, BufferedChar
from ..core.terminal import Color


class OptimizedGameMap(GameMap):
    """Game map with optimized rendering using dirty region tracking."""
    
    def __init__(self, width, height, x_offset=0, y_offset=0, use_procedural=True, use_levels=False):
        """Initialize optimized game map.
        
        Args:
            width: Map width
            height: Map height
            x_offset: X offset for rendering
            y_offset: Y offset for rendering
            use_procedural: Whether to use procedural generation
            use_levels: Whether to use level system
        """
        super().__init__(width, height, x_offset, y_offset, use_procedural, use_levels)
        
        # Optimization structures
        self.dirty_tracker = DirtyRegionTracker(width, height)
        self.last_rendered_tiles: Dict[Tuple[int, int], Tuple[str, Color]] = {}
        self.last_entity_positions: Dict[int, Tuple[int, int]] = {}  # entity_id -> (x, y)
        self.batch_renderer = None  # Will be initialized when terminal is available
        
        # Track which tiles changed this frame
        self.changed_tiles: Set[Tuple[int, int]] = set()
        
        self.logger = logging.getLogger(__name__)
        
    def set_color_palette(self, term):
        """Initialize color palette and batch renderer with terminal instance."""
        super().set_color_palette(term)
        if not self.batch_renderer:
            from ..core.terminal import BlessedTerminal
            terminal_adapter = BlessedTerminal()
            terminal_adapter._term = term
            self.batch_renderer = BatchRenderer(terminal_adapter)
            
    def mark_tile_dirty(self, x: int, y: int) -> None:
        """Mark a tile as needing redraw."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.dirty_tracker.mark_dirty(x, y)
            self.changed_tiles.add((x, y))
            
    def mark_region_dirty(self, x: int, y: int, width: int, height: int) -> None:
        """Mark a rectangular region as needing redraw."""
        self.dirty_tracker.mark_region_dirty(x, y, width, height)
        for dy in range(height):
            for dx in range(width):
                if 0 <= x + dx < self.width and 0 <= y + dy < self.height:
                    self.changed_tiles.add((x + dx, y + dy))
                    
    def draw_static(self, term):
        """Draw static map elements, only redrawing changed tiles."""
        if self.color_palette is None:
            self.set_color_palette(term)
            
        # If this is the first render, draw everything
        if not self.last_rendered_tiles:
            self._draw_all_tiles(term)
            return
            
        # Otherwise, only draw changed tiles
        self._draw_changed_tiles(term)
        
    def _draw_all_tiles(self, term):
        """Draw all tiles (used for initial render)."""
        self.logger.debug("Drawing all tiles (initial render)")
        
        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                color = self._get_tile_color(tile)
                
                # Add to batch
                self.batch_renderer.add_char(
                    x + self.x_offset,
                    y + self.y_offset,
                    tile,
                    color
                )
                
                # Remember what we rendered
                self.last_rendered_tiles[(x, y)] = (tile, color)
                
        # Flush all at once
        self.batch_renderer.flush()
        
    def _draw_changed_tiles(self, term):
        """Draw only tiles that have changed."""
        changes = 0
        
        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                color = self._get_tile_color(tile)
                current = (tile, color)
                
                # Check if this tile changed
                last = self.last_rendered_tiles.get((x, y))
                if current != last or (x, y) in self.changed_tiles:
                    # Add to batch
                    self.batch_renderer.add_char(
                        x + self.x_offset,
                        y + self.y_offset,
                        tile,
                        color
                    )
                    
                    # Update cache
                    self.last_rendered_tiles[(x, y)] = current
                    changes += 1
                    
        # Clear changed tiles set
        self.changed_tiles.clear()
        
        # Only flush if there were changes
        if changes > 0:
            self.logger.debug(f"Redrawing {changes} changed tiles")
            self.batch_renderer.flush()
            
    def _get_tile_color(self, tile: str) -> Color:
        """Get the color for a tile."""
        # Use color palette if available
        if self.color_palette:
            # The color palette already handles tile-to-color mapping
            color_tuple = self.color_palette.get_color_for_char(tile)
            if color_tuple:
                return Color(*color_tuple)
                
        # Default colors as fallback
        default_colors = {
            '#': Color(128, 128, 128),  # Gray wall
            '.': Color(64, 64, 64),     # Dark gray floor
            '+': Color(139, 69, 19),    # Brown door
            '<': Color(255, 255, 0),    # Yellow stairs up
            '>': Color(255, 255, 0),    # Yellow stairs down
            '~': Color(0, 100, 255),    # Blue water
            '%': Color(255, 100, 0),    # Orange lava
            '$': Color(255, 215, 0),    # Gold chest
            '^': Color(255, 255, 255),  # White altar
            # Resources
            't': Color(139, 69, 19),    # Brown wood
            's': Color(128, 128, 128),  # Gray stone
            'o': Color(192, 192, 192),  # Silver ore
            '*': Color(100, 200, 255),  # Light blue crystal/essence
            'm': Color(139, 69, 19),    # Brown mushroom
            'h': Color(0, 255, 0),      # Green herbs
        }
        
        return default_colors.get(tile, Color(192, 192, 192))
        
    def draw_entities(self, term):
        """Draw entities, only redrawing those that moved."""
        if self.color_palette is None:
            self.set_color_palette(term)
            
        # Get current entity positions
        current_positions = {}
        entities = self.entity_manager.get_entities_with_component(Position)
        
        for entity in entities:
            pos = entity.get_component(Position)
            if pos and 0 <= pos.x < self.width and 0 <= pos.y < self.height:
                current_positions[entity.id] = (pos.x, pos.y)
                
        # Clear old positions that changed
        for entity_id, old_pos in self.last_entity_positions.items():
            if entity_id not in current_positions or current_positions[entity_id] != old_pos:
                # Redraw the tile at the old position
                tile = self.tiles[old_pos[1]][old_pos[0]]
                color = self._get_tile_color(tile)
                
                self.batch_renderer.add_char(
                    old_pos[0] + self.x_offset,
                    old_pos[1] + self.y_offset,
                    tile,
                    color
                )
                
        # Draw entities at new positions
        for entity in entities:
            pos = entity.get_component(Position)
            renderable = entity.renderable
            
            if pos and renderable and 0 <= pos.x < self.width and 0 <= pos.y < self.height:
                entity_pos = (pos.x, pos.y)
                
                # Only draw if position changed or entity is new
                if (entity.id not in self.last_entity_positions or 
                    self.last_entity_positions[entity.id] != entity_pos):
                    
                    # Get entity color
                    if hasattr(renderable, 'color'):
                        color = Color(*renderable.color)
                    else:
                        color = Color(255, 255, 255)  # Default white
                        
                    self.batch_renderer.add_char(
                        pos.x + self.x_offset,
                        pos.y + self.y_offset,
                        renderable.char,
                        color
                    )
                    
        # Update position tracking
        self.last_entity_positions = current_positions
        
        # Flush all changes
        self.batch_renderer.flush()
        
    def draw_player(self, term, player):
        """Draw player efficiently."""
        if self.color_palette is None:
            self.set_color_palette(term)
            
        # Player is always white @ symbol
        self.batch_renderer.add_char(
            player.x + self.x_offset,
            player.y + self.y_offset,
            '@',
            Color(255, 255, 255)
        )
        self.batch_renderer.flush()
        
    def clear_player(self, term, player):
        """Clear player position by redrawing the tile underneath."""
        if self.color_palette is None:
            self.set_color_palette(term)
            
        tile = self.tiles[player.y][player.x]
        color = self._get_tile_color(tile)
        
        self.batch_renderer.add_char(
            player.x + self.x_offset,
            player.y + self.y_offset,
            tile,
            color
        )
        self.batch_renderer.flush()
        
    def open_door(self, x: int, y: int) -> bool:
        """Open a door at the given position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.tiles[y][x] == '+':
                self.tiles[y][x] = '.'
                self.mark_tile_dirty(x, y)  # Mark as needing redraw
                return True
        return False
        
    def remove_resource(self, x: int, y: int) -> bool:
        """Remove a resource from the map."""
        if 0 <= x < self.width and 0 <= y < self.height:
            resource_tiles = ['t', 's', 'o', '*', 'm', 'h']
            if self.tiles[y][x] in resource_tiles:
                self.tiles[y][x] = '.'
                self.mark_tile_dirty(x, y)  # Mark as needing redraw
                return True
        return False
        
    def set_tile(self, x: int, y: int, tile: str) -> None:
        """Set a tile and mark it as dirty."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.tiles[y][x] != tile:
                self.tiles[y][x] = tile
                self.mark_tile_dirty(x, y)