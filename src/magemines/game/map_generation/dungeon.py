"""Dungeon generator using rooms and corridors."""

import random
from collections import deque
from typing import List, Optional
from .base import MapGenerator, TileType, MapGeneratorConfig
from .room import Room
from .corridor import Corridor


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
        
        # Place stairs
        self._place_stairs()
    
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
                
    def _place_stairs(self) -> None:
        """Place stairs in the dungeon."""
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