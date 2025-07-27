"""Tests for the multi-level dungeon system."""

import pytest
from magemines.game.level_manager import LevelManager
from magemines.game.dungeon_level import DungeonLevel
from magemines.game.map_generation import GenerationMethod, TileType


class TestLevelManager:
    """Test the level manager functionality."""
    
    def test_initial_level_creation(self):
        """Test that the first level is created properly."""
        manager = LevelManager(50, 30, max_depth=5)
        
        assert manager.current_depth == 1
        assert len(manager.levels) == 1
        assert 1 in manager.levels
        
        level = manager.get_current_level()
        assert isinstance(level, DungeonLevel)
        assert level.depth == 1
        assert level.width == 50
        assert level.height == 30
    
    def test_level_generation_types(self):
        """Test that different level types are generated at correct depths."""
        manager = LevelManager(50, 30, max_depth=10)
        
        # Level 1 should be a town
        level1 = manager.levels[1]
        assert level1.generator.config.method == GenerationMethod.TOWN
        
        # Generate level 5
        for _ in range(4):
            manager.go_down()
        
        # Level 5 should be a cave
        level5 = manager.get_current_level()
        assert level5.generator.config.method == GenerationMethod.CELLULAR_AUTOMATA
        
        # Generate level 3
        manager.current_depth = 3
        manager._generate_level(3)
        level3 = manager.levels[3]
        # Regular levels should be dungeons
        assert level3.generator.config.method == GenerationMethod.ROOMS_AND_CORRIDORS
    
    def test_going_down_levels(self):
        """Test descending through levels."""
        manager = LevelManager(50, 30, max_depth=5)
        
        # Start at level 1
        assert manager.current_depth == 1
        
        # Go down
        success, spawn_pos = manager.go_down()
        assert success is True
        assert spawn_pos is not None
        assert manager.current_depth == 2
        
        # New level should be generated
        assert 2 in manager.levels
        level2 = manager.get_current_level()
        assert level2.depth == 2
    
    def test_going_up_levels(self):
        """Test ascending through levels."""
        manager = LevelManager(50, 30, max_depth=5)
        
        # Go down first
        manager.go_down()
        manager.go_down()
        assert manager.current_depth == 3
        
        # Now go up
        success, spawn_pos = manager.go_up()
        assert success is True
        assert spawn_pos is not None
        assert manager.current_depth == 2
        
        # Level 2 should still exist (persistence)
        assert 2 in manager.levels
    
    def test_depth_limits(self):
        """Test that we can't go beyond depth limits."""
        manager = LevelManager(50, 30, max_depth=3)
        
        # Can't go up from level 1
        assert manager.can_go_up() is False
        success, _ = manager.go_up()
        assert success is False
        assert manager.current_depth == 1
        
        # Go to max depth
        manager.go_down()
        manager.go_down()
        assert manager.current_depth == 3
        
        # Can't go deeper
        assert manager.can_go_down() is False
        success, _ = manager.go_down()
        assert success is False
        assert manager.current_depth == 3
    
    def test_spawn_positions(self):
        """Test that spawn positions are set correctly."""
        manager = LevelManager(50, 30, max_depth=5)
        
        # Go down (coming from above)
        success, spawn_pos = manager.go_down()
        assert success is True
        
        # Should spawn at up stairs on level 2
        level2 = manager.get_current_level()
        assert spawn_pos == level2.stairs_up_pos
        
        # Go back up (coming from below)
        success, spawn_pos = manager.go_up()
        assert success is True
        
        # Should spawn at down stairs on level 1
        level1 = manager.get_current_level()
        assert spawn_pos == level1.stairs_down_pos
    
    def test_depth_based_difficulty(self):
        """Test that deeper levels have harder configurations."""
        manager = LevelManager(50, 30, max_depth=10)
        
        # Check level 1 config
        config1 = manager._create_config_for_depth(1)
        
        # Check level 10 config
        config10 = manager._create_config_for_depth(10)
        
        # Deeper levels should have more rooms
        assert config10.max_rooms > config1.max_rooms
        
        # Deeper levels should allow larger rooms
        assert config10.max_room_size > config1.max_room_size
        
        # Deeper levels should have more diagonal corridors
        assert config10.diagonal_chance > config1.diagonal_chance
    
    def test_stairs_placement(self):
        """Test that stairs are placed correctly in levels."""
        manager = LevelManager(50, 30, max_depth=5)
        
        level1 = manager.get_current_level()
        
        # Level 1 should have down stairs
        assert level1.stairs_down_pos is not None
        down_x, down_y = level1.stairs_down_pos
        assert level1.tiles[down_y][down_x] == '>'
        
        # Level 1 might have up stairs (for town exit)
        if level1.stairs_up_pos:
            up_x, up_y = level1.stairs_up_pos
            assert level1.tiles[up_y][up_x] == '<'


class TestDungeonLevel:
    """Test the dungeon level functionality."""
    
    def test_dungeon_level_creation(self):
        """Test creating a dungeon level."""
        from magemines.game.map_generator import DungeonGenerator, MapGeneratorConfig
        
        config = MapGeneratorConfig(width=50, height=30)
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Convert tiles
        tiles = [['.'] * 50 for _ in range(30)]
        
        level = DungeonLevel(
            depth=1,
            width=50,
            height=30,
            generator=generator,
            tiles=tiles
        )
        
        assert level.depth == 1
        assert level.width == 50
        assert level.height == 30
        assert level.entities == {}
        assert level.items == {}
    
    def test_tile_access(self):
        """Test accessing tiles in a level."""
        tiles = [['#'] * 5 for _ in range(5)]
        tiles[2][2] = '.'
        
        level = DungeonLevel(
            depth=1,
            width=5,
            height=5,
            generator=None,
            tiles=tiles
        )
        
        # Test in-bounds access
        assert level.get_tile(2, 2) == '.'
        assert level.get_tile(0, 0) == '#'
        
        # Test out-of-bounds access
        assert level.get_tile(-1, 0) == '#'
        assert level.get_tile(10, 10) == '#'
    
    def test_stairs_detection(self):
        """Test detecting stairs in a level."""
        tiles = [['#'] * 5 for _ in range(5)]
        tiles[1][1] = '<'
        tiles[3][3] = '>'
        tiles[2][2] = '.'
        
        level = DungeonLevel(
            depth=1,
            width=5,
            height=5,
            generator=None,
            tiles=tiles
        )
        
        # Test stairs detection
        assert level.is_stairs_up(1, 1) is True
        assert level.is_stairs_down(3, 3) is True
        assert level.is_stairs_up(2, 2) is False
        assert level.is_stairs_down(2, 2) is False
        
        # Test cached positions
        assert level.stairs_up_pos == (1, 1)
        assert level.stairs_down_pos == (3, 3)