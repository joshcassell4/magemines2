class GameMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [['.' for _ in range(width)] for _ in range(height)]
        for x in range(width):
            self.tiles[0][x] = '#'
            self.tiles[height - 1][x] = '#'
        for y in range(height):
            self.tiles[y][0] = '#'
            self.tiles[y][width - 1] = '#'

    def draw_static(self, term):
        for y in range(self.height):
            for x in range(self.width):
                print(term.move(y, x) + self.tiles[y][x])

    def draw_player(self, term, player):
        print(term.move(player.y, player.x) + '@', end='', flush=True)

    def clear_player(self, term, player):
        print(term.move(player.y, player.x) + self.tiles[player.y][player.x], end='', flush=True)

    def is_blocked(self, x, y):
        return self.tiles[y][x] == '#'
