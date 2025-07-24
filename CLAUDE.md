# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MageMines is a terminal-based roguelike game built with Python using the `blessed` library for terminal manipulation. The game currently features basic player movement within a map bounded by walls and includes OpenAI integration for AI-powered features.

## Development Commands

```bash
# Run the game
python main.py

# Install dependencies
pip install -r requirements.txt
# OR if using uv package manager:
uv pip install -r requirements.txt

# Install the project in editable mode
pip install -e .
```

## Architecture Overview

The game follows a modular architecture with clear separation of concerns:

### Core Components

1. **Entry Point** (`main.py`): Simple launcher that calls the game loop
2. **Game Loop** (`game/game_loop.py`): Central game controller that:
   - Initializes the terminal with blessed
   - Creates the game map and player
   - Handles the main game loop (input → update → render cycle)
   - Uses terminal capabilities: fullscreen, cbreak mode, hidden cursor

3. **Map System** (`game/map.py`):
   - `GameMap` class manages the game world
   - Creates a border of walls (`#`) around the playable area
   - Handles rendering of static map elements and dynamic entities
   - Provides collision detection via `is_blocked()`

4. **Player** (`game/player.py`):
   - Simple entity with position (x, y)
   - Movement handled through `move(dx, dy)` method

5. **Input Handling** (`game/input_handler.py`):
   - Processes keyboard input (WASD movement, Q to quit)
   - Validates movement against map boundaries
   - Updates player position if move is valid

### Key Design Patterns

- **Separation of Rendering**: The map handles all terminal drawing operations, keeping display logic centralized
- **Entity System Foundation**: `entities.py` provides a base `Entity` class for future NPCs/monsters
- **Terminal State Management**: The game properly manages terminal modes and cleanup through context managers

### Terminal Rendering Strategy

The game uses an efficient rendering approach:
- Static map elements are drawn once at startup
- Only the player position is updated each frame (clear old position, draw new position)
- This minimizes screen flicker and improves performance

## Dependencies

- `blessed==1.20.0`: Terminal control library for cross-platform terminal manipulation
- `openai`: OpenAI API client for AI-powered features (narrative generation, NPC dialogue, etc.)
- Python >=3.11 (specified in pyproject.toml)

## Future Extension Points

The codebase is structured to easily add:
- AI-powered features using OpenAI integration (dynamic narratives, intelligent NPCs, procedural content)
- Additional entities (monsters, NPCs) using the `Entity` base class
- Map features (doors, items, terrain types) by extending the tile system
- Game states (menus, inventory) by expanding the game loop
- Visual effects by leveraging blessed's color and styling capabilities

## Development Guidelines

- **Project Status Tracking**:
  - Update status to note starting implementation before implementing new features
  - After feature is complete, update status again