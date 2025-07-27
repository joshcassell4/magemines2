"""Procedural map generation system."""

import random
from collections import deque
from enum import Enum, auto
from typing import List, Tuple, Optional
from dataclasses import dataclass, field


class TileType(Enum):
    """Types of tiles in the game."""
    EMPTY = auto()
    FLOOR = auto()
    WALL = auto()
    DOOR = auto()
    STAIRS_UP = auto()
    STAIRS_DOWN = auto()
    WATER = auto()
    LAVA = auto()
    CHEST = auto()
    ALTAR = auto()


class GenerationMethod(Enum):
    """Map generation algorithms."""
    ROOMS_AND_CORRIDORS = auto()
    CELLULAR_AUTOMATA = auto()
    TOWN = auto()


@dataclass
class Room:
    """Represents a rectangular room."""
    x: int
    y: int
    width: int
    height: int
    
    def center(self) -> Tuple[int, int]:
        """Get the center point of the room."""
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        return cx, cy
    
    def intersects(self, other: 'Room') -> bool:
        """Check if this room intersects with another."""
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)
    
    def contains(self, x: int, y: int) -> bool:
        """Check if a point is inside the room."""
        return (x >= self.x and x < self.x + self.width and
                y >= self.y and y < self.y + self.height)


@dataclass
class Corridor:
    """Represents a corridor between two points."""
    x1: int
    y1: int
    x2: int
    y2: int
    
    def get_points(self) -> List[Tuple[int, int]]:
        """Get all points in the corridor."""
        points = []
        
        # Create an L-shaped corridor
        # We go from (x1,y1) to (x2,y1) then from (x2,y1) to (x2,y2)
        
        # Horizontal segment
        if self.x1 < self.x2:
            for x in range(self.x1, self.x2 + 1):
                points.append((x, self.y1))
        else:
            for x in range(self.x2, self.x1 + 1):
                points.append((x, self.y1))
        
        # Vertical segment (excluding the corner point which is already added)
        if self.y1 < self.y2:
            for y in range(self.y1 + 1, self.y2 + 1):
                points.append((self.x2, y))
        elif self.y1 > self.y2:
            for y in range(self.y2, self.y1):
                points.append((self.x2, y))
        # If y1 == y2, no vertical segment needed
        
        return points


@dataclass
class MapGeneratorConfig:
    """Configuration for map generation."""
    width: int = 80
    height: int = 50
    min_room_size: int = 4
    max_room_size: int = 12
    max_rooms: int = 20
    method: GenerationMethod = GenerationMethod.ROOMS_AND_CORRIDORS
    
    # Cave generation parameters
    initial_density: float = 0.45
    smoothing_iterations: int = 5
    
    # Town generation parameters
    road_width: int = 3
    building_padding: int = 2
    
    # Corridor style parameters
    diagonal_corridors: bool = True  # Enable diagonal corridors
    diagonal_chance: float = 0.5     # Chance of diagonal vs L-shaped corridor
    corridor_width: int = 1          # Width of corridors (1 for thin, 2+ for wider)


