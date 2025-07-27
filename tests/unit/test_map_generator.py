"""Tests for procedural map generation."""

import pytest
from unittest.mock import Mock, MagicMock

from magemines.game.map_generation import (
    MapGenerator, Room, Corridor, TileType,
    MapGeneratorConfig, GenerationMethod,
    DungeonGenerator, CaveGenerator, TownGenerator
)


class TestTileType:
    """Test tile type enum."""
    
    def test_tile_types_exist(self):
        """Test all tile types are defined."""
        assert TileType.FLOOR
        assert TileType.WALL
        assert TileType.DOOR
        assert TileType.STAIRS_UP
        assert TileType.STAIRS_DOWN
        assert TileType.WATER
        assert TileType.LAVA
        assert TileType.CHEST
        assert TileType.ALTAR
        assert TileType.EMPTY


class TestRoom:
    """Test room data structure."""
    
    def test_room_creation(self):
        """Test creating a room."""
        room = Room(5, 10, 8, 6)
        
        assert room.x == 5
        assert room.y == 10
        assert room.width == 8
        assert room.height == 6
        
    def test_room_center(self):
        """Test getting room center."""
        room = Room(0, 0, 10, 10)
        cx, cy = room.center()
        
        assert cx == 5
        assert cy == 5
        
    def test_room_intersects(self):
        """Test room intersection."""
        room1 = Room(0, 0, 10, 10)
        room2 = Room(5, 5, 10, 10)
        room3 = Room(20, 20, 10, 10)
        
        assert room1.intersects(room2) is True
        assert room1.intersects(room3) is False
        assert room2.intersects(room3) is False
        
    def test_room_contains_point(self):
        """Test if room contains a point."""
        room = Room(5, 5, 10, 10)
        
        # Points inside
        assert room.contains(10, 10) is True
        assert room.contains(5, 5) is True
        assert room.contains(14, 14) is True
        
        # Points outside
        assert room.contains(4, 10) is False
        assert room.contains(15, 10) is False
        assert room.contains(10, 4) is False
        assert room.contains(10, 15) is False


class TestCorridor:
    """Test corridor data structure."""
    
    def test_corridor_creation(self):
        """Test creating a corridor."""
        corridor = Corridor(5, 10, 15, 10)
        
        assert corridor.x1 == 5
        assert corridor.y1 == 10
        assert corridor.x2 == 15
        assert corridor.y2 == 10
        
    def test_corridor_points(self):
        """Test getting corridor points."""
        # Horizontal corridor
        corridor = Corridor(0, 5, 10, 5)
        points = list(corridor.get_points())
        
        assert len(points) == 11
        assert (0, 5) in points
        assert (10, 5) in points
        
        # Vertical corridor
        corridor = Corridor(5, 0, 5, 10)
        points = list(corridor.get_points())
        
        assert len(points) == 11
        assert (5, 0) in points
        assert (5, 10) in points
        
        # L-shaped corridor
        corridor = Corridor(0, 0, 5, 5)
        points = list(corridor.get_points())
        
        # Should create an L shape
        assert (0, 0) in points
        assert (5, 0) in points
        assert (5, 5) in points


