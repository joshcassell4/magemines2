"""Test specifically for cave door issues at different depths."""

import sys
sys.path.insert(0, 'src')

from magemines.game.level_manager import LevelManager
from magemines.game.map_generator import TileType

def test_cave_levels():
    """Test cave levels specifically (every 5th level)."""
    print("Testing Cave Levels for Door Issues")
    print("=" * 80)
    
    # Create level manager
    level_manager = LevelManager(width=80, height=50, max_depth=20)
    
    # Test levels 5, 10, 15, 20 (cave levels)
    cave_depths = [5, 10, 15, 20]
    
    for depth in cave_depths:
        print(f"\nChecking level {depth} (should be a cave)...")
        
        # Go to the specific depth
        while level_manager.current_depth < depth:
            level_manager.go_down()
        
        # Get the current level
        level = level_manager.get_current_level()
        generator = level.generator
        
        # Check generator type
        print(f"Generator type: {type(generator).__name__}")
        
        # Count doors
        door_count = 0
        wall_adjacent_doors = []
        
        for y in range(level.height):
            for x in range(level.width):
                if level.tiles[y][x] == '+':
                    door_count += 1
                    
                    # Check if door is adjacent to only walls (shouldn't happen)
                    adjacent_tiles = []
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < level.width and 0 <= ny < level.height:
                            adjacent_tiles.append(level.tiles[ny][nx])
                    
                    # Count walls around door
                    wall_count = sum(1 for t in adjacent_tiles if t == '#')
                    if wall_count >= 3:  # Door with 3+ walls around it is suspicious
                        wall_adjacent_doors.append((x, y, wall_count))
        
        print(f"Doors found: {door_count}")
        if wall_adjacent_doors:
            print(f"Doors surrounded by walls: {len(wall_adjacent_doors)}")
            for x, y, wall_count in wall_adjacent_doors[:5]:  # Show first 5
                print(f"  Door at ({x}, {y}) has {wall_count} walls around it")
        
        # Show a small section of the map around a door if found
        if door_count > 0:
            # Find first door
            door_x, door_y = None, None
            for y in range(level.height):
                for x in range(level.width):
                    if level.tiles[y][x] == '+':
                        door_x, door_y = x, y
                        break
                if door_x is not None:
                    break
            
            if door_x is not None:
                print(f"\nMap section around door at ({door_x}, {door_y}):")
                for dy in range(-3, 4):
                    line = ""
                    for dx in range(-5, 6):
                        nx, ny = door_x + dx, door_y + dy
                        if 0 <= nx < level.width and 0 <= ny < level.height:
                            line += level.tiles[ny][nx]
                        else:
                            line += " "
                    print(f"  {line}")


def test_regular_dungeon_levels():
    """Test regular dungeon levels for comparison."""
    print("\n\nTesting Regular Dungeon Levels for Comparison")
    print("=" * 80)
    
    # Create level manager
    level_manager = LevelManager(width=80, height=50, max_depth=10)
    
    # Test levels 2, 3, 4 (regular dungeons)
    dungeon_depths = [2, 3, 4]
    
    for depth in dungeon_depths:
        print(f"\nChecking level {depth} (should be a dungeon)...")
        
        # Go to the specific depth
        while level_manager.current_depth < depth:
            level_manager.go_down()
        
        # Get the current level
        level = level_manager.get_current_level()
        
        # Check generator type
        print(f"Generator type: {type(level.generator).__name__}")
        
        # Count doors
        door_count = 0
        for y in range(level.height):
            for x in range(level.width):
                if level.tiles[y][x] == '+':
                    door_count += 1
        
        print(f"Doors found: {door_count}")


if __name__ == "__main__":
    test_cave_levels()
    test_regular_dungeon_levels()