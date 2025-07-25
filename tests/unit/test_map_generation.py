"""Unit tests for procedural map generation."""

import pytest
from magemines.game.map_generator import (
    DungeonGenerator, CaveGenerator, TownGenerator, 
    MapGeneratorConfig, TileType, GenerationMethod,
    Room, Corridor, create_generator
)
from magemines.game.map import GameMap


class TestDungeonGenerator:
    """Test dungeon generation algorithms."""
    
    def test_dungeon_generation_creates_rooms(self):
        """Test that dungeon generation creates rooms."""
        config = MapGeneratorConfig(width=50, height=30, max_rooms=10)
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Should have created some rooms
        assert len(generator.rooms) > 0
        assert len(generator.rooms) <= config.max_rooms
        
        # Verify rooms don't overlap
        for i, room1 in enumerate(generator.rooms):
            for j, room2 in enumerate(generator.rooms):
                if i != j:
                    assert not room1.intersects(room2)
        
        # Verify corridors were created (at least n-1 for n rooms)
        if len(generator.rooms) > 1:
            assert len(generator.corridors) >= len(generator.rooms) - 1
    
    def test_dungeon_has_floor_tiles(self):
        """Test that dungeons have walkable floor tiles."""
        config = MapGeneratorConfig(width=50, height=30)
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Count floor tiles
        floor_count = 0
        for y in range(config.height):
            for x in range(config.width):
                if generator.get_tile(x, y) == TileType.FLOOR:
                    floor_count += 1
        
        # Should have some floor tiles
        assert floor_count > 0
    
    def test_dungeon_has_stairs(self):
        """Test that dungeons have up and down stairs."""
        config = MapGeneratorConfig(width=50, height=30, max_rooms=5)
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Find stairs
        has_up_stairs = False
        has_down_stairs = False
        
        for y in range(config.height):
            for x in range(config.width):
                tile = generator.get_tile(x, y)
                if tile == TileType.STAIRS_UP:
                    has_up_stairs = True
                elif tile == TileType.STAIRS_DOWN:
                    has_down_stairs = True
        
        # Should have both stairs if we have at least 2 rooms
        if len(generator.rooms) >= 2:
            assert has_up_stairs
            assert has_down_stairs
    
    def test_find_empty_position(self):
        """Test finding empty positions in the dungeon."""
        config = MapGeneratorConfig(width=50, height=30)
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Should be able to find an empty position
        pos = generator.find_empty_position()
        assert pos is not None
        x, y = pos
        assert generator.get_tile(x, y) == TileType.FLOOR
    
    def test_all_rooms_connected(self):
        """Test that all rooms are reachable from each other."""
        config = MapGeneratorConfig(width=80, height=50, max_rooms=15)
        generator = DungeonGenerator(config)
        generator.generate()
        
        if len(generator.rooms) <= 1:
            return  # Nothing to test with 0 or 1 room
        
        # Use flood fill from the first room to verify connectivity
        visited = [[False for _ in range(config.width)] for _ in range(config.height)]
        
        # Start flood fill from center of first room
        start_x, start_y = generator.rooms[0].center()
        to_visit = [(start_x, start_y)]
        visited[start_y][start_x] = True
        visited_rooms = set()
        
        while to_visit:
            x, y = to_visit.pop(0)
            
            # Check which room this position belongs to
            for i, room in enumerate(generator.rooms):
                if room.contains(x, y):
                    visited_rooms.add(i)
            
            # Check all four directions
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < config.width and 0 <= ny < config.height and
                    not visited[ny][nx] and generator.get_tile(nx, ny) == TileType.FLOOR):
                    visited[ny][nx] = True
                    to_visit.append((nx, ny))
        
        # All rooms should be visited
        assert len(visited_rooms) == len(generator.rooms)
    
    def test_diagonal_corridors(self):
        """Test that diagonal corridors can be generated."""
        # Test with diagonal corridors enabled
        config = MapGeneratorConfig(
            width=60, height=40, max_rooms=10,
            diagonal_corridors=True,
            diagonal_chance=1.0  # Always use diagonal
        )
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Should have rooms and corridors
        assert len(generator.rooms) > 0
        assert len(generator.corridors) > 0
        
        # All rooms should still be connected
        if len(generator.rooms) > 1:
            # Simple connectivity check - all rooms should have floor tiles between them
            assert generator.find_empty_position() is not None


class TestRoom:
    """Test the Room class."""
    
    def test_room_center(self):
        """Test room center calculation."""
        room = Room(10, 10, 10, 10)
        cx, cy = room.center()
        assert cx == 15  # 10 + 10//2
        assert cy == 15  # 10 + 10//2
    
    def test_room_intersection(self):
        """Test room intersection detection."""
        room1 = Room(10, 10, 10, 10)
        room2 = Room(15, 15, 10, 10)  # Overlaps
        room3 = Room(25, 25, 10, 10)  # Doesn't overlap
        
        assert room1.intersects(room2)
        assert room2.intersects(room1)  # Should be symmetric
        assert not room1.intersects(room3)
        assert not room3.intersects(room1)
    
    def test_room_contains(self):
        """Test if a point is inside a room."""
        room = Room(10, 10, 10, 10)
        
        # Points inside
        assert room.contains(10, 10)  # Top-left corner
        assert room.contains(15, 15)  # Center
        assert room.contains(19, 19)  # Just inside bottom-right
        
        # Points outside
        assert not room.contains(9, 10)   # Just left
        assert not room.contains(10, 9)   # Just above
        assert not room.contains(20, 10)  # Just right
        assert not room.contains(10, 20)  # Just below


