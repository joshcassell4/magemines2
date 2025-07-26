# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MageMines is a terminal-based roguelike game built with Python using the `blessed` library for terminal manipulation. The game currently features basic player movement within a map bounded by walls and includes OpenAI integration for AI-powered features.

## Development Philosophy: Playtest Driven Development

We're using **Playtest Driven Development (PDD)** instead of strict TDD. This approach emphasizes:

1. **Build → Playtest → Iterate**: Create features, playtest them, gather feedback, then refine
2. **Emergent Gameplay**: Allow for unexpected behaviors and "happy accidents" 
3. **Narrative-First**: Focus on the player experience and story that emerges
4. **Flexible Testing**: Write unit tests for concrete systems (pathfinding, collision) but allow creative features to evolve through play

### Playtest Workflow
1. Implement a feature based on the game vision
2. Run the game and experiment with the feature
3. Document what works, what surprises, and what needs improvement
4. Iterate based on playtest results
5. Write tests for stable, concrete behaviors (not emergent ones)

## Development Commands

```bash
# Run the game
make run

# Install dependencies
uv pip install -r requirements.txt

# Install the project in editable mode
uv pip install -e .
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

## Playtest Notes

When playtesting, consider:
- **Atmosphere**: Does the world feel mysterious and alive?
- **Emergence**: What unexpected behaviors arise?
- **Narrative**: What story is being told through play?
- **Sacred Chaos**: Some unpredictability is intentional - embrace it

## Development Guidelines

- **Project Status Tracking**:
  - Update status to note starting implementation before implementing new features
  - After feature is complete, update status again
- **Playtest Documentation**:
  - Record surprising moments
  - Note emergent behaviors 
  - Capture the "feel" of playing
  - Document both bugs AND happy accidents

## Game Concepts

### "Whispers Beneath the Mountain"

- **Genre**: ASCII turn-based world builder
- **Core Loop**:
  - Player navigates via arrow keys or commands
  - Each turn advances time and causes NPCs to act
  - The player collects materials, builds altars, and communicates with ancient beings
- **Key Gameplay Expectations**:
  - Actions consume time and energy
  - Certain areas become more alive or mysterious the more time is spent there
  - ASCII symbols evolve as the world deepens
- **Testing Notes**:
  - Tests should not assume deterministic output
  - Emergence is intentional. Some chaos is sacred

## Test Scenarios

### Narrative Simulation Tests

- Test scenario for simulating player exploration with narrative tracking
  - Simulates a player's journey through a mystical cave environment
  - Focuses on capturing the narrative trace of player actions
  - Example test setup demonstrates AI-guided gameplay simulation
  - Validates the game's ability to generate emergent storytelling experiences

```python
# Simulate this test instead:
"""
Test Scenario:
1. Player wakes in cave with torch.
2. Walks north three steps.
3. Encounters ancient door. It should shimmer.
4. Player knocks once. Echo should reply.

Expected narrative trace: ["wake", "walk", "walk", "walk", "door", "knock", "echo"]
"""

# Let the AI generate:
simulate_gameplay(scenario)
```

## AI Playtesting Scenarios

- **Scenario: Magemines AI Playtester**
  - You're an AI playtester in a turn-based ASCII world
  - Every move, describe what you see, what you do, and what you expect next
  - Game: "Magemines"
  - Starting Scenario: You wake in a soft fog on the edge of a broken temple

## Testing Best Practices

- Be sure to try and do any tests through unit tests instead of scripts. This helps keep the testing in a coherent, organized place and able to work with the Makefile

## Playtest Script Guidelines

- Playtest scripts are ok however. Just try to keep them organized and able to be maintained.

## Screen Rendering Concerns

- Minimizing screen flickering in this project is a maximum concern. Please update the screen carefully and only redraw the pieces of the screen that need redrawing during any screen manipulation.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.