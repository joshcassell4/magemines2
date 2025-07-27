"""Comprehensive test of all map generation fixes."""

import sys
sys.path.insert(0, 'src')

from magemines.game.level_manager import LevelManager
from collections import deque

def check_connectivity_from_point(tiles, start_x, start_y, width, height):
    """Check what tiles are reachable from a starting point."""
    visited = set()
    queue = deque([(start_x, start_y)])
    reachable = 0
    
    while queue:
        x, y = queue.popleft()
        
        if (x, y) in visited:
            continue
        
        if not (0 <= x < width and 0 <= y < height):
            continue
            
        if tiles[y][x] == '#':
            continue
        
        visited.add((x, y))
        reachable += 1
        
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in visited:
                queue.append((nx, ny))
    
    return reachable, visited


def test_comprehensive():
    """Test all aspects of map generation."""
    print("Comprehensive Map Generation Test")
    print("=" * 80)
    
    # Create level manager with 10 levels
    level_manager = LevelManager(width=80, height=50, max_depth=10)
    
    issues = []
    
    # Test each level type
    for depth in range(1, 11):
        print(f"\n{'='*40}")
        print(f"Testing Level {depth}")
        print(f"{'='*40}")
        
        # Go to the specific depth
        while level_manager.current_depth < depth:
            success, spawn_pos = level_manager.go_down()
            if not success:
                print(f"ERROR: Could not go down to level {depth}")
                break
        
        level = level_manager.get_current_level()
        print(f"Level type: {type(level.generator).__name__}")
        
        # Get spawn position
        spawn_x, spawn_y = level.get_spawn_position(from_above=True)
        print(f"Spawn position: ({spawn_x}, {spawn_y})")
        print(f"Tile at spawn: '{level.tiles[spawn_y][spawn_x]}'")
        
        # Count tile types
        tile_counts = {}
        total_walkable = 0
        for y in range(level.height):
            for x in range(level.width):
                tile = level.tiles[y][x]
                tile_counts[tile] = tile_counts.get(tile, 0) + 1
                if tile in ['.', '<', '>', '+']:
                    total_walkable += 1
        
        # Convert special characters for printing
        printable_counts = {}
        for tile, count in tile_counts.items():
            if tile == '▲':
                printable_counts['altar'] = count
            elif tile == '□':
                printable_counts['chest'] = count
            elif tile == '≈':
                printable_counts['lava'] = count
            else:
                printable_counts[tile] = count
        print(f"Tile counts: {printable_counts}")
        
        # Check connectivity from spawn point
        reachable, visited_set = check_connectivity_from_point(
            level.tiles, spawn_x, spawn_y, level.width, level.height
        )
        
        connectivity_ratio = reachable / total_walkable if total_walkable > 0 else 0
        print(f"Connectivity: {reachable}/{total_walkable} tiles ({connectivity_ratio*100:.1f}%)")
        
        # Check for issues
        if connectivity_ratio < 0.95:  # Less than 95% connectivity is an issue
            issues.append({
                'depth': depth,
                'type': type(level.generator).__name__,
                'connectivity': connectivity_ratio,
                'reachable': reachable,
                'total': total_walkable
            })
            print("WARNING: Connectivity issue detected!")
        
        # Special checks for each level type
        if type(level.generator).__name__ == 'CaveGenerator':
            if tile_counts.get('+', 0) > 0:
                print("ERROR: Cave has doors!")
                issues.append({
                    'depth': depth,
                    'type': 'CaveGenerator',
                    'issue': 'Has doors',
                    'door_count': tile_counts.get('+', 0)
                })
        
        if type(level.generator).__name__ == 'DungeonGenerator':
            # Check if rooms exist
            if hasattr(level.generator, 'rooms'):
                print(f"Number of rooms: {len(level.generator.rooms)}")
    
    print(f"\n{'='*80}")
    print(f"Test Summary:")
    print(f"{'='*80}")
    
    if not issues:
        print("[OK] All tests passed! No connectivity or generation issues found.")
    else:
        print(f"[FAIL] Found {len(issues)} issues:")
        for issue in issues:
            print(f"  - Level {issue['depth']}: {issue}")
    
    return len(issues) == 0


def test_stress():
    """Stress test with many rapid generations."""
    print("\n\nStress Test: 100 rapid map generations")
    print("=" * 80)
    
    failures = 0
    
    for i in range(100):
        if i % 20 == 0:
            print(f"Progress: {i}/100", end='\r')
        
        # Create a new level manager each time
        level_manager = LevelManager(width=80, height=50, max_depth=5)
        
        # Jump to level 2 (dungeon)
        success, spawn_pos = level_manager.go_down()
        
        if not success or not spawn_pos:
            failures += 1
            continue
        
        # Check spawn position validity
        level = level_manager.get_current_level()
        spawn_x, spawn_y = spawn_pos
        
        if level.tiles[spawn_y][spawn_x] == '#':
            failures += 1
            print(f"\nERROR at iteration {i}: Player spawned in wall!")
    
    print(f"\nStress test complete: {failures}/100 failures")
    return failures == 0


if __name__ == "__main__":
    test_passed = test_comprehensive()
    stress_passed = test_stress()
    
    print("\n" + "="*80)
    print("FINAL RESULTS:")
    print("Comprehensive test:", "PASSED" if test_passed else "FAILED")
    print("Stress test:", "PASSED" if stress_passed else "FAILED")
    print("="*80)