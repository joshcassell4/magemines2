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