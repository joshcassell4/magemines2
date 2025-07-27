"""Town generator for creating town layouts."""

import random
from typing import List
from .base import MapGenerator, TileType, MapGeneratorConfig
from .room import Room


class TownGenerator(MapGenerator):
    """Generates town layouts."""
    
    def __init__(self, config: MapGeneratorConfig, message_pane=None):
        """Initialize the town generator."""
        super().__init__(config, message_pane)
        self.buildings: List[Room] = []
    
    def generate(self) -> None:
        """Generate a town."""
        self.debug_message("Starting town generation...", "info")
        self.clear(TileType.WALL)
        self.buildings = []
        
        # Create main roads
        self.debug_message("Creating roads...")
        self._create_roads()
        
        # Place buildings
        self.debug_message("Placing buildings...")
        self._place_buildings()
        self.debug_message(f"Placed {len(self.buildings)} buildings")
        
        # Ensure connectivity by adding paths between isolated areas
        self.debug_message("Ensuring connectivity...")
        self._ensure_connectivity()
        
        # Place special features
        self.debug_message("Placing special features...")
        self._place_features()
        
        # Ensure map edges are walls (fix stray floor tiles)
        for x in range(self.width):
            self.set_tile(x, 0, TileType.WALL)
            self.set_tile(x, self.height - 1, TileType.WALL)
        for y in range(self.height):
            self.set_tile(0, y, TileType.WALL)
            self.set_tile(self.width - 1, y, TileType.WALL)
        
        self.debug_message("Town generation complete!", "info")
    
    def _create_roads(self) -> None:
        """Create the main roads with better connectivity."""
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
        
        # Add additional cross roads for better connectivity
        # Horizontal roads at 1/3 and 2/3 height
        for y in [self.height // 3, 2 * self.height // 3]:
            for x in range(1, self.width - 1):
                if self.in_bounds(x, y):
                    self.set_tile(x, y, TileType.FLOOR)
        
        # Vertical roads at 1/3 and 2/3 width
        for x in [self.width // 3, 2 * self.width // 3]:
            for y in range(1, self.height - 1):
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
        """Carve out a building with walls and multiple doors."""
        # Fill with walls first
        for y in range(building.y, building.y + building.height):
            for x in range(building.x, building.x + building.width):
                self.set_tile(x, y, TileType.WALL)
        
        # Carve interior
        for y in range(building.y + 1, building.y + building.height - 1):
            for x in range(building.x + 1, building.x + building.width - 1):
                self.set_tile(x, y, TileType.FLOOR)
        
        # Place 2-3 doors on sides facing roads for better connectivity
        num_doors = random.randint(2, 3)
        doors_placed = 0
        self.debug_message(f"Placing {num_doors} doors for building at ({building.x}, {building.y})")
        
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
        
        # Try to place doors on different sides for better connectivity
        used_sides = []
        
        for side_idx, side in enumerate(sides):
            if doors_placed >= num_doors:
                break
            
            # Try random positions on this side
            positions = list(side)
            random.shuffle(positions)
            
            # Try to place 1-2 doors on this side
            doors_on_this_side = 0
            max_doors_per_side = 2 if len(positions) > 4 else 1
            
            for x, y in positions:
                if doors_placed >= num_doors or doors_on_this_side >= max_doors_per_side:
                    break
                    
                # Skip if too close to another door
                if self._too_close_to_door(x, y, building):
                    continue
                
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
                    doors_placed += 1
                    doors_on_this_side += 1
                    used_sides.append(side_idx)
                    self.debug_message(f"Placed door {doors_placed} at ({x}, {y})")
        
        # If no doors were placed (building is isolated), force at least one door
        if doors_placed == 0:
            self.debug_message(f"Building at ({building.x}, {building.y}) is isolated, forcing door placement", "warning")
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
    
    def _too_close_to_door(self, x: int, y: int, building: Room) -> bool:
        """Check if a position is too close to an existing door."""
        # Check adjacent tiles for doors
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx == 0 and dy == 0:
                    continue
                check_x, check_y = x + dx, y + dy
                if self.in_bounds(check_x, check_y) and self.get_tile(check_x, check_y) == TileType.DOOR:
                    return True
        return False
    
    def _ensure_connectivity(self) -> None:
        """Ensure all buildings and areas are connected."""
        from collections import deque
        
        # Find all floor tiles (roads and building interiors)
        floor_regions = []
        visited = set()
        
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in visited and self.get_tile(x, y) in [TileType.FLOOR, TileType.DOOR]:
                    # Start flood fill from this tile
                    region = []
                    queue = deque([(x, y)])
                    
                    while queue:
                        cx, cy = queue.popleft()
                        if (cx, cy) in visited or not self.in_bounds(cx, cy):
                            continue
                        
                        tile = self.get_tile(cx, cy)
                        if tile not in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN, TileType.ALTAR]:
                            continue
                        
                        visited.add((cx, cy))
                        region.append((cx, cy))
                        
                        # Add neighbors
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            queue.append((cx + dx, cy + dy))
                    
                    if region:
                        floor_regions.append(region)
        
        self.debug_message(f"Found {len(floor_regions)} disconnected regions")
        
        # Connect all regions to the first (main) region
        if len(floor_regions) > 1:
            main_region = floor_regions[0]
            
            for i in range(1, len(floor_regions)):
                region = floor_regions[i]
                self.debug_message(f"Connecting region {i} ({len(region)} tiles) to main region")
                
                # Find closest points between regions
                min_dist = float('inf')
                best_p1 = None
                best_p2 = None
                
                for x1, y1 in main_region[:100]:  # Sample to avoid O(n²) complexity
                    for x2, y2 in region[:100]:
                        dist = abs(x1 - x2) + abs(y1 - y2)
                        if dist < min_dist:
                            min_dist = dist
                            best_p1 = (x1, y1)
                            best_p2 = (x2, y2)
                
                if best_p1 and best_p2:
                    self.debug_message(f"Creating path from {best_p1} to {best_p2}")
                    self._create_path(best_p1[0], best_p1[1], best_p2[0], best_p2[1])
    
    def _create_path(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """Create a path between two points."""
        # Simple L-shaped path
        # Go horizontal first
        if x1 < x2:
            for x in range(x1, x2 + 1):
                if self.get_tile(x, y1) == TileType.WALL:
                    self.set_tile(x, y1, TileType.FLOOR)
        else:
            for x in range(x2, x1 + 1):
                if self.get_tile(x, y1) == TileType.WALL:
                    self.set_tile(x, y1, TileType.FLOOR)
        
        # Then go vertical
        if y1 < y2:
            for y in range(y1, y2 + 1):
                if self.get_tile(x2, y) == TileType.WALL:
                    self.set_tile(x2, y, TileType.FLOOR)
        else:
            for y in range(y2, y1 + 1):
                if self.get_tile(x2, y) == TileType.WALL:
                    self.set_tile(x2, y, TileType.FLOOR)