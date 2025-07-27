# MageMines Configuration System

MageMines uses a comprehensive JSON-based configuration system that allows fine-tuning of all game parameters without modifying code.

## Overview

The configuration system is designed to be:
- **Modular**: Separated into logical sections for easy management
- **Expandable**: New configuration options can be added easily
- **Type-safe**: Uses Python dataclasses for validation
- **Override-friendly**: Supports layered configuration with overrides

## Configuration Files Location

All configuration files are stored in the `config/` directory at the project root:

```
magemines/
├── config/
│   ├── game.json           # Core game settings
│   ├── display.json        # Display and rendering
│   ├── map_generation.json # Map generation parameters
│   ├── entities.json       # Entity system settings
│   ├── ui.json            # User interface configuration
│   ├── ai.json            # AI behavior settings
│   ├── divine_powers.json  # Divine spells configuration
│   ├── resources.json      # Resource and crafting
│   ├── combat.json        # Combat system parameters
│   ├── performance.json    # Performance optimization
│   ├── debug.json         # Debug and development
│   └── overrides.json     # User overrides (optional)
```

## Configuration Sections

### Game Configuration (`game.json`)
Core game settings that affect overall gameplay.

```json
{
  "seed": null,              // Random seed (null for random)
  "difficulty": "normal",    // Game difficulty: easy, normal, hard, expert
  "turn_duration_ms": 100,   // Turn processing time limit
  "max_turns": null,         // Maximum game length (null for unlimited)
  "autosave_interval": 100,  // Turns between autosaves
  "autosave_enabled": true   // Enable/disable autosaving
}
```

### Display Configuration (`display.json`)
Settings for terminal display and rendering.

```json
{
  "width": 80,               // Default terminal width
  "height": 24,              // Default terminal height
  "fullscreen": true,        // Use fullscreen mode
  "color_mode": "rgb",       // Color mode: rgb, 256, 16, mono
  "font_size": null,         // Font size override
  "vsync": true,             // Vertical sync
  "fps_limit": 60,           // FPS limit for animations
  "show_fps": false          // Show FPS counter
}
```

### Map Generation Configuration (`map_generation.json`)
Parameters controlling procedural map generation.

```json
{
  "default_width": 80,
  "default_height": 50,
  
  // Room generation
  "min_room_size": 4,
  "max_room_size": 12,
  "max_rooms_base": 20,
  "rooms_per_level": 0.5,    // Additional rooms per depth level
  
  // Corridor settings
  "corridor_style": "l_shaped",  // l_shaped, diagonal, mixed
  "corridor_width": 1,
  "door_chance": 0.2,
  
  // Level themes
  "town_frequency": 5,       // Town every N levels
  "cave_frequency": 5,       // Cave every N levels
  
  // Cave generation (cellular automata)
  "cave_fill_probability": 0.45,
  "cave_smoothing_iterations": 5,
  "cave_neighbor_threshold": 4,
  
  // Town generation
  "town_building_min_size": 4,
  "town_building_max_size": 8,
  "town_street_width": 3,
  "town_building_door_chance": 1.0
}
```

### UI Configuration (`ui.json`)
User interface appearance and behavior.

```json
{
  // Message pane
  "message_pane_width": 40,
  "message_pane_height": 8,
  "message_history_size": 1000,
  "message_categories": ["system", "info", "warning", ...],
  
  // Color scheme (RGB values)
  "color_scheme": {
    "background": [0, 0, 0],
    "foreground": [255, 255, 255],
    "wall": [128, 128, 128],
    "floor": [64, 64, 64],
    // ... more colors
  },
  
  // Header bar
  "header_show_turn": true,
  "header_show_depth": true,
  "header_show_mana": true,
  "header_show_fps": false,
  
  // Loading overlay
  "loading_spinner_speed": 0.1,
  "loading_styles": ["spinner", "dots", "progress_bar"]
}
```

### AI Configuration (`ai.json`)
AI behavior and OpenAI integration settings.

