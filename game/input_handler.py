def handle_input(key, player, game_map):
    dx, dy = 0, 0
    if key == 'w': dy = -1
    elif key == 's': dy = 1
    elif key == 'a': dx = -1
    elif key == 'd': dx = 1

    new_x = player.x + dx
    new_y = player.y + dy

    if not game_map.is_blocked(new_x, new_y):
        player.move(dx, dy)
