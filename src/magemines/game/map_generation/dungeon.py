"""Dungeon generator using rooms and corridors."""

import random
from collections import deque
from typing import List, Optional
from .base import MapGenerator, TileType, MapGeneratorConfig
from .room import Room
from .corridor import Corridor


class DungeonGenerator(MapGenerator):
    """Generates dungeons using rooms and corridors."""
    
    def __init__(self, config: MapGeneratorConfig, message_pane=None):
        """Initialize the dungeon generator."""
        super().__init__(config, message_pane)
        self.rooms: List[Room] = []
        self.corridors: List[Corridor] = []
    
    def generate(self) -> None:
        """Generate a dungeon level."""
        # Limit regeneration attempts to prevent infinite recursion
        max_attempts = 10
        attempt = 0
        
        self.debug_message("Starting dungeon generation...", "info")
        
        while attempt < max_attempts:
            attempt += 1
            
            if attempt > 1:
                self.debug_message(f"Generation attempt {attempt}/{max_attempts}", "warning")
            
            # Clear the map
            self.clear(TileType.WALL)
            self.rooms = []
            self.corridors = []
            
            # Clear door markers
            if hasattr(self, '_rooms_with_doors'):
                delattr(self, '_rooms_with_doors')
            
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
            
            self.debug_message(f"Generated {len(self.rooms)} rooms")
            
            # Need at least 2 rooms for a valid dungeon
            if len(self.rooms) < 2:
                self.debug_message("Not enough rooms generated, retrying...", "warning")
                continue
            
            # Connect all rooms using a more robust approach
            self.debug_message("Connecting rooms...")
            self._connect_all_rooms()
            
            # Final validation to ensure connectivity BEFORE placing doors
            self.debug_message("Validating connectivity...")
            if self._validate_connectivity():
                # Success! Now we can place doors and stairs
                self.debug_message("Connectivity validated!", "info")
                
                # Place doors at room entrances if any rooms were marked for doors
                if hasattr(self, '_rooms_with_doors'):
                    self.debug_message(f"Placing doors in {len(self._rooms_with_doors)} rooms")
                    self._place_room_doors()
                
                # Place stairs
                self.debug_message("Placing stairs...", "info")
                self._place_stairs()
                self.debug_message("Dungeon generation complete!", "info")
                return
            
            # If we get here, validation failed, try again
            self.debug_message(f"Connectivity validation failed on attempt {attempt}", "error")
            print(f"Connectivity validation failed on attempt {attempt}, regenerating...")
        
        # If we've exhausted all attempts, create a simple fallback dungeon
        self.debug_message(f"Failed after {max_attempts} attempts, using fallback", "error")
        print(f"Failed to generate connected dungeon after {max_attempts} attempts, using fallback")
        self._generate_simple_dungeon()
    
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
        
        # Ensure the starting and ending points are floor
        self.set_tile(x1, y1, TileType.FLOOR)
        self.set_tile(x2, y2, TileType.FLOOR)
        
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
    
    def _connect_all_rooms(self) -> None:
        """Connect all rooms together using a robust algorithm that guarantees connectivity."""
        if len(self.rooms) <= 1:
            return
        
        self.debug_message(f"Connecting {len(self.rooms)} rooms...")
        
        # First, ensure basic connectivity using minimum spanning tree
        self._connect_rooms_mst()
        
        # Then add some extra connections for more interesting layouts
        self._add_extra_connections()
        
        # Finally, verify and fix any remaining connectivity issues
        self._ensure_full_connectivity()
        
        self.debug_message("Room connection complete")
    
    def _connect_rooms_mst(self) -> None:
        """Connect rooms using a minimum spanning tree approach."""
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
                
                # Carve corridor with extra reliability
                self._carve_reliable_corridor(room1, room2)
                
                # Mark as connected
                connected.add(closest_unconnected)
                unconnected.remove(closest_unconnected)
    
    def _add_extra_connections(self) -> None:
        """Add extra connections between rooms for more interesting layouts."""
        extra_connections = min(len(self.rooms) // 4, 3)  # Add up to 3 extra connections
        
        for _ in range(extra_connections):
            if len(self.rooms) < 4:
                break
                
            # Pick two random rooms
            room1_idx = random.randint(0, len(self.rooms) - 1)
            room2_idx = random.randint(0, len(self.rooms) - 1)
            
            if room1_idx != room2_idx:
                room1 = self.rooms[room1_idx]
                room2 = self.rooms[room2_idx]
                
                cx1, cy1 = room1.center()
                cx2, cy2 = room2.center()
                
                # Only add if they're not too close
                dist = abs(cx1 - cx2) + abs(cy1 - cy2)
                if dist > 15:
                    self._carve_reliable_corridor(room1, room2)
    
    def _carve_reliable_corridor(self, room1: Room, room2: Room) -> None:
        """Carve a corridor between two rooms with extra reliability."""
        cx1, cy1 = room1.center()
        cx2, cy2 = room2.center()
        
        self.debug_message(f"Carving corridor from room at ({cx1},{cy1}) to room at ({cx2},{cy2})")
        
        # Use wider corridors to ensure connectivity
        old_width = self.config.corridor_width
        self.config.corridor_width = 3  # Even wider for guaranteed connectivity
        
        # Simple but reliable: just connect the centers with a thick corridor
        if self.config.diagonal_corridors and random.random() < self.config.diagonal_chance:
            self._carve_diagonal_corridor(cx1, cy1, cx2, cy2)
        else:
            self._carve_simple_corridor(cx1, cy1, cx2, cy2)
        
        # Also ensure the centers themselves are floor (in case of very small rooms)
        self.set_tile(cx1, cy1, TileType.FLOOR)
        self.set_tile(cx2, cy2, TileType.FLOOR)
        
        self.config.corridor_width = old_width
        
        # Track the corridor
        corridor = Corridor(cx1, cy1, cx2, cy2)
        self.corridors.append(corridor)
    
    def _ensure_full_connectivity(self) -> None:
        """Ensure all rooms are fully connected by checking with flood fill."""
        # Find all connected components
        components = self._find_connected_components()
        
        if len(components) <= 1:
            self.debug_message("All rooms already connected")
            return
            
        self.debug_message(f"Found {len(components)} disconnected components, connecting them...")
        
        # If there's more than one component, connect them
        attempts = 0
        max_attempts = 10
        while len(components) > 1 and attempts < max_attempts:
            attempts += 1
            self.debug_message(f"Connection attempt {attempts}: {len(components)} components remain")
            
            # Connect the first two components
            comp1 = components[0]
            comp2 = components[1]
            
            # Find closest rooms between components
            min_dist = float('inf')
            best_room1_idx = None
            best_room2_idx = None
            
            for room1_idx in comp1:
                room1 = self.rooms[room1_idx]
                cx1, cy1 = room1.center()
                
                for room2_idx in comp2:
                    room2 = self.rooms[room2_idx]
                    cx2, cy2 = room2.center()
                    
                    dist = abs(cx1 - cx2) + abs(cy1 - cy2)
                    if dist < min_dist:
                        min_dist = dist
                        best_room1_idx = room1_idx
                        best_room2_idx = room2_idx
            
            # Connect the closest rooms
            if best_room1_idx is not None and best_room2_idx is not None:
                self.debug_message(f"Connecting component {0} to component {1}")
                
                # Use even wider corridors for forced connections
                old_width = self.config.corridor_width
                self.config.corridor_width = 5  # Very wide to ensure connectivity
                
                # Carve multiple paths to ensure connectivity
                room1 = self.rooms[best_room1_idx]
                room2 = self.rooms[best_room2_idx]
                cx1, cy1 = room1.center()
                cx2, cy2 = room2.center()
                
                # Carve primary corridor
                self._carve_simple_corridor(cx1, cy1, cx2, cy2)
                
                # Also carve a backup corridor with different routing
                # Use edges of rooms for more connection points
                edge1_x = room1.x + 1 if cx1 > cx2 else room1.x + room1.width - 2
                edge1_y = room1.y + room1.height // 2
                edge2_x = room2.x + room2.width - 2 if cx1 > cx2 else room2.x + 1
                edge2_y = room2.y + room2.height // 2
                
                self._carve_simple_corridor(edge1_x, edge1_y, edge2_x, edge2_y)
                
                self.config.corridor_width = old_width
                
                # If still not connected after double corridor, force direct connection
                components_after = self._find_connected_components()
                if len(components_after) >= len(components):
                    self.debug_message("Double corridor failed, forcing aggressive connection", "warning")
                    self._force_direct_connection(room1, room2)
            else:
                self.debug_message("ERROR: Could not find rooms to connect!", "error")
                break
            
            # Recalculate components
            components = self._find_connected_components()
        
        if len(components) > 1:
            self.debug_message(f"WARNING: Still have {len(components)} disconnected components after {attempts} attempts", "warning")
    
    def _force_direct_connection(self, room1: Room, room2: Room) -> None:
        """Force a direct connection between two rooms by carving a thick path."""
        self.debug_message("Forcing direct connection between rooms", "warning")
        
        cx1, cy1 = room1.center()
        cx2, cy2 = room2.center()
        
        # Carve an extremely wide path to guarantee connectivity
        # This is a last resort, so we don't care about aesthetics
        old_width = self.config.corridor_width
        self.config.corridor_width = 7  # Very wide corridor
        
        # First, carve from center to center
        self._carve_simple_corridor(cx1, cy1, cx2, cy2)
        
        # Also carve from multiple points in each room to ensure connectivity
        # Use corners of the rooms
        corners1 = [
            (room1.x + 1, room1.y + 1),
            (room1.x + room1.width - 2, room1.y + 1),
            (room1.x + 1, room1.y + room1.height - 2),
            (room1.x + room1.width - 2, room1.y + room1.height - 2)
        ]
        
        corners2 = [
            (room2.x + 1, room2.y + 1),
            (room2.x + room2.width - 2, room2.y + 1),
            (room2.x + 1, room2.y + room2.height - 2),
            (room2.x + room2.width - 2, room2.y + room2.height - 2)
        ]
        
        # Find closest corners
        best_dist = float('inf')
        best_c1 = corners1[0]
        best_c2 = corners2[0]
        
        for c1 in corners1:
            for c2 in corners2:
                dist = abs(c1[0] - c2[0]) + abs(c1[1] - c2[1])
                if dist < best_dist:
                    best_dist = dist
                    best_c1 = c1
                    best_c2 = c2
        
        # Carve corridor between closest corners
        self._carve_simple_corridor(best_c1[0], best_c1[1], best_c2[0], best_c2[1])
        
        # Also directly carve a straight line of floor tiles as absolute fallback
        # This ignores corridor functions and just ensures connectivity
        dx = 1 if cx2 > cx1 else -1 if cx2 < cx1 else 0
        dy = 1 if cy2 > cy1 else -1 if cy2 < cy1 else 0
        
        x, y = cx1, cy1
        while x != cx2 or y != cy2:
            # Carve a 3x3 area around current position
            for dy2 in range(-3, 4):
                for dx2 in range(-3, 4):
                    if self.in_bounds(x + dx2, y + dy2):
                        self.set_tile(x + dx2, y + dy2, TileType.FLOOR)
            
            # Move towards target
            if x != cx2:
                x += dx
            if y != cy2:
                y += dy
        
        # Ensure the destination is also carved out
        for dy2 in range(-3, 4):
            for dx2 in range(-3, 4):
                if self.in_bounds(cx2 + dx2, cy2 + dy2):
                    self.set_tile(cx2 + dx2, cy2 + dy2, TileType.FLOOR)
        
        self.config.corridor_width = old_width
    
    def _find_connected_components(self) -> List[List[int]]:
        """Find all connected components of rooms."""
        visited_rooms = set()
        components = []
        
        for i, room in enumerate(self.rooms):
            if i not in visited_rooms:
                # Start a new component
                component = []
                self._find_component_rooms(i, visited_rooms, component)
                if component:
                    components.append(component)
        
        return components
    
    def _find_component_rooms(self, room_idx: int, visited: set, component: list) -> None:
        """Find all rooms connected to the given room using flood fill."""
        if room_idx in visited:
            return
        
        visited.add(room_idx)
        component.append(room_idx)
        
        room = self.rooms[room_idx]
        cx, cy = room.center()
        
        # Check if this room is connected to other rooms via floor tiles
        visited_tiles = set()
        reachable_rooms = set()
        self._flood_fill_from_room(cx, cy, visited_tiles, reachable_rooms)
        
        # Recursively visit connected rooms
        for other_idx in reachable_rooms:
            if other_idx != room_idx and other_idx not in visited:
                self._find_component_rooms(other_idx, visited, component)
    
    def _flood_fill_from_room(self, start_x: int, start_y: int, visited_tiles: set, reachable_rooms: set) -> None:
        """Flood fill from a starting position to find reachable rooms."""
        queue = deque([(start_x, start_y)])
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited_tiles or not self.in_bounds(x, y):
                continue
            
            if self.get_tile(x, y) not in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN]:
                continue
            
            visited_tiles.add((x, y))
            
            # Check which room this tile belongs to
            # Only check floor tiles that are actually inside the room's floor area
            for i, room in enumerate(self.rooms):
                # Check if this is a floor tile inside the room's actual floor area (not walls)
                if (x > room.x and x < room.x + room.width - 1 and
                    y > room.y and y < room.y + room.height - 1):
                    reachable_rooms.add(i)
            
            # Add adjacent tiles (only if not already visited)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_pos = (x + dx, y + dy)
                if next_pos not in visited_tiles:
                    queue.append(next_pos)
    
    def _validate_connectivity(self) -> bool:
        """Validate that all rooms are connected."""
        if len(self.rooms) <= 1:
            return True
        
        # First check using the component method
        components = self._find_connected_components()
        
        # Debug: log component information
        if len(components) > 1:
            self.debug_message(f"Found {len(components)} disconnected components!", "error")
            for i, comp in enumerate(components):
                self.debug_message(f"  Component {i}: {len(comp)} rooms", "error")
                # Show which rooms are in this component
                room_info = []
                for room_idx in comp[:3]:  # Show first 3 rooms
                    if room_idx < len(self.rooms):
                        room = self.rooms[room_idx]
                        cx, cy = room.center()
                        room_info.append(f"Room at ({cx},{cy})")
                if len(comp) > 3:
                    room_info.append(f"... and {len(comp)-3} more")
                self.debug_message(f"    {', '.join(room_info)}", "error")
            print(f"WARNING: Found {len(components)} disconnected components!")
            for i, comp in enumerate(components):
                print(f"  Component {i}: {len(comp)} rooms")
                
            # Double-check with a simpler global flood fill
            # This helps catch edge cases where our room detection might be off
            reachable_count = self._count_reachable_rooms_global()
            self.debug_message(f"Global flood fill found {reachable_count}/{len(self.rooms)} reachable rooms")
            
            if reachable_count == len(self.rooms):
                self.debug_message("Global flood fill shows all rooms connected! Component detection may have issues.", "warning")
                return True
        else:
            self.debug_message(f"All {len(self.rooms)} rooms are connected!")
        
        return len(components) == 1
    
    def _count_reachable_rooms_global(self) -> int:
        """Count how many rooms are reachable from the first room using a global flood fill."""
        if not self.rooms:
            return 0
            
        # Start from the center of the first room
        start_room = self.rooms[0]
        start_x, start_y = start_room.center()
        
        visited = set()
        reachable_rooms = set()
        queue = deque([(start_x, start_y)])
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited or not self.in_bounds(x, y):
                continue
                
            tile = self.get_tile(x, y)
            if tile not in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN]:
                continue
                
            visited.add((x, y))
            
            # Check which room(s) this tile belongs to
            for i, room in enumerate(self.rooms):
                # Check if inside room's floor area
                if (x > room.x and x < room.x + room.width - 1 and
                    y > room.y and y < room.y + room.height - 1):
                    reachable_rooms.add(i)
            
            # Add neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_pos = (x + dx, y + dy)
                if next_pos not in visited:
                    queue.append(next_pos)
        
        return len(reachable_rooms)
    
    def _place_room_doors(self) -> None:
        """Place doors at entrances to rooms marked for doors."""
        for room in self._rooms_with_doors:
            # Find all corridor entry points to this room
            entry_points = []
            
            # Check room perimeter for corridor connections
            for x in range(room.x, room.x + room.width):
                for y in [room.y, room.y + room.height - 1]:  # Top and bottom walls
                    if self._is_corridor_entry(x, y, room):
                        entry_points.append((x, y))
            
            for y in range(room.y, room.y + room.height):
                for x in [room.x, room.x + room.width - 1]:  # Left and right walls
                    if self._is_corridor_entry(x, y, room):
                        entry_points.append((x, y))
            
            # Only place doors if room has multiple connections
            # AND never block the only entrance to a room
            if len(entry_points) >= 2:
                # Find valid door positions from entry points
                door_positions = []
                for x, y in entry_points:
                    if self._is_valid_door_position(x, y, room):
                        door_positions.append((x, y))
                
                if door_positions and len(door_positions) >= 2:
                    # Place 1-2 doors, but always leave at least one entrance open
                    # Never place doors on ALL entrances
                    max_doors = min(2, len(door_positions) - 1)  # Always leave one entrance open
                    if max_doors > 0:
                        num_doors = random.randint(1, max_doors)
                        selected_positions = random.sample(door_positions, num_doors)
                        for x, y in selected_positions:
                            self.set_tile(x, y, TileType.DOOR)
                            self.debug_message(f"Placed door at ({x}, {y}) for room at ({room.x}, {room.y})")
    
    def _is_corridor_entry(self, x: int, y: int, room: Room) -> bool:
        """Check if a position is where a corridor enters the room."""
        if not self.in_bounds(x, y):
            return False
        
        # Must be on room edge
        if not (x == room.x or x == room.x + room.width - 1 or 
                y == room.y or y == room.y + room.height - 1):
            return False
        
        # Check if there's floor on both sides (corridor outside, room inside)
        has_room_floor = False
        has_corridor_floor = False
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                tile = self.get_tile(nx, ny)
                if tile == TileType.FLOOR:
                    # Check if inside room's floor area (not walls)
                    if (nx > room.x and nx < room.x + room.width - 1 and
                        ny > room.y and ny < room.y + room.height - 1):
                        has_room_floor = True
                    else:
                        has_corridor_floor = True
        
        return has_room_floor and has_corridor_floor
    
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
                    # Check if this floor is inside the room's floor area (not walls)
                    if (nx > room.x and nx < room.x + room.width - 1 and
                        ny > room.y and ny < room.y + room.height - 1):
                        has_room_floor = True
                    else:
                        has_corridor_floor = True
                elif tile == TileType.WALL:
                    adjacent_wall += 1
        
        # Valid door position must connect room floor to corridor floor
        # and have exactly 2 adjacent floor tiles
        return adjacent_floor == 2 and has_room_floor and has_corridor_floor
    
                
    def _place_stairs(self) -> None:
        """Place stairs in the dungeon."""
        if len(self.rooms) < 2:
            return
            
        # Find the main connected component
        components = self._find_connected_components()
        if not components:
            return
            
        # Use the largest component (should be the only one after validation)
        largest_component = max(components, key=len)
        
        if len(largest_component) < 2:
            # Not enough connected rooms for stairs
            return
            
        # Place stairs in rooms from the connected component
        # Use first and last rooms in the component for maximum distance
        room1_idx = largest_component[0]
        room2_idx = largest_component[-1]
        
        room1 = self.rooms[room1_idx]
        room2 = self.rooms[room2_idx]
        
        # Place stairs up in first room
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
        
        # Place stairs down in last room
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
    
    def _generate_simple_dungeon(self) -> None:
        """Generate a simple but guaranteed connected dungeon as a fallback."""
        self.debug_message("Generating simple fallback dungeon...", "warning")
        self.clear(TileType.WALL)
        self.rooms = []
        
        # Create a simple 3x3 grid of rooms with guaranteed connections
        room_size = 6
        spacing = 10
        
        for row in range(3):
            for col in range(3):
                x = 5 + col * (room_size + spacing)
                y = 5 + row * (room_size + spacing)
                
                # Make sure room fits on map
                if x + room_size >= self.width - 1 or y + room_size >= self.height - 1:
                    continue
                
                room = Room(x, y, room_size, room_size)
                self._carve_room(room)
                self.rooms.append(room)
                
                # Connect to previous room in row
                if col > 0 and len(self.rooms) > 1:
                    prev_room = self.rooms[-2]
                    cx1, cy1 = prev_room.center()
                    cx2, cy2 = room.center()
                    self._carve_simple_corridor(cx1, cy1, cx2, cy2)
                
                # Connect to room above
                if row > 0 and col < len(self.rooms) - 3:
                    above_idx = len(self.rooms) - 4
                    if above_idx >= 0:
                        above_room = self.rooms[above_idx]
                        cx1, cy1 = above_room.center()
                        cx2, cy2 = room.center()
                        self._carve_simple_corridor(cx1, cy1, cx2, cy2)
        
        self.debug_message(f"Simple dungeon created with {len(self.rooms)} rooms", "info")
        
        # Place stairs in first and last rooms
        if len(self.rooms) >= 2:
            self._place_stairs()
            self.debug_message("Simple dungeon generation complete!", "info")