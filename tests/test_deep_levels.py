"""Test deep level generation to ensure no recursion errors."""

import sys
from magemines.game.level_manager import LevelManager
from magemines.game.map_generator import create_generator, MapGeneratorConfig, GenerationMethod

def test_deep_level_generation():
    """Test generating deep dungeon levels without recursion errors."""
    print(f"Python recursion limit: {sys.getrecursionlimit()}")
    
    # Create level manager with higher max depth for testing
    width, height = 80, 50
    level_manager = LevelManager(width, height, max_depth=50)
    
    # Test generating deep levels
    test_depths = [5, 10, 15, 20, 25, 30]
    
    for depth in test_depths:
        print(f"\nTesting level {depth}...")
        
        try:
            # Navigate to the desired depth
            while level_manager.current_depth < depth:
                success, _ = level_manager.go_down()
                if not success:
                    print(f"  Cannot go deeper than level {level_manager.current_depth}")
                    break
            
            # Get the level
            level = level_manager.get_current_level()
            
            # Count tiles to verify generation worked
            floor_count = 0
            wall_count = 0
            for y in range(height):
                for x in range(width):
                    tile = level.tiles[y][x]
                    if tile == '.':
                        floor_count += 1
                    elif tile == '#':
                        wall_count += 1
            
            print(f"  Level {depth}: {floor_count} floor tiles, {wall_count} wall tiles")
            
            # Get spawn position to verify connectivity
            spawn_x, spawn_y = level.get_spawn_position(from_above=True)
            print(f"  Spawn position: ({spawn_x}, {spawn_y})")
            
        except RecursionError as e:
            print(f"  ERROR: Recursion error at depth {depth}!")
            raise e
        except Exception as e:
            print(f"  ERROR at depth {depth}: {type(e).__name__}: {e}")
            raise e
    
    print("\nAll levels generated successfully!")

def test_large_cave_generation():
    """Test generating large caves that might trigger recursion errors."""
    print("\nTesting large cave generation...")
    
    # Large cave that would stress recursive flood fill
    config = MapGeneratorConfig(
        width=100,
        height=100,
        method=GenerationMethod.CELLULAR_AUTOMATA,
        initial_density=0.40,  # Less walls = larger connected areas
        smoothing_iterations=5
    )
    
    try:
        generator = create_generator(config)
        generator.generate()
        
        # Count floor tiles
        floor_count = sum(1 for y in range(config.height) for x in range(config.width)
                         if generator.get_tile(x, y).name == 'FLOOR')
        
        print(f"  Generated cave with {floor_count} floor tiles")
        print("  No recursion error!")
        
    except RecursionError:
        print("  ERROR: Recursion error in cave generation!")
        raise

def test_complex_dungeon():
    """Test a complex dungeon with many rooms."""
    print("\nTesting complex dungeon generation...")
    
    config = MapGeneratorConfig(
        width=120,
        height=80,
        min_room_size=3,
        max_room_size=8,
        max_rooms=50,  # Many rooms = complex connectivity checking
        method=GenerationMethod.ROOMS_AND_CORRIDORS
    )
    
    try:
        generator = create_generator(config)
        generator.generate()
        
        room_count = len(generator.rooms) if hasattr(generator, 'rooms') else 0
        print(f"  Generated dungeon with {room_count} rooms")
        print("  No recursion error!")
        
    except RecursionError:
        print("  ERROR: Recursion error in dungeon generation!")
        raise

if __name__ == "__main__":
    test_deep_level_generation()
    test_large_cave_generation()
    test_complex_dungeon()
    print("\n✓ All tests passed!")