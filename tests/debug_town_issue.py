"""Debug the town generation issue at position (39,0)."""

from magemines.game.map_generator import TownGenerator, MapGeneratorConfig, GenerationMethod, TileType

# Create a town generator
config = MapGeneratorConfig(
    width=80,
    height=40,
    method=GenerationMethod.TOWN
)

generator = TownGenerator(config)
generator.generate()

# Check what's at position (39,0) and surrounding area
print("Area around (39,0):")
for y in range(0, 5):
    line = ""
    for x in range(35, 45):
        if x == 39 and y == 0:
            line += "X"
        else:
            tile = generator.get_tile(x, y)
            if tile == TileType.WALL:
                line += "#"
            elif tile == TileType.FLOOR:
                line += "."
            elif tile == TileType.DOOR:
                line += "+"
            else:
                line += " "
    print(f"y={y}: {line}")

print(f"\nTile at (39,0): {generator.get_tile(39, 0)}")
print(f"Buildings near (39,0):")
for i, building in enumerate(generator.buildings):
    if building.x <= 39 <= building.x + building.width and building.y <= 0 <= building.y + building.height:
        print(f"  Building {i}: x={building.x}, y={building.y}, w={building.width}, h={building.height}")