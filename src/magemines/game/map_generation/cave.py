"""Cave generator using cellular automata."""

import random
from collections import deque
from typing import List, Tuple
from .base import MapGenerator, TileType, MapGeneratorConfig


class CaveGenerator(MapGenerator):
    """Generates caves using cellular automata."""
    
    def generate(self) -> None:
        """Generate a cave level."""
        # Initialize with random walls
        self._randomize()
        
        # Apply cellular automata smoothing
        for _ in range(self.config.smoothing_iterations):
            self._smooth()
        
        # Clean up isolated areas
        self._cleanup_isolated_areas()
        
        # Place stairs
        self._place_stairs()
    
    def _randomize(self) -> None:
        """Randomly fill the map."""
        for y in range(self.height):
            for x in range(self.width):
                if x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1:
                    self.set_tile(x, y, TileType.WALL)
                else:
                    if random.random() < self.config.initial_density:
                        self.set_tile(x, y, TileType.WALL)
                    else:
                        self.set_tile(x, y, TileType.FLOOR)
    
    def _smooth(self) -> None:
        """Apply cellular automata smoothing."""
        new_tiles = [[TileType.EMPTY for _ in range(self.width)] 
                     for _ in range(self.height)]
        
        for y in range(self.height):
            for x in range(self.width):
                wall_count = self._count_walls(x, y)
                
                if wall_count >= 5:
                    new_tiles[y][x] = TileType.WALL
                else:
                    new_tiles[y][x] = TileType.FLOOR
        
        self.tiles = new_tiles
    
    def _count_walls(self, cx: int, cy: int) -> int:
        """Count walls in the 8 surrounding tiles."""
        count = 0
        for y in range(cy - 1, cy + 2):
            for x in range(cx - 1, cx + 2):
                if not self.in_bounds(x, y) or self.get_tile(x, y) == TileType.WALL:
                    count += 1
        return count
    
    def _cleanup_isolated_areas(self) -> None:
        """Remove small isolated areas."""
        # Simple flood fill to find connected areas
        visited = [[False for _ in range(self.width)] for _ in range(self.height)]
        areas = []
        
        for y in range(self.height):
            for x in range(self.width):
                if not visited[y][x] and self.get_tile(x, y) == TileType.FLOOR:
                    area = []
                    self._flood_fill(x, y, visited, area)
                    areas.append(area)
        
        # Keep only the largest area
        if areas:
            largest_area = max(areas, key=len)
            
            # Fill in all other areas
            for y in range(self.height):
                for x in range(self.width):
                    if self.get_tile(x, y) == TileType.FLOOR and (x, y) not in largest_area:
                        self.set_tile(x, y, TileType.WALL)
    
    def _flood_fill(self, start_x: int, start_y: int, visited: List[List[bool]], 
                     area: List[Tuple[int, int]]) -> None:
        """Flood fill to find connected areas using iterative approach."""
        queue = deque([(start_x, start_y)])
        
        while queue:
            x, y = queue.popleft()
            
            if not self.in_bounds(x, y) or visited[y][x] or self.get_tile(x, y) != TileType.FLOOR:
                continue
            
            visited[y][x] = True
            area.append((x, y))
            
            # Add all 4 adjacent positions to queue
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                queue.append((x + dx, y + dy))
    
    def _place_stairs(self) -> None:
        """Place stairs in the cave."""
        # Find two distant floor positions
        floor_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.get_tile(x, y) == TileType.FLOOR:
                    floor_positions.append((x, y))
        
        if len(floor_positions) >= 2:
            # Place stairs up
            pos = random.choice(floor_positions)
            self.set_tile(pos[0], pos[1], TileType.STAIRS_UP)
            
            # Place stairs down far from stairs up
            max_dist = 0
            best_pos = None
            for fp in floor_positions:
                dist = abs(fp[0] - pos[0]) + abs(fp[1] - pos[1])
                if dist > max_dist:
                    max_dist = dist
                    best_pos = fp
            
            if best_pos:
                self.set_tile(best_pos[0], best_pos[1], TileType.STAIRS_DOWN)