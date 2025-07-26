"""Test map connectivity to ensure all rooms are reachable."""

import pytest
from collections import deque
from typing import Set, Tuple, List

from magemines.game.map_generator import (
    DungeonGenerator, 
    MapGeneratorConfig, 
    TileType,
    GenerationMethod
)


class TestMapConnectivity:
    """Test suite for verifying map connectivity."""
    
    def flood_fill(self, generator: DungeonGenerator, start_x: int, start_y: int) -> Set[Tuple[int, int]]:
        """Use flood fill to find all reachable floor tiles from a starting position."""
        visited = set()
        queue = deque([(start_x, start_y)])
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) in visited:
                continue
                
            if not generator.in_bounds(x, y):
                continue
                
            tile = generator.get_tile(x, y)
            if tile not in [TileType.FLOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN, TileType.DOOR]:
                continue
                
            visited.add((x, y))
            
            # Check all 4 directions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                queue.append((x + dx, y + dy))
        
        return visited
    
    def get_all_floor_tiles(self, generator: DungeonGenerator) -> Set[Tuple[int, int]]:
        """Get all floor tiles in the map."""
        floor_tiles = set()
        for y in range(generator.height):
            for x in range(generator.width):
                tile = generator.get_tile(x, y)
                if tile in [TileType.FLOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN, TileType.DOOR]:
                    floor_tiles.add((x, y))
        return floor_tiles
    
    def find_disconnected_rooms(self, generator: DungeonGenerator) -> List[int]:
        """Find which rooms are not connected to the main area."""
        if not generator.rooms:
            return []
        
        # Start flood fill from first room center
        start_x, start_y = generator.rooms[0].center()
        reachable = self.flood_fill(generator, start_x, start_y)
        
        # Check which rooms are not reachable
        disconnected = []
        for i, room in enumerate(generator.rooms):
            room_center = room.center()
            # Check if any floor tile in the room is reachable
            room_connected = False
            for y in range(room.y + 1, room.y + room.height - 1):
                for x in range(room.x + 1, room.x + room.width - 1):
                    if (x, y) in reachable:
                        room_connected = True
                        break
                if room_connected:
                    break
            
            if not room_connected:
                disconnected.append(i)
        
        return disconnected
    
    def visualize_map(self, generator: DungeonGenerator, highlight_disconnected: bool = True) -> str:
        """Create a string visualization of the map."""
        if not highlight_disconnected:
            # Simple visualization
            lines = []
            for y in range(generator.height):
                line = ""
                for x in range(generator.width):
                    tile = generator.get_tile(x, y)
                    if tile == TileType.WALL:
                        line += "#"
                    elif tile == TileType.FLOOR:
                        line += "."
                    elif tile == TileType.DOOR:
                        line += "+"
                    elif tile == TileType.STAIRS_UP:
                        line += "<"
                    elif tile == TileType.STAIRS_DOWN:
                        line += ">"
                    else:
                        line += " "
                lines.append(line)
            return "\n".join(lines)
        
        # Highlight disconnected areas
        disconnected_rooms = self.find_disconnected_rooms(generator)
        disconnected_positions = set()
        
        for room_idx in disconnected_rooms:
            room = generator.rooms[room_idx]
            for y in range(room.y, room.y + room.height):
                for x in range(room.x, room.x + room.width):
                    disconnected_positions.add((x, y))
        
        lines = []
        for y in range(generator.height):
            line = ""
            for x in range(generator.width):
                tile = generator.get_tile(x, y)
                if (x, y) in disconnected_positions and tile == TileType.FLOOR:
                    line += "X"  # Mark disconnected floor tiles
                elif tile == TileType.WALL:
                    line += "#"
                elif tile == TileType.FLOOR:
                    line += "."
                elif tile == TileType.DOOR:
                    line += "+"
                elif tile == TileType.STAIRS_UP:
                    line += "<"
                elif tile == TileType.STAIRS_DOWN:
                    line += ">"
                else:
                    line += " "
            lines.append(line)
        return "\n".join(lines)
    
    def test_basic_connectivity(self):
        """Test that all rooms in a basic dungeon are connected."""
        config = MapGeneratorConfig(
            width=50,
            height=50,
            min_room_size=4,
            max_room_size=8,
            max_rooms=5
        )
        
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Check if any rooms are disconnected
        disconnected = self.find_disconnected_rooms(generator)
        
        if disconnected:
            print("\nDisconnected rooms found!")
            print(f"Room indices: {disconnected}")
            print("\nMap visualization (X = disconnected areas):")
            print(self.visualize_map(generator, highlight_disconnected=True))
            
        assert len(disconnected) == 0, f"Found {len(disconnected)} disconnected rooms"
    
    def test_many_rooms_connectivity(self):
        """Test connectivity with many rooms."""
        config = MapGeneratorConfig(
            width=80,
            height=50,
            min_room_size=3,
            max_room_size=6,
            max_rooms=20
        )
        
        generator = DungeonGenerator(config)
        generator.generate()
        
        disconnected = self.find_disconnected_rooms(generator)
        
        if disconnected:
            print(f"\nDisconnected rooms in large map: {disconnected}")
            print(f"Total rooms: {len(generator.rooms)}")
            
        assert len(disconnected) == 0, f"Found {len(disconnected)} disconnected rooms out of {len(generator.rooms)}"
    
    def test_all_floor_tiles_reachable(self):
        """Test that all floor tiles are reachable from the starting position."""
        config = MapGeneratorConfig(
            width=50,
            height=50,
            min_room_size=4,
            max_room_size=8,
            max_rooms=10
        )
        
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Get all floor tiles
        all_floor = self.get_all_floor_tiles(generator)
        
        if not all_floor:
            pytest.skip("No floor tiles generated")
        
        # Pick any floor tile as start
        start_x, start_y = next(iter(all_floor))
        
        # Find all reachable tiles
        reachable = self.flood_fill(generator, start_x, start_y)
        
        # Check if all floor tiles are reachable
        unreachable = all_floor - reachable
        
        if unreachable:
            print(f"\nUnreachable floor tiles: {len(unreachable)} out of {len(all_floor)}")
            print("\nMap visualization:")
            print(self.visualize_map(generator))
            
        assert len(unreachable) == 0, f"Found {len(unreachable)} unreachable floor tiles"
    
    def test_multiple_generation_seeds(self):
        """Test connectivity across multiple random seeds."""
        config = MapGeneratorConfig(
            width=60,
            height=40,
            min_room_size=4,
            max_room_size=8,
            max_rooms=12
        )
        
        failed_seeds = []
        
        # Test with multiple seeds
        import random
        for seed in range(20):  # Test 20 different seeds
            random.seed(seed)
            generator = DungeonGenerator(config)
            generator.generate()
            
            disconnected = self.find_disconnected_rooms(generator)
            if disconnected:
                failed_seeds.append((seed, len(disconnected), len(generator.rooms)))
        
        if failed_seeds:
            print("\nFailed seeds:")
            for seed, disc_count, total_rooms in failed_seeds:
                print(f"  Seed {seed}: {disc_count}/{total_rooms} rooms disconnected")
        
        assert len(failed_seeds) == 0, f"Connectivity failed for {len(failed_seeds)} out of 20 seeds"
    
    def test_corridor_actually_connects(self):
        """Test that corridors actually create walkable paths between rooms."""
        config = MapGeneratorConfig(
            width=40,
            height=40,
            min_room_size=4,
            max_room_size=6,
            max_rooms=4
        )
        
        generator = DungeonGenerator(config)
        generator.generate()
        
        if len(generator.rooms) < 2:
            pytest.skip("Not enough rooms generated")
        
        # For each pair of adjacent rooms in the connection order
        # verify there's a path between them
        for i in range(len(generator.rooms) - 1):
            room1 = generator.rooms[i]
            room2 = generator.rooms[i + 1]
            
            # Flood fill from room1
            cx1, cy1 = room1.center()
            reachable = self.flood_fill(generator, cx1, cy1)
            
            # Check if room2 is reachable
            cx2, cy2 = room2.center()
            room2_reachable = any(
                (x, y) in reachable 
                for y in range(room2.y + 1, room2.y + room2.height - 1)
                for x in range(room2.x + 1, room2.x + room2.width - 1)
            )
            
            assert room2_reachable, f"Room {i+1} not reachable from room {i}"
    
    def test_single_room_map(self):
        """Test edge case of map with single room."""
        config = MapGeneratorConfig(
            width=30,
            height=30,
            min_room_size=5,
            max_room_size=10,
            max_rooms=1
        )
        
        generator = DungeonGenerator(config)
        generator.generate()
        
        assert len(generator.rooms) >= 1
        
        # Should have no disconnected rooms
        disconnected = self.find_disconnected_rooms(generator)
        assert len(disconnected) == 0
    
    def test_game_actual_configuration(self):
        """Test with the actual configuration used in the game."""
        # Match the configuration from map.py
        config = MapGeneratorConfig(
            width=80,
            height=40,  # Typical game height
            min_room_size=4,
            max_room_size=10,
            max_rooms=15  # As used in map.py
        )
        
        failed_attempts = []
        
        # Test multiple times since it's random
        for attempt in range(10):
            generator = DungeonGenerator(config)
            generator.generate()
            
            disconnected = self.find_disconnected_rooms(generator)
            if disconnected:
                failed_attempts.append({
                    'attempt': attempt,
                    'disconnected': disconnected,
                    'total_rooms': len(generator.rooms),
                    'map': self.visualize_map(generator, highlight_disconnected=True)
                })
        
        if failed_attempts:
            print(f"\nFailed {len(failed_attempts)} out of 10 attempts")
            for fail in failed_attempts:
                print(f"\nAttempt {fail['attempt']}: {len(fail['disconnected'])}/{fail['total_rooms']} disconnected")
                print("Map:")
                print(fail['map'])
        
        assert len(failed_attempts) == 0
    
    def test_connectivity_without_doors(self):
        """Test connectivity ignoring doors (since closed doors block movement)."""
        config = MapGeneratorConfig(
            width=60,
            height=40,
            min_room_size=4,
            max_room_size=8,
            max_rooms=10
        )
        
        generator = DungeonGenerator(config)
        generator.generate()
        
        # First check WITH doors blocking
        disconnected_with_doors = self.find_disconnected_rooms(generator)
        
        # Now temporarily convert all doors to floors and recheck
        door_positions = []
        for y in range(generator.height):
            for x in range(generator.width):
                if generator.get_tile(x, y) == TileType.DOOR:
                    door_positions.append((x, y))
                    generator.set_tile(x, y, TileType.FLOOR)
        
        disconnected_without_doors = self.find_disconnected_rooms(generator)
        
        # Restore doors
        for x, y in door_positions:
            generator.set_tile(x, y, TileType.DOOR)
        
        print(f"\nDoors found: {len(door_positions)}")
        print(f"Disconnected with doors: {len(disconnected_with_doors)}")
        print(f"Disconnected without doors: {len(disconnected_without_doors)}")
        
        if disconnected_with_doors and not disconnected_without_doors:
            print("\nDoors are blocking connectivity!")
            print("Map with blocked areas marked:")
            print(self.visualize_map(generator, highlight_disconnected=True))
        
        # The map should be connected even without opening doors
        assert len(disconnected_without_doors) == 0, "Map has truly disconnected rooms"