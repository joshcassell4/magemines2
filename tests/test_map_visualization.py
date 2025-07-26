"""Visual test for map generation - creates maps and saves them to files."""

import os
from datetime import datetime
from magemines.game.map_generator import (
    DungeonGenerator, 
    MapGeneratorConfig, 
    TileType,
    GenerationMethod
)
from collections import deque


def flood_fill(generator, start_x, start_y):
    """Use flood fill to find all reachable floor tiles."""
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


def visualize_map_with_rooms(generator, show_room_numbers=True):
    """Create a visual representation of the map with room numbers."""
    lines = []
    
    # Create a map of positions to room numbers
    pos_to_room = {}
    if show_room_numbers and hasattr(generator, 'rooms'):
        for i, room in enumerate(generator.rooms):
            # Mark room centers
            cx, cy = room.center()
            pos_to_room[(cx, cy)] = str(i)
    
    # Find disconnected areas
    if hasattr(generator, 'rooms') and generator.rooms:
        start_x, start_y = generator.rooms[0].center()
        reachable = flood_fill(generator, start_x, start_y)
        
        # Find which rooms are disconnected
        disconnected_rooms = []
        for i, room in enumerate(generator.rooms):
            room_reachable = False
            for y in range(room.y + 1, room.y + room.height - 1):
                for x in range(room.x + 1, room.x + room.width - 1):
                    if (x, y) in reachable:
                        room_reachable = True
                        break
                if room_reachable:
                    break
            if not room_reachable:
                disconnected_rooms.append(i)
    else:
        reachable = set()
        disconnected_rooms = []
    
    for y in range(generator.height):
        line = ""
        for x in range(generator.width):
            # Check if this position has a room number
            if (x, y) in pos_to_room:
                line += pos_to_room[(x, y)]
            else:
                tile = generator.get_tile(x, y)
                
                # Check if this is a disconnected floor tile
                is_disconnected = False
                if tile == TileType.FLOOR and (x, y) not in reachable:
                    is_disconnected = True
                
                if is_disconnected:
                    line += "X"  # Mark disconnected areas
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
    
    return "\n".join(lines), disconnected_rooms


def generate_test_maps():
    """Generate several test maps and save them to files."""
    # Create output directory
    output_dir = os.path.join("tests", "map_outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Test configurations
    configs = [
        {
            "name": "small_dungeon",
            "config": MapGeneratorConfig(
                width=40,
                height=25,
                min_room_size=3,
                max_room_size=6,
                max_rooms=5
            )
        },
        {
            "name": "medium_dungeon",
            "config": MapGeneratorConfig(
                width=60,
                height=40,
                min_room_size=4,
                max_room_size=8,
                max_rooms=10
            )
        },
        {
            "name": "game_config",
            "config": MapGeneratorConfig(
                width=80,
                height=40,
                min_room_size=4,
                max_room_size=10,
                max_rooms=15
            )
        },
        {
            "name": "dense_dungeon",
            "config": MapGeneratorConfig(
                width=80,
                height=50,
                min_room_size=3,
                max_room_size=6,
                max_rooms=25
            )
        }
    ]
    
    results = []
    
    for test_config in configs:
        print(f"\nGenerating {test_config['name']}...")
        
        # Generate multiple samples
        for i in range(3):
            generator = DungeonGenerator(test_config['config'])
            generator.generate()
            
            # Create visualization
            map_str, disconnected = visualize_map_with_rooms(generator)
            
            # Save to file
            filename = f"{test_config['name']}_{timestamp}_{i}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                f.write(f"Configuration: {test_config['name']}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Sample: {i}\n")
                f.write(f"Total rooms: {len(generator.rooms) if hasattr(generator, 'rooms') else 0}\n")
                f.write(f"Disconnected rooms: {disconnected}\n")
                f.write(f"Width: {test_config['config'].width}, Height: {test_config['config'].height}\n")
                f.write(f"Room size: {test_config['config'].min_room_size}-{test_config['config'].max_room_size}\n")
                f.write(f"Max rooms: {test_config['config'].max_rooms}\n")
                f.write("\nMap (numbers = room centers, X = disconnected areas):\n")
                f.write(map_str)
                
                # Add room details
                if hasattr(generator, 'rooms'):
                    f.write("\n\nRoom details:\n")
                    for j, room in enumerate(generator.rooms):
                        cx, cy = room.center()
                        status = "DISCONNECTED" if j in disconnected else "Connected"
                        f.write(f"Room {j}: pos=({room.x},{room.y}) size=({room.width}x{room.height}) center=({cx},{cy}) - {status}\n")
            
            print(f"  Saved to: {filepath}")
            
            result = {
                "config": test_config['name'],
                "sample": i,
                "total_rooms": len(generator.rooms) if hasattr(generator, 'rooms') else 0,
                "disconnected": len(disconnected),
                "filepath": filepath
            }
            results.append(result)
            
            if disconnected:
                print(f"  WARNING: Found {len(disconnected)} disconnected rooms!")
    
    # Summary
    print("\n=== Summary ===")
    print(f"Generated {len(results)} maps")
    print(f"Output directory: {output_dir}")
    
    failed = [r for r in results if r['disconnected'] > 0]
    if failed:
        print(f"\nMaps with disconnected rooms: {len(failed)}")
        for f in failed:
            print(f"  {f['config']} sample {f['sample']}: {f['disconnected']}/{f['total_rooms']} disconnected")
    else:
        print("\nAll maps are fully connected!")
    
    return results


if __name__ == "__main__":
    generate_test_maps()