class MapGenerator:
    """Base class for map generators."""
    
    def __init__(self, config: MapGeneratorConfig):
        """Initialize the map generator."""
        self.config = config
        self.width = config.width
        self.height = config.height
        self.tiles = [[TileType.EMPTY for _ in range(self.width)] 
                      for _ in range(self.height)]
    
    def clear(self, tile_type: TileType) -> None:
        """Clear the map with a specific tile type."""
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x] = tile_type
    
    def set_tile(self, x: int, y: int, tile_type: TileType) -> None:
        """Set a tile at the given position."""
        if self.in_bounds(x, y):
            self.tiles[y][x] = tile_type
    
    def get_tile(self, x: int, y: int) -> TileType:
        """Get the tile at the given position."""
        if self.in_bounds(x, y):
            return self.tiles[y][x]
        return TileType.EMPTY
    
    def in_bounds(self, x: int, y: int) -> bool:
        """Check if a position is within map bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def generate(self) -> None:
        """Generate the map. Override in subclasses."""
        raise NotImplementedError
    
    def find_empty_position(self) -> Optional[Tuple[int, int]]:
        """Find a random empty floor position."""
        floor_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == TileType.FLOOR:
                    floor_positions.append((x, y))
        
        if floor_positions:
            return random.choice(floor_positions)
        return None


class DungeonGenerator(MapGenerator):
    """Generates dungeons using rooms and corridors."""
    
    def __init__(self, config: MapGeneratorConfig):
        """Initialize the dungeon generator."""
        super().__init__(config)
        self.rooms: List[Room] = []
        self.corridors: List[Corridor] = []
    
    def generate(self) -> None:
        """Generate a dungeon level."""
        self.clear(TileType.WALL)
        self.rooms = []
        self.corridors = []
        
        # Generate rooms
        for _ in range(self.config.max_rooms):
            # Random room size
            w = random.randint(self.config.min_room_size, self.config.max_room_size)
            h = random.randint(self.config.min_room_size, self.config.max_room_size)
            
            # Random position
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            
            new_room = Room(x, y, w, h)
            
            # Check if it intersects with existing rooms
            intersects = False
            for room in self.rooms:
                if new_room.intersects(room):
                    intersects = True
                    break
            
            if not intersects:
                self._carve_room(new_room)
                self.rooms.append(new_room)
        
        # Connect all rooms using a minimum spanning tree approach
        self._connect_rooms()
        
        # Place doors at room entrances if any rooms were marked for doors
        if hasattr(self, '_rooms_with_doors'):
            self._place_room_doors()
        
        # Verify connectivity and fix if needed - run twice for better results
        self._ensure_all_rooms_connected()
        self._ensure_all_rooms_connected()  # Second pass to catch any missed connections
        
        # Place stairs - ensure they're in connected rooms
        if len(self.rooms) >= 2:
            # Find the largest connected component after ensuring connectivity
            visited = [[False for _ in range(self.width)] for _ in range(self.height)]
            largest_component = []
            
            # Find a floor tile to start from
            for room in self.rooms:
                for y in range(room.y + 1, room.y + room.height - 1):
                    for x in range(room.x + 1, room.x + room.width - 1):
                        if self.get_tile(x, y) == TileType.FLOOR and not visited[y][x]:
                            component = []
                            self._flood_fill_rooms(x, y, visited, component)
                            if len(component) > len(largest_component):
                                largest_component = component
            
            # Place stairs in rooms from the largest component
            if len(largest_component) >= 2:
                # Stairs up in first connected room
                room1 = self.rooms[largest_component[0]]
                cx, cy = room1.center()
                # Make sure center is floor
                if self.get_tile(cx, cy) != TileType.FLOOR:
                    # Find a floor tile in the room
                    for y in range(room1.y + 1, room1.y + room1.height - 1):
                        for x in range(room1.x + 1, room1.x + room1.width - 1):
                            if self.get_tile(x, y) == TileType.FLOOR:
                                cx, cy = x, y
                                break
                        if self.get_tile(cx, cy) == TileType.FLOOR:
                            break
                self.set_tile(cx, cy, TileType.STAIRS_UP)
                
                # Stairs down in last connected room
                room2 = self.rooms[largest_component[-1]]
                cx, cy = room2.center()
                # Make sure center is floor
                if self.get_tile(cx, cy) != TileType.FLOOR:
                    # Find a floor tile in the room
                    for y in range(room2.y + 1, room2.y + room2.height - 1):
                        for x in range(room2.x + 1, room2.x + room2.width - 1):
                            if self.get_tile(x, y) == TileType.FLOOR:
                                cx, cy = x, y
                                break
                        if self.get_tile(cx, cy) == TileType.FLOOR:
                            break
                self.set_tile(cx, cy, TileType.STAIRS_DOWN)
            else:
                # Fallback - just use first two rooms
                cx, cy = self.rooms[0].center()
                self.set_tile(cx, cy, TileType.STAIRS_UP)
                cx, cy = self.rooms[-1].center()
                self.set_tile(cx, cy, TileType.STAIRS_DOWN)
    
    def _carve_room(self, room: Room) -> None:
        """Carve out a room."""
        for y in range(room.y + 1, room.y + room.height - 1):
            for x in range(room.x + 1, room.x + room.width - 1):
                self.set_tile(x, y, TileType.FLOOR)
        
        # Optionally add doors to room entrances (20% chance per room)
        if random.random() < 0.2:
            # Mark this room for door placement after corridors are carved
            if not hasattr(self, '_rooms_with_doors'):
                self._rooms_with_doors = []
            self._rooms_with_doors.append(room)
    
    def _carve_corridor(self, corridor: Corridor) -> None:
        """Carve out a corridor."""
        if hasattr(corridor, 'points'):
            # Custom corridor with pre-calculated points
            for x, y in corridor.points:
                self.set_tile(x, y, TileType.FLOOR)
        else:
            # Regular corridor
            for x, y in corridor.get_points():
                self.set_tile(x, y, TileType.FLOOR)
    
    def _carve_simple_corridor(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Carve a simple L-shaped corridor between two points.
        
        This is a more robust implementation that ensures connectivity.
        """
        # Use corridor width from config, default to 1 for normal corridors
        corridor_width = self.config.corridor_width
        
        # Randomly choose whether to go horizontal-first or vertical-first
        if random.random() < 0.5:
            # Horizontal then vertical
            # Go from x1 to x2 along y1
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.set_tile(x, y1, TileType.FLOOR)
                # Make corridor wider if requested
                for dy in range(1, corridor_width):
                    if self.in_bounds(x, y1 + dy):
                        self.set_tile(x, y1 + dy, TileType.FLOOR)
                    if self.in_bounds(x, y1 - dy):
                        self.set_tile(x, y1 - dy, TileType.FLOOR)
            # Go from y1 to y2 along x2
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.set_tile(x2, y, TileType.FLOOR)
                # Make corridor wider if requested
                for dx in range(1, corridor_width):
                    if self.in_bounds(x2 + dx, y):
                        self.set_tile(x2 + dx, y, TileType.FLOOR)
                    if self.in_bounds(x2 - dx, y):
                        self.set_tile(x2 - dx, y, TileType.FLOOR)
        else:
            # Vertical then horizontal
            # Go from y1 to y2 along x1
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.set_tile(x1, y, TileType.FLOOR)
                # Make corridor wider if requested
                for dx in range(1, corridor_width):
                    if self.in_bounds(x1 + dx, y):
                        self.set_tile(x1 + dx, y, TileType.FLOOR)
                    if self.in_bounds(x1 - dx, y):
                        self.set_tile(x1 - dx, y, TileType.FLOOR)
            # Go from x1 to x2 along y2
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.set_tile(x, y2, TileType.FLOOR)
                # Make corridor wider if requested
                for dy in range(1, corridor_width):
                    if self.in_bounds(x, y2 + dy):
                        self.set_tile(x, y2 + dy, TileType.FLOOR)
                    if self.in_bounds(x, y2 - dy):
                        self.set_tile(x, y2 - dy, TileType.FLOOR)
    
    def _carve_diagonal_corridor(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Carve a diagonal corridor between two points.
        
        Uses Bresenham's line algorithm to create a diagonal path.
        """
        # Calculate deltas
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        # Determine direction
        x_step = 1 if x1 < x2 else -1
        y_step = 1 if y1 < y2 else -1
        
        # Bresenham's line algorithm
        x, y = x1, y1
        
        if dx > dy:
            # More horizontal than vertical
            error = dx / 2
            while x != x2:
                self.set_tile(x, y, TileType.FLOOR)
                # Make corridor slightly wider for better connectivity
                if self.in_bounds(x, y - 1):
                    self.set_tile(x, y - 1, TileType.FLOOR)
                if self.in_bounds(x, y + 1):
                    self.set_tile(x, y + 1, TileType.FLOOR)
                
                error -= dy
                if error < 0:
                    y += y_step
                    error += dx
                x += x_step
        else:
            # More vertical than horizontal
            error = dy / 2
            while y != y2:
                self.set_tile(x, y, TileType.FLOOR)
                # Make corridor slightly wider for better connectivity
                if self.in_bounds(x - 1, y):
                    self.set_tile(x - 1, y, TileType.FLOOR)
                if self.in_bounds(x + 1, y):
                    self.set_tile(x + 1, y, TileType.FLOOR)
                
                error -= dx
                if error < 0:
                    x += x_step
                    error += dy
                y += y_step
        
        # Ensure we reach the end point
        self.set_tile(x2, y2, TileType.FLOOR)
    
    def _create_alternate_corridor(self, x1: int, y1: int, x2: int, y2: int):
        """Create a corridor that goes vertical first, then horizontal."""
        # Create a custom corridor object with pre-calculated points
        corridor = Corridor(x1, y1, x2, y2)
        corridor.points = []
        
        # Vertical segment first
        if y1 < y2:
            for y in range(y1, y2 + 1):
                corridor.points.append((x1, y))
        else:
            for y in range(y2, y1 + 1):
                corridor.points.append((x1, y))
        
        # Horizontal segment (excluding corner)
        if x1 < x2:
            for x in range(x1 + 1, x2 + 1):
                corridor.points.append((x, y2))
        elif x1 > x2:
            for x in range(x2, x1):
                corridor.points.append((x, y2))
        
        return corridor
    
    def _connect_rooms(self) -> None:
        """Connect all rooms together ensuring no room is isolated.
        
        Uses a simple algorithm that:
        1. Connects each room to at least one other room
        2. Ensures all rooms are reachable from any other room
        """
        if len(self.rooms) <= 1:
            return
        
        # Keep track of connected rooms
        connected = set()
        unconnected = set(range(len(self.rooms)))
        
        # Start with the first room
        current = 0
        connected.add(current)
        unconnected.remove(current)
        
        # Connect each unconnected room to the nearest connected room
        while unconnected:
            # Find the closest pair of connected/unconnected rooms
            min_dist = float('inf')
            closest_connected = None
            closest_unconnected = None
            
            for conn_idx in connected:
                conn_room = self.rooms[conn_idx]
                conn_cx, conn_cy = conn_room.center()
                
                for unconn_idx in unconnected:
                    unconn_room = self.rooms[unconn_idx]
                    unconn_cx, unconn_cy = unconn_room.center()
                    
                    # Calculate distance
                    dist = abs(conn_cx - unconn_cx) + abs(conn_cy - unconn_cy)
                    
                    if dist < min_dist:
                        min_dist = dist
                        closest_connected = conn_idx
                        closest_unconnected = unconn_idx
            
            # Connect the closest pair
            if closest_connected is not None and closest_unconnected is not None:
                room1 = self.rooms[closest_connected]
                room2 = self.rooms[closest_unconnected]
                
                cx1, cy1 = room1.center()
                cx2, cy2 = room2.center()
                
                # Choose corridor type based on configuration
                if self.config.diagonal_corridors and random.random() < self.config.diagonal_chance:
                    # Use diagonal corridor
                    self._carve_diagonal_corridor(cx1, cy1, cx2, cy2)
                else:
                    # Use L-shaped corridor
                    self._carve_simple_corridor(cx1, cy1, cx2, cy2)
                
                # Still track the corridor for statistics
                corridor = Corridor(cx1, cy1, cx2, cy2)
                self.corridors.append(corridor)
                
                # Mark as connected
                connected.add(closest_unconnected)
                unconnected.remove(closest_unconnected)
        
        # Optionally add some extra connections for more interesting layouts
        # This creates loops and multiple paths
        extra_connections = min(len(self.rooms) // 4, 3)  # Add up to 3 extra connections
        for _ in range(extra_connections):
            if len(self.rooms) < 4:
                break
                
            # Pick two random rooms that aren't already directly connected
            room1_idx = random.randint(0, len(self.rooms) - 1)
            room2_idx = random.randint(0, len(self.rooms) - 1)
            
            if room1_idx != room2_idx:
                room1 = self.rooms[room1_idx]
                room2 = self.rooms[room2_idx]
                
                cx1, cy1 = room1.center()
                cx2, cy2 = room2.center()
                
                # Only add if they're not too close (avoid redundant corridors)
                dist = abs(cx1 - cx2) + abs(cy1 - cy2)
                if dist > 15:  # Minimum distance for extra corridors
                    # Extra corridors are more likely to be diagonal for visual interest
                    if self.config.diagonal_corridors and random.random() < (self.config.diagonal_chance * 1.5):
                        self._carve_diagonal_corridor(cx1, cy1, cx2, cy2)
                    else:
                        self._carve_simple_corridor(cx1, cy1, cx2, cy2)
                    corridor = Corridor(cx1, cy1, cx2, cy2)
                    self.corridors.append(corridor)
    
    def _place_room_doors(self) -> None:
        """Place doors at entrances to rooms marked for doors."""
        for room in self._rooms_with_doors:
            # Find potential door positions (where room walls meet corridors)
            door_positions = []
            
            # Check room perimeter
            for x in range(room.x, room.x + room.width):
                for y in [room.y, room.y + room.height - 1]:  # Top and bottom walls
                    if self._is_valid_door_position(x, y, room):
                        door_positions.append((x, y))
            
            for y in range(room.y, room.y + room.height):
                for x in [room.x, room.x + room.width - 1]:  # Left and right walls
                    if self._is_valid_door_position(x, y, room):
                        door_positions.append((x, y))
            
            # Place 1-2 doors per room
            if door_positions:
                num_doors = min(random.randint(1, 2), len(door_positions))
                selected_positions = random.sample(door_positions, num_doors)
                for x, y in selected_positions:
                    self.set_tile(x, y, TileType.DOOR)
    
    def _is_valid_door_position(self, x: int, y: int, room: Room) -> bool:
        """Check if a position is valid for a door."""
        if not self.in_bounds(x, y):
            return False
        
        # Must be on room edge
        if not (x == room.x or x == room.x + room.width - 1 or 
                y == room.y or y == room.y + room.height - 1):
            return False
        
        # Check if there's a corridor on one side and room floor on the other
        adjacent_floor = 0
        adjacent_wall = 0
        has_room_floor = False
        has_corridor_floor = False
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                tile = self.get_tile(nx, ny)
                if tile == TileType.FLOOR:
                    adjacent_floor += 1
                    # Check if this floor is inside the room or outside (corridor)
                    if room.contains(nx, ny):
                        has_room_floor = True
                    else:
                        has_corridor_floor = True
                elif tile == TileType.WALL:
                    adjacent_wall += 1
        
        # Valid door position must connect room floor to corridor floor
        # and have exactly 2 adjacent floor tiles
        return adjacent_floor == 2 and has_room_floor and has_corridor_floor
    
    def _ensure_all_rooms_connected(self) -> None:
        """Verify all rooms are connected and add corridors if needed."""
        if len(self.rooms) < 2:
            return
        
        # Use flood fill to find connected components
        visited = [[False for _ in range(self.width)] for _ in range(self.height)]
        components = []
        
        for i, room in enumerate(self.rooms):
            # Check if this room has already been visited
            already_visited = False
            for comp in components:
                if i in comp:
                    already_visited = True
                    break
            
            if not already_visited:
                # Find a floor tile in this room to start from
                start_x, start_y = None, None
                for y in range(room.y + 1, room.y + room.height - 1):
                    for x in range(room.x + 1, room.x + room.width - 1):
                        if self.get_tile(x, y) == TileType.FLOOR:
                            start_x, start_y = x, y
                            break
                    if start_x is not None:
                        break
                
                if start_x is not None:
                    # Start a new component
                    component = []
                    self._flood_fill_rooms(start_x, start_y, visited, component)
                    if i not in component:
                        component.append(i)  # Ensure this room is in its component
                    components.append(component)
        
        # If there's more than one component, connect them
        if len(components) > 1:
            # Connect each component to the main component
            main_component = components[0]
            for i in range(1, len(components)):
                # Find closest pair of rooms between components
                min_dist = float('inf')
                best_room1 = None
                best_room2 = None
                
                for room_idx1 in main_component:
                    room1 = self.rooms[room_idx1]
                    cx1, cy1 = room1.center()
                    
                    for room_idx2 in components[i]:
                        room2 = self.rooms[room_idx2]
                        cx2, cy2 = room2.center()
                        
                        dist = abs(cx1 - cx2) + abs(cy1 - cy2)
                        if dist < min_dist:
                            min_dist = dist
                            best_room1 = room1
                            best_room2 = room2
                
                # Connect the closest rooms with a wider corridor
                if best_room1 and best_room2:
                    cx1, cy1 = best_room1.center()
                    cx2, cy2 = best_room2.center()
                    
                    # Use wider corridors for better connectivity
                    old_width = self.config.corridor_width
                    self.config.corridor_width = 2  # Temporarily use wider corridors
                    
                    # Carve corridor twice with slight offset for reliability
                    self._carve_simple_corridor(cx1, cy1, cx2, cy2)
                    # Try alternate path too
                    if abs(cx1 - cx2) > 2 and abs(cy1 - cy2) > 2:
                        self._carve_simple_corridor(cx1 + 1, cy1, cx2, cy2 + 1)
                    
                    self.config.corridor_width = old_width  # Restore original width
                    
                    # Merge this component into main
                    main_component.extend(components[i])
    
    def _flood_fill_rooms(self, start_x: int, start_y: int, visited: list, component: list) -> None:
        """Flood fill to find connected rooms using iterative approach."""
        queue = deque([(start_x, start_y)])
        
        while queue:
            x, y = queue.popleft()
            
            if not self.in_bounds(x, y) or visited[y][x]:
                continue
            
            if self.get_tile(x, y) not in [TileType.FLOOR, TileType.DOOR]:
                continue
            
            visited[y][x] = True
            
            # Find which room contains this position
            for i, room in enumerate(self.rooms):
                if room.contains(x, y):
                    if i not in component:
                        component.append(i)
                    break
            
            # Add adjacent positions to queue
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                queue.append((x + dx, y + dy))


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


class TownGenerator(MapGenerator):
    """Generates town layouts."""
    
    def __init__(self, config: MapGeneratorConfig):
        """Initialize the town generator."""
        super().__init__(config)
        self.buildings: List[Room] = []
    
    def generate(self) -> None:
        """Generate a town."""
        self.clear(TileType.WALL)
        self.buildings = []
        
        # Create main roads
        self._create_roads()
        
        # Place buildings
        self._place_buildings()
        
        # Place special features
        self._place_features()
        
        # Ensure map edges are walls (fix stray floor tiles)
        for x in range(self.width):
            self.set_tile(x, 0, TileType.WALL)
            self.set_tile(x, self.height - 1, TileType.WALL)
        for y in range(self.height):
            self.set_tile(0, y, TileType.WALL)
            self.set_tile(self.width - 1, y, TileType.WALL)
    
    def _create_roads(self) -> None:
        """Create the main roads."""
        # Horizontal main road
        mid_y = self.height // 2
        for y in range(mid_y - self.config.road_width // 2, 
                       mid_y + self.config.road_width // 2 + 1):
            for x in range(self.width):
                if self.in_bounds(x, y):
                    self.set_tile(x, y, TileType.FLOOR)
        
        # Vertical main road
        mid_x = self.width // 2
        for x in range(mid_x - self.config.road_width // 2,
                       mid_x + self.config.road_width // 2 + 1):
            for y in range(self.height):
                if self.in_bounds(x, y):
                    self.set_tile(x, y, TileType.FLOOR)
        
        # Add perimeter road to ensure edge buildings can connect
        # Top and bottom edges
        for x in range(1, self.width - 1):
            self.set_tile(x, 1, TileType.FLOOR)
            self.set_tile(x, self.height - 2, TileType.FLOOR)
        
        # Left and right edges
        for y in range(1, self.height - 1):
            self.set_tile(1, y, TileType.FLOOR)
            self.set_tile(self.width - 2, y, TileType.FLOOR)
    
    def _place_buildings(self) -> None:
        """Place buildings around the roads."""
        attempts = 0
        max_attempts = 100
        
        while len(self.buildings) < self.config.max_rooms and attempts < max_attempts:
            attempts += 1
            
            # Random building size
            w = random.randint(self.config.min_room_size + 2, 
                               self.config.max_room_size + 2)
            h = random.randint(self.config.min_room_size + 2, 
                               self.config.max_room_size + 2)
            
            # Try to place near roads
            x = random.randint(2, self.width - w - 2)
            y = random.randint(2, self.height - h - 2)
            
            building = Room(x, y, w, h)
            
            # Check if it intersects with existing buildings or roads
            valid = True
            for b in self.buildings:
                if building.intersects(b):
                    valid = False
                    break
            
            # Check distance from roads
            if valid:
                near_road = False
                for check_y in range(y - 1, y + h + 1):
                    for check_x in range(x - 1, x + w + 1):
                        if self.in_bounds(check_x, check_y) and \
                           self.get_tile(check_x, check_y) == TileType.FLOOR:
                            near_road = True
                            break
                    if near_road:
                        break
                
                if near_road:
                    self._carve_building(building)
                    self.buildings.append(building)
    
    def _carve_building(self, building: Room) -> None:
        """Carve out a building with walls and a door."""
        # Fill with walls first
        for y in range(building.y, building.y + building.height):
            for x in range(building.x, building.x + building.width):
                self.set_tile(x, y, TileType.WALL)
        
        # Carve interior
        for y in range(building.y + 1, building.y + building.height - 1):
            for x in range(building.x + 1, building.x + building.width - 1):
                self.set_tile(x, y, TileType.FLOOR)
        
        # Place door on a side facing a road
        door_placed = False
        
        # Try each side
        sides = [
            # Top side
            [(x, building.y) for x in range(building.x + 1, building.x + building.width - 1)],
            # Bottom side
            [(x, building.y + building.height - 1) for x in range(building.x + 1, building.x + building.width - 1)],
            # Left side
            [(building.x, y) for y in range(building.y + 1, building.y + building.height - 1)],
            # Right side
            [(building.x + building.width - 1, y) for y in range(building.y + 1, building.y + building.height - 1)]
        ]
        
        random.shuffle(sides)
        
        for side in sides:
            if door_placed:
                break
            
            # Try random positions on this side
            positions = list(side)
            random.shuffle(positions)
            
            for x, y in positions:
                # Determine which direction is "outside" based on which side we're on
                if y == building.y:  # Top side
                    outside_x, outside_y = x, y - 1
                elif y == building.y + building.height - 1:  # Bottom side
                    outside_x, outside_y = x, y + 1
                elif x == building.x:  # Left side
                    outside_x, outside_y = x - 1, y
                else:  # Right side
                    outside_x, outside_y = x + 1, y
                
                # Check if the outside position is a road (floor) and not inside another building
                if (self.in_bounds(outside_x, outside_y) and 
                    self.get_tile(outside_x, outside_y) == TileType.FLOOR and
                    not any(b.contains(outside_x, outside_y) for b in self.buildings)):
                    # Place door
                    self.set_tile(x, y, TileType.DOOR)
                    door_placed = True
                    break
        
        # If no door was placed (building is isolated), create a path to the nearest road
        if not door_placed:
            # Find the closest road tile
            min_dist = float('inf')
            closest_road = None
            
            for road_y in range(self.height):
                for road_x in range(self.width):
                    if (self.get_tile(road_x, road_y) == TileType.FLOOR and
                        not any(b.contains(road_x, road_y) for b in self.buildings)):
                        # Calculate distance to building center
                        cx, cy = building.center()
                        dist = abs(cx - road_x) + abs(cy - road_y)
                        if dist < min_dist:
                            min_dist = dist
                            closest_road = (road_x, road_y)
            
            if closest_road:
                # Place door on the side closest to the road
                cx, cy = building.center()
                road_x, road_y = closest_road
                
                # Determine which side is closest
                if abs(road_x - cx) > abs(road_y - cy):
                    # Road is more to the left/right
                    if road_x < cx:
                        # Door on left side
                        door_x = building.x
                        door_y = building.y + building.height // 2
                    else:
                        # Door on right side
                        door_x = building.x + building.width - 1
                        door_y = building.y + building.height // 2
                else:
                    # Road is more above/below
                    if road_y < cy:
                        # Door on top side
                        door_x = building.x + building.width // 2
                        door_y = building.y
                    else:
                        # Door on bottom side
                        door_x = building.x + building.width // 2
                        door_y = building.y + building.height - 1
                
                # Place the door
                self.set_tile(door_x, door_y, TileType.DOOR)
    
    def _place_features(self) -> None:
        """Place special features in the town."""
        # Place an altar in the center building
        if self.buildings:
            center_building = self.buildings[len(self.buildings) // 2]
            cx, cy = center_building.center()
            self.set_tile(cx, cy, TileType.ALTAR)
        
        # Place stairs in town (different buildings if possible)
        if len(self.buildings) >= 2:
            # Down stairs in first building
            first_building = self.buildings[0]
            cx, cy = first_building.center()
            self.set_tile(cx, cy, TileType.STAIRS_DOWN)
            
            # Up stairs in last building (for returning to surface/exit)
            last_building = self.buildings[-1]
            cx, cy = last_building.center()
            # Don't overwrite the altar
            if self.get_tile(cx, cy) != TileType.ALTAR:
                self.set_tile(cx, cy, TileType.STAIRS_UP)
            else:
                # Find another spot in the building
                for y in range(last_building.y + 1, last_building.y + last_building.height - 1):
                    for x in range(last_building.x + 1, last_building.x + last_building.width - 1):
                        if self.get_tile(x, y) == TileType.FLOOR:
                            self.set_tile(x, y, TileType.STAIRS_UP)
                            return
        elif self.buildings:
            # Only one building, place both stairs but separated
            building = self.buildings[0]
            # Down stairs in upper left corner area
            self.set_tile(building.x + 1, building.y + 1, TileType.STAIRS_DOWN)
            # Up stairs in lower right corner area
            self.set_tile(
                building.x + building.width - 2, 
                building.y + building.height - 2, 
                TileType.STAIRS_UP
            )


def create_generator(config: MapGeneratorConfig) -> MapGenerator:
    """Factory function to create the appropriate generator."""
    if config.method == GenerationMethod.ROOMS_AND_CORRIDORS:
        return DungeonGenerator(config)
    elif config.method == GenerationMethod.CELLULAR_AUTOMATA:
        return CaveGenerator(config)
    elif config.method == GenerationMethod.TOWN:
        return TownGenerator(config)
    else:
        raise ValueError(f"Unknown generation method: {config.method}")