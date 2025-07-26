"""Test all map generation methods to check for connectivity issues."""

import random
from magemines.game.map_generator import (
    create_generator,
    MapGeneratorConfig,
    GenerationMethod,
    TileType
)
from magemines.game.level_manager import LevelManager
from collections import deque


def flood_fill(tiles, start_x, start_y, width, height):
    """Flood fill to find reachable tiles."""
    visited = set()
    queue = deque([(start_x, start_y)])
    
    while queue:
        x, y = queue.popleft()
        
        if (x, y) in visited:
            continue
        if x < 0 or x >= width or y < 0 or y >= height:
            continue
            
        # Check tile - in the game, walls (#) and closed doors (+) block movement
        tile = tiles[y][x]
        if tile == '#':  # Wall blocks
            continue
        if tile == '+':  # Closed door blocks (this might be the issue!)
            continue
            
        visited.add((x, y))
        
        # Check all 4 directions
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            queue.append((x + dx, y + dy))
    
    return visited


def test_generation_method(method_name, config):
    """Test a specific generation method."""
    print(f"\nTesting {method_name}...")
    
    issues_found = []
    
    for i in range(5):
        random.seed(42 + i)  # Consistent seeds for reproducibility
        generator = create_generator(config)
        generator.generate()
        
        # Convert to tile array like the game uses
        tiles = []
        for y in range(config.height):
            row = []
            for x in range(config.width):
                tile_type = generator.get_tile(x, y)
                # Convert to game representation
                tile_map = {
                    TileType.FLOOR: '.',
                    TileType.WALL: '#',
                    TileType.DOOR: '+',  # Closed doors!
                    TileType.STAIRS_UP: '<',
                    TileType.STAIRS_DOWN: '>',
                    TileType.WATER: '~',
                    TileType.ALTAR: '▲',
                    TileType.EMPTY: '#'
                }
                row.append(tile_map.get(tile_type, '#'))
            tiles.append(row)
        
        # Find a starting position (stairs up or any floor tile)
        start_pos = None
        for y in range(config.height):
            for x in range(config.width):
                if tiles[y][x] == '<':
                    start_pos = (x, y)
                    break
                elif tiles[y][x] == '.' and start_pos is None:
                    start_pos = (x, y)
            if start_pos and tiles[start_pos[1]][start_pos[0]] == '<':
                break
        
        if not start_pos:
            issues_found.append(f"Sample {i}: No starting position found!")
            continue
        
        # Flood fill from start to find reachable areas
        reachable = flood_fill(tiles, start_pos[0], start_pos[1], config.width, config.height)
        
        # Count total accessible tiles (floors, stairs, but NOT closed doors)
        total_accessible = 0
        for y in range(config.height):
            for x in range(config.width):
                if tiles[y][x] in ['.', '<', '>']:
                    total_accessible += 1
        
        # Check if all accessible tiles are reachable
        unreachable_count = total_accessible - len(reachable)
        
        if unreachable_count > 0:
            # Find which areas are blocked
            blocked_areas = []
            for y in range(config.height):
                for x in range(config.width):
                    if tiles[y][x] in ['.', '<', '>'] and (x, y) not in reachable:
                        # Check if it's behind a door
                        behind_door = False
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < config.width and 0 <= ny < config.height:
                                if tiles[ny][nx] == '+':
                                    behind_door = True
                                    break
                        if behind_door:
                            blocked_areas.append((x, y, "behind door"))
                        else:
                            blocked_areas.append((x, y, "disconnected"))
            
            issues_found.append(f"Sample {i}: {unreachable_count} tiles unreachable! Details: {blocked_areas[:5]}...")
            
            # Print a small section of the map showing the issue
            if blocked_areas:
                bx, by, reason = blocked_areas[0]
                print(f"  Issue at ({bx},{by}) - {reason}")
                print("  Map section:")
                for dy in range(max(0, by-3), min(config.height, by+4)):
                    line = "  "
                    for dx in range(max(0, bx-5), min(config.width, bx+6)):
                        if dx == bx and dy == by:
                            line += "X"
                        else:
                            line += tiles[dy][dx]
                    print(line)
    
    return issues_found


def test_level_manager():
    """Test the level manager which handles multi-level dungeons."""
    print("\nTesting Level Manager...")
    
    width, height = 80, 40
    level_manager = LevelManager(width, height)
    
    issues_found = []
    
    # Test first 10 levels
    for depth in range(1, 11):
        level = level_manager.levels[depth - 1]
        tiles = level.tiles
        
        # Get spawn position
        spawn_x, spawn_y = level.get_spawn_position(from_above=True)
        
        # Flood fill from spawn
        reachable = flood_fill(tiles, spawn_x, spawn_y, width, height)
        
        # Count accessible tiles
        total_accessible = sum(1 for y in range(height) for x in range(width) 
                             if tiles[y][x] in ['.', '<', '>'])
        
        unreachable_count = total_accessible - len(reachable)
        
        if unreachable_count > 0:
            # Check if it's due to doors
            door_blocked = 0
            truly_disconnected = 0
            for y in range(height):
                for x in range(width):
                    if tiles[y][x] in ['.', '<', '>'] and (x, y) not in reachable:
                        # Check adjacent tiles for doors
                        has_adjacent_door = False
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < width and 0 <= ny < height and tiles[ny][nx] == '+':
                                has_adjacent_door = True
                                break
                        if has_adjacent_door:
                            door_blocked += 1
                        else:
                            truly_disconnected += 1
            
            if truly_disconnected > 0:
                issues_found.append(f"Level {depth}: {truly_disconnected} tiles truly disconnected!")
            if door_blocked > 0:
                issues_found.append(f"Level {depth}: {door_blocked} tiles blocked by doors")
    
    return issues_found


def main():
    """Run all tests."""
    all_issues = []
    
    # Test dungeon generation
    dungeon_config = MapGeneratorConfig(
        width=80,
        height=40,
        min_room_size=4,
        max_room_size=10,
        max_rooms=15,
        method=GenerationMethod.ROOMS_AND_CORRIDORS
    )
    issues = test_generation_method("Dungeon", dungeon_config)
    all_issues.extend([f"Dungeon: {issue}" for issue in issues])
    
    # Test cave generation
    cave_config = MapGeneratorConfig(
        width=80,
        height=40,
        method=GenerationMethod.CELLULAR_AUTOMATA
    )
    issues = test_generation_method("Cave", cave_config)
    all_issues.extend([f"Cave: {issue}" for issue in issues])
    
    # Test town generation
    town_config = MapGeneratorConfig(
        width=80,
        height=40,
        min_room_size=6,
        max_room_size=12,
        max_rooms=10,
        method=GenerationMethod.TOWN
    )
    issues = test_generation_method("Town", town_config)
    all_issues.extend([f"Town: {issue}" for issue in issues])
    
    # Test level manager
    issues = test_level_manager()
    all_issues.extend([f"LevelManager: {issue}" for issue in issues])
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if all_issues:
        print(f"\nFound {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"  - {issue}")
        print("\nLikely cause: Closed doors ('+') are blocking movement!")
        print("Players need to open doors with 'o' to access all areas.")
    else:
        print("\nNo connectivity issues found!")
        print("All areas are reachable when doors are considered as barriers.")
    
    return len(all_issues)


if __name__ == "__main__":
    exit(main())