#!/usr/bin/env python3
"""Quick test of the multi-level dungeon system."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from magemines.game.level_manager import LevelManager
from magemines.game.map import GameMap


def test_multilevel():
    """Test the multi-level dungeon system."""
    print("Testing Multi-Level Dungeon System")
    print("=" * 50)
    
    # Create a game map with levels
    game_map = GameMap(80, 30, use_levels=True)
    
    print(f"\nStarting at level {game_map.get_current_depth()}")
    print(f"Can go up: {game_map.can_go_up()}")
    print(f"Can go down: {game_map.can_go_down()}")
    
    # Find stairs
    up_stairs = None
    down_stairs = None
    for y in range(game_map.height):
        for x in range(game_map.width):
            if game_map.is_stairs_up(x, y):
                up_stairs = (x, y)
            elif game_map.is_stairs_down(x, y):
                down_stairs = (x, y)
    
    print(f"Up stairs at: {up_stairs}")
    print(f"Down stairs at: {down_stairs}")
    
    # Try to go down
    if down_stairs:
        print("\nGoing down...")
        success, new_pos = game_map.change_level(going_down=True)
        if success:
            print(f"Success! Now at level {game_map.get_current_depth()}")
            print(f"Spawned at position: {new_pos}")
            print(f"Can go up: {game_map.can_go_up()}")
            print(f"Can go down: {game_map.can_go_down()}")
            
            # Go down again
            print("\nGoing down again...")
            success, new_pos = game_map.change_level(going_down=True)
            if success:
                print(f"Success! Now at level {game_map.get_current_depth()}")
                
                # Go back up
                print("\nGoing back up...")
                success, new_pos = game_map.change_level(going_down=False)
                if success:
                    print(f"Success! Now at level {game_map.get_current_depth()}")
    
    # Test level generation types
    print("\n" + "=" * 50)
    print("Level Generation Types:")
    manager = game_map.level_manager
    
    for depth in [1, 3, 5, 7, 10]:
        if depth <= manager.max_depth:
            config = manager._create_config_for_depth(depth)
            print(f"Level {depth}: {config.method.name}")
            print(f"  - Max rooms: {config.max_rooms}")
            print(f"  - Max room size: {config.max_room_size}")
            print(f"  - Diagonal corridors: {config.diagonal_corridors}")


if __name__ == "__main__":
    test_multilevel()