```json
{
  // Pathfinding
  "pathfinding_algorithm": "astar",
  "pathfinding_max_steps": 1000,
  "pathfinding_cache_size": 100,
  
  // Mage AI
  "mage_ai_think_time": 0.1,
  "mage_ai_update_frequency": 1,
  "mage_task_priorities": {
    "survive": 1.0,
    "eat": 0.8,
    "gather": 0.6,
    "craft": 0.5,
    "socialize": 0.4,
    "explore": 0.3
  },
  
  // OpenAI integration
  "openai_enabled": false,
  "openai_model": "gpt-4o-mini",
  "openai_temperature": 0.7,
  "openai_max_tokens": 150,
  "openai_cache_responses": true
}
```

### Debug Configuration (`debug.json`)
Development and debugging options.

```json
{
  "debug_mode": false,
  "show_room_numbers": false,
  "show_pathfinding": false,
  "show_entity_states": false,
  "show_tile_coordinates": false,
  "immortal_player": false,
  "unlimited_mana": false,
  "reveal_all_maps": false,
  "fast_map_generation": false,
  "log_level": "INFO",
  "log_file": "magemines.log"
}
```

## Configuration Overrides

The system supports configuration overrides through the `overrides.json` file. This file is not tracked by git and allows users to customize settings without modifying the base configuration files.

### Creating Overrides

1. Copy `config/overrides.example.json` to `config/overrides.json`
2. Add only the settings you want to override:

```json
{
  "game": {
    "difficulty": "hard",
    "autosave_interval": 50
  },
  "debug": {
    "debug_mode": true,
    "show_room_numbers": true
  }
}
```

### Override Priority

Settings are loaded in this order (later overrides earlier):
1. Default values in code
2. Configuration files (`*.json`)
3. Override file (`overrides.json`)
4. Command-line arguments (future feature)

## Using Configuration in Code

### Basic Usage

```python
from magemines.core.config import get_config, ConfigSection

# Get a configuration section
game_config = get_config(ConfigSection.GAME)
print(f"Difficulty: {game_config.difficulty}")

# Access nested configuration
ui_config = get_config(ConfigSection.UI)
wall_color = ui_config.color_scheme["wall"]
```

### Advanced Usage

```python
from magemines.core.config import get_config_manager

# Get the configuration manager
config_manager = get_config_manager()

# Reload all configurations (useful for hot-reloading)
config_manager.reload()

# Save current configuration state
config_manager.save_all()

# Create default configuration files
config_manager.create_default_configs()
```

### Adding New Configuration Options

1. Add the field to the appropriate dataclass in `core/config.py`:

```python
@dataclass
class GameConfig:
    # ... existing fields ...
    new_option: str = "default_value"
```

2. Regenerate default configs:
```bash
python scripts/generate_default_configs.py
```

3. Use the new configuration in your code:
```python
game_config = get_config(ConfigSection.GAME)
value = game_config.new_option
```

## Configuration Validation

The configuration system performs basic type validation through Python dataclasses. Invalid values in JSON files will result in the default values being used, with warnings logged.

### Type Conversions

- **Integers**: Must be valid JSON numbers
- **Floats**: Must be valid JSON numbers
- **Booleans**: Must be `true` or `false` (lowercase)
- **Strings**: Must be quoted
- **Lists**: Must use JSON array syntax `[]`
- **Dicts**: Must use JSON object syntax `{}`

## Best Practices

1. **Don't edit default configs directly** - Use `overrides.json` for customization
2. **Keep overrides minimal** - Only override what you need
3. **Test configuration changes** - Some combinations may cause issues
4. **Use appropriate types** - Match the expected type in the dataclass
5. **Document new options** - Update this file when adding configuration

## Troubleshooting

### Configuration Not Loading

Check the log output for warnings about invalid JSON or missing files.

### Changes Not Taking Effect

1. Ensure you're editing the correct file
2. Check JSON syntax is valid
3. Restart the game (hot-reload coming soon)
4. Verify override priority

### Invalid JSON Errors

Use a JSON validator or editor with syntax checking. Common issues:
- Missing commas between items
- Trailing commas (not allowed in JSON)
- Unquoted keys
- Single quotes instead of double quotes

## Future Enhancements

- Command-line configuration overrides
- Hot-reloading of configuration changes
- Configuration profiles (preset collections)
- In-game configuration editor
- Schema validation with better error messages