class TestMapGeneratorConfig:
    """Test map generator configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = MapGeneratorConfig()
        
        assert config.width == 80
        assert config.height == 50
        assert config.min_room_size == 4
        assert config.max_room_size == 12
        assert config.max_rooms == 20
        assert config.method == GenerationMethod.ROOMS_AND_CORRIDORS
        
    def test_custom_config(self):
        """Test custom configuration."""
        config = MapGeneratorConfig(
            width=100,
            height=60,
            min_room_size=6,
            max_room_size=15,
            max_rooms=30,
            method=GenerationMethod.CELLULAR_AUTOMATA
        )
        
        assert config.width == 100
        assert config.height == 60
        assert config.min_room_size == 6
        assert config.max_room_size == 15
        assert config.max_rooms == 30
        assert config.method == GenerationMethod.CELLULAR_AUTOMATA


class TestMapGenerator:
    """Test base map generator."""
    
    def test_map_generator_creation(self):
        """Test creating map generator."""
        config = MapGeneratorConfig(width=50, height=30)
        generator = MapGenerator(config)
        
        assert generator.config == config
        assert generator.width == 50
        assert generator.height == 30
        assert generator.tiles is not None
        assert len(generator.tiles) == 30
        assert len(generator.tiles[0]) == 50
        
    def test_clear_map(self):
        """Test clearing the map."""
        config = MapGeneratorConfig(width=10, height=10)
        generator = MapGenerator(config)
        
        generator.clear(TileType.WALL)
        
        for y in range(10):
            for x in range(10):
                assert generator.tiles[y][x] == TileType.WALL
                
    def test_set_tile(self):
        """Test setting individual tiles."""
        config = MapGeneratorConfig(width=10, height=10)
        generator = MapGenerator(config)
        
        generator.set_tile(5, 5, TileType.FLOOR)
        assert generator.tiles[5][5] == TileType.FLOOR
        
        # Out of bounds should not crash
        generator.set_tile(-1, 5, TileType.FLOOR)
        generator.set_tile(5, -1, TileType.FLOOR)
        generator.set_tile(10, 5, TileType.FLOOR)
        generator.set_tile(5, 10, TileType.FLOOR)
        
    def test_get_tile(self):
        """Test getting tile values."""
        config = MapGeneratorConfig(width=10, height=10)
        generator = MapGenerator(config)
        
        generator.set_tile(5, 5, TileType.FLOOR)
        assert generator.get_tile(5, 5) == TileType.FLOOR
        
        # Out of bounds should return EMPTY
        assert generator.get_tile(-1, 5) == TileType.EMPTY
        assert generator.get_tile(5, -1) == TileType.EMPTY
        assert generator.get_tile(10, 5) == TileType.EMPTY
        assert generator.get_tile(5, 10) == TileType.EMPTY
        
    def test_in_bounds(self):
        """Test bounds checking."""
        config = MapGeneratorConfig(width=10, height=10)
        generator = MapGenerator(config)
        
        assert generator.in_bounds(0, 0) is True
        assert generator.in_bounds(9, 9) is True
        assert generator.in_bounds(5, 5) is True
        
        assert generator.in_bounds(-1, 5) is False
        assert generator.in_bounds(5, -1) is False
        assert generator.in_bounds(10, 5) is False
        assert generator.in_bounds(5, 10) is False


class TestDungeonGenerator:
    """Test dungeon generation."""
    
    def test_dungeon_generator_creation(self):
        """Test creating dungeon generator."""
        config = MapGeneratorConfig(
            width=50,
            height=30,
            method=GenerationMethod.ROOMS_AND_CORRIDORS
        )
        generator = DungeonGenerator(config)
        
        assert isinstance(generator, DungeonGenerator)
        assert len(generator.rooms) == 0
        assert len(generator.corridors) == 0
        
    def test_generate_dungeon(self):
        """Test generating a dungeon."""
        config = MapGeneratorConfig(
            width=50,
            height=30,
            max_rooms=10,
            min_room_size=4,
            max_room_size=8
        )
        generator = DungeonGenerator(config)
        
        generator.generate()
        
        # Should have created some rooms
        assert len(generator.rooms) > 0
        assert len(generator.rooms) <= 10
        
        # Should have corridors connecting rooms
        if len(generator.rooms) > 1:
            assert len(generator.corridors) > 0
        
        # Should have floor tiles
        has_floor = False
        for y in range(generator.height):
            for x in range(generator.width):
                if generator.tiles[y][x] == TileType.FLOOR:
                    has_floor = True
                    break
            if has_floor:
                break
        assert has_floor
        
        # Should have stairs
        has_stairs_up = False
        has_stairs_down = False
        for y in range(generator.height):
            for x in range(generator.width):
                if generator.tiles[y][x] == TileType.STAIRS_UP:
                    has_stairs_up = True
                elif generator.tiles[y][x] == TileType.STAIRS_DOWN:
                    has_stairs_down = True
        
        assert has_stairs_up
        assert has_stairs_down
        
    def test_carve_room(self):
        """Test carving a room."""
        config = MapGeneratorConfig(width=20, height=20)
        generator = DungeonGenerator(config)
        generator.clear(TileType.WALL)
        
        room = Room(5, 5, 10, 10)
        generator._carve_room(room)
        
        # Check room interior is floor
        for y in range(6, 14):
            for x in range(6, 14):
                assert generator.tiles[y][x] == TileType.FLOOR
                
        # Check room walls
        for x in range(5, 15):
            assert generator.tiles[5][x] == TileType.WALL
            assert generator.tiles[14][x] == TileType.WALL
        for y in range(5, 15):
            assert generator.tiles[y][5] == TileType.WALL
            assert generator.tiles[y][14] == TileType.WALL
            
    def test_carve_corridor(self):
        """Test carving a corridor."""
        config = MapGeneratorConfig(width=20, height=20)
        generator = DungeonGenerator(config)
        generator.clear(TileType.WALL)
        
        corridor = Corridor(5, 10, 15, 10)
        generator._carve_corridor(corridor)
        
        # Check corridor is floor
        for x in range(5, 16):
            assert generator.tiles[10][x] == TileType.FLOOR


class TestCaveGenerator:
    """Test cave generation."""
    
    def test_cave_generator_creation(self):
        """Test creating cave generator."""
        config = MapGeneratorConfig(
            width=50,
            height=30,
            method=GenerationMethod.CELLULAR_AUTOMATA
        )
        generator = CaveGenerator(config)
        
        assert isinstance(generator, CaveGenerator)
        
    def test_generate_cave(self):
        """Test generating a cave."""
        config = MapGeneratorConfig(
            width=50,
            height=30,
            method=GenerationMethod.CELLULAR_AUTOMATA
        )
        generator = CaveGenerator(config)
        
        generator.generate()
        
        # Should have both floor and wall tiles
        has_floor = False
        has_wall = False
        for y in range(generator.height):
            for x in range(generator.width):
                if generator.tiles[y][x] == TileType.FLOOR:
                    has_floor = True
                elif generator.tiles[y][x] == TileType.WALL:
                    has_wall = True
                    
        assert has_floor
        assert has_wall
        
        # Should have stairs
        has_stairs_up = False
        has_stairs_down = False
        for y in range(generator.height):
            for x in range(generator.width):
                if generator.tiles[y][x] == TileType.STAIRS_UP:
                    has_stairs_up = True
                elif generator.tiles[y][x] == TileType.STAIRS_DOWN:
                    has_stairs_down = True
        
        assert has_stairs_up
        assert has_stairs_down


class TestTownGenerator:
    """Test town generation."""
    
    def test_town_generator_creation(self):
        """Test creating town generator."""
        config = MapGeneratorConfig(
            width=50,
            height=30,
            method=GenerationMethod.TOWN
        )
        generator = TownGenerator(config)
        
        assert isinstance(generator, TownGenerator)
        
    def test_generate_town(self):
        """Test generating a town."""
        config = MapGeneratorConfig(
            width=50,
            height=30,
            method=GenerationMethod.TOWN,
            max_rooms=8  # Buildings
        )
        generator = TownGenerator(config)
        
        generator.generate()
        
        # Should have created some buildings
        assert len(generator.buildings) > 0
        assert len(generator.buildings) <= 8
        
        # Should have floor tiles (roads and building interiors)
        has_floor = False
        for y in range(generator.height):
            for x in range(generator.width):
                if generator.tiles[y][x] == TileType.FLOOR:
                    has_floor = True
                    break
            if has_floor:
                break
        assert has_floor
        
        # Should have doors on buildings
        has_door = False
        for y in range(generator.height):
            for x in range(generator.width):
                if generator.tiles[y][x] == TileType.DOOR:
                    has_door = True
                    break
            if has_door:
                break
        assert has_door


class TestMapGeneratorFactory:
    """Test map generator factory."""
    
    def test_create_dungeon_generator(self):
        """Test creating dungeon generator."""
        from magemines.game.map_generator import create_generator
        
        config = MapGeneratorConfig(method=GenerationMethod.ROOMS_AND_CORRIDORS)
        generator = create_generator(config)
        
        assert isinstance(generator, DungeonGenerator)
        
    def test_create_cave_generator(self):
        """Test creating cave generator."""
        from magemines.game.map_generator import create_generator
        
        config = MapGeneratorConfig(method=GenerationMethod.CELLULAR_AUTOMATA)
        generator = create_generator(config)
        
        assert isinstance(generator, CaveGenerator)
        
    def test_create_town_generator(self):
        """Test creating town generator."""
        from magemines.game.map_generator import create_generator
        
        config = MapGeneratorConfig(method=GenerationMethod.TOWN)
        generator = create_generator(config)
        
        assert isinstance(generator, TownGenerator)