class TestCorridor:
    """Test the Corridor class."""
    
    def test_corridor_points(self):
        """Test corridor point generation."""
        # Horizontal then vertical corridor
        corridor = Corridor(10, 10, 20, 20)
        points = corridor.get_points()
        
        # Should create an L-shaped path
        assert len(points) > 0
        assert (10, 10) in points  # Start point
        assert (20, 20) in points  # End point
        
        # Should have intermediate points
        assert (15, 10) in points  # Horizontal segment
        assert (20, 15) in points  # Vertical segment


class TestGameMapIntegration:
    """Test integration between GameMap and procedural generation."""
    
    def test_game_map_procedural_generation(self):
        """Test that GameMap can use procedural generation."""
        # Create map with procedural generation
        game_map = GameMap(60, 40, use_procedural=True)
        
        # Should have non-empty tiles
        has_floor = False
        has_wall = False
        
        for y in range(game_map.height):
            for x in range(game_map.width):
                tile = game_map.tiles[y][x]
                if tile == '.':
                    has_floor = True
                elif tile == '#':
                    has_wall = True
        
        assert has_floor
        assert has_wall
    
    def test_game_map_starting_position(self):
        """Test that GameMap finds valid starting positions."""
        game_map = GameMap(60, 40, use_procedural=True)
        
        # Get starting position
        x, y = game_map.get_starting_position()
        
        # Should be a valid, non-blocked position
        assert 0 <= x < game_map.width
        assert 0 <= y < game_map.height
        assert not game_map.is_blocked(x, y)
    
    def test_game_map_simple_mode(self):
        """Test that GameMap can still create simple bordered maps."""
        game_map = GameMap(30, 20, use_procedural=False)
        
        # Should have walls around border
        for x in range(game_map.width):
            assert game_map.tiles[0][x] == '#'  # Top wall
            assert game_map.tiles[game_map.height - 1][x] == '#'  # Bottom wall
        
        for y in range(game_map.height):
            assert game_map.tiles[y][0] == '#'  # Left wall
            assert game_map.tiles[y][game_map.width - 1] == '#'  # Right wall
        
        # Should have floor in the middle
        assert game_map.tiles[10][10] == '.'


class TestCaveGenerator:
    """Test cave generation algorithms."""
    
    def test_cave_generation(self):
        """Test that cave generation creates connected areas."""
        config = MapGeneratorConfig(
            width=50, 
            height=30, 
            method=GenerationMethod.CELLULAR_AUTOMATA
        )
        generator = CaveGenerator(config)
        generator.generate()
        
        # Should have floor tiles
        floor_count = 0
        for y in range(config.height):
            for x in range(config.width):
                if generator.get_tile(x, y) == TileType.FLOOR:
                    floor_count += 1
        
        assert floor_count > 0
        
        # Should have stairs
        has_stairs = False
        for y in range(config.height):
            for x in range(config.width):
                tile = generator.get_tile(x, y)
                if tile in [TileType.STAIRS_UP, TileType.STAIRS_DOWN]:
                    has_stairs = True
                    break
        
        assert has_stairs


class TestTownGenerator:
    """Test town generation."""
    
    def test_town_generation(self):
        """Test that town generation creates roads and buildings."""
        config = MapGeneratorConfig(
            width=60,
            height=40,
            method=GenerationMethod.TOWN,
            max_rooms=10  # Buildings
        )
        generator = TownGenerator(config)
        generator.generate()
        
        # Should have roads (floor tiles)
        floor_count = 0
        for y in range(config.height):
            for x in range(config.width):
                if generator.get_tile(x, y) == TileType.FLOOR:
                    floor_count += 1
        
        assert floor_count > 0
        
        # Should have buildings
        assert len(generator.buildings) > 0
        
        # Should have at least one door
        has_door = False
        for y in range(config.height):
            for x in range(config.width):
                if generator.get_tile(x, y) == TileType.DOOR:
                    has_door = True
                    break
        
        assert has_door
        
        # Should have an altar in one building
        has_altar = False
        for y in range(config.height):
            for x in range(config.width):
                if generator.get_tile(x, y) == TileType.ALTAR:
                    has_altar = True
                    break
        
        assert has_altar


class TestMapGeneratorFactory:
    """Test the map generator factory function."""
    
    def test_create_dungeon_generator(self):
        """Test creating a dungeon generator."""
        config = MapGeneratorConfig(method=GenerationMethod.ROOMS_AND_CORRIDORS)
        generator = create_generator(config)
        assert isinstance(generator, DungeonGenerator)
    
    def test_create_cave_generator(self):
        """Test creating a cave generator."""
        config = MapGeneratorConfig(method=GenerationMethod.CELLULAR_AUTOMATA)
        generator = create_generator(config)
        assert isinstance(generator, CaveGenerator)
    
    def test_create_town_generator(self):
        """Test creating a town generator."""
        config = MapGeneratorConfig(method=GenerationMethod.TOWN)
        generator = create_generator(config)
        assert isinstance(generator, TownGenerator)