# MageMines Test-Driven Development Workflow

## Overview

This document outlines the comprehensive Test-Driven Development (TDD) strategy for MageMines, a god-game combining elements from Dwarf Fortress, D&D, and Populous. The approach emphasizes incremental development with testing at every stage to ensure high code quality, maintainability, and performance.

## Core TDD Principles

1. **Red-Green-Refactor Cycle**
   - Red: Write a failing test that defines desired behavior
   - Green: Write minimal code to make the test pass
   - Refactor: Improve code quality while keeping tests green

2. **Test First, Code Second**
   - Every feature starts with tests
   - Tests define the API and expected behavior
   - Implementation follows test specifications

3. **Incremental Development**
   - Small, testable units of functionality
   - Continuous integration after each feature
   - Regular refactoring to maintain code quality

## Turn-Based Architecture

MageMines is a turn-based game where time advances only when the player acts. This design impacts all systems:

### Turn Resolution Order
1. **Player Input**: Game waits for player action
2. **Player Action**: Player's action is executed
3. **World Updates**: Environmental effects, timers, etc.
4. **Entity Actions**: All entities act in initiative order
5. **Effect Resolution**: Spell effects, damage, status changes
6. **Render Changes**: Only modified tiles are redrawn
7. **Message Display**: Turn summary in message pane

### Key Turn-Based Principles
- **No Real-Time Updates**: Nothing changes between player actions
- **Deterministic Order**: Same input always produces same result
- **Partial Rendering**: Only redraw what changed this turn
- **Action Economy**: Some actions may consume multiple turns
- **Responsive Input**: Turn resolution should complete in <100ms

### Testing Turn-Based Systems
- Test action ordering and priority
- Test that state is frozen between turns
- Test partial rendering efficiency
- Test turn resolution performance with many entities
- Test action interruption and cancellation

## Testing Framework Stack

### Core Testing Tools
- **pytest**: Primary testing framework
- **pytest-mock**: Mocking external dependencies
- **pytest-asyncio**: Testing async OpenAI integration
- **pytest-benchmark**: Performance testing
- **pytest-cov**: Code coverage reporting
- **hypothesis**: Property-based testing for procedural generation

### Specialized Testing Tools
- **pytest-snapshot**: UI state verification
- **pytest-timeout**: Preventing hanging tests
- **pytest-xdist**: Parallel test execution
- **freezegun**: Time-based testing

## Project Structure for TDD

```
magemines/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── game_state.py      # Centralized game state management
│   │   ├── event_system.py    # Event-driven architecture
│   │   ├── config.py          # Game configuration
│   │   └── constants.py       # Game constants
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── base.py           # Entity Component System base
│   │   ├── components/       # ECS components
│   │   ├── systems/          # ECS systems
│   │   └── factory.py        # Entity creation
│   ├── world/
│   │   ├── __init__.py
│   │   ├── map_generator.py  # Procedural map generation
│   │   ├── level.py          # Level management
│   │   ├── tile.py           # Tile system
│   │   └── resources.py      # Resource placement
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── behavior_tree.py  # AI behavior trees
│   │   ├── pathfinding.py    # A* pathfinding
│   │   ├── task_system.py    # Mage task management
│   │   └── social.py         # Social interactions
│   ├── spells/
│   │   ├── __init__.py
│   │   ├── divine_spells.py  # Player spell system
│   │   ├── effects.py        # Spell effects
│   │   └── cooldowns.py      # Spell management
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── terminal.py       # Terminal abstraction
│   │   ├── renderer.py       # Rendering system
│   │   ├── colors.py         # Color management with RGB
│   │   ├── message_pane.py   # Scrollable message system
│   │   └── layouts.py        # UI layout management
│   └── integrations/
│       ├── __init__.py
│       ├── openai_client.py  # OpenAI API wrapper
│       ├── narrative.py      # Story generation
│       └── dialogue.py       # Dialogue system
├── tests/
│   ├── unit/
│   │   ├── test_entities.py
│   │   ├── test_map_generation.py
│   │   ├── test_ai_behaviors.py
│   │   ├── test_spells.py
│   │   └── test_ui_components.py
│   ├── integration/
│   │   ├── test_game_loop.py
│   │   ├── test_save_load.py
│   │   ├── test_level_transitions.py
│   │   └── test_openai_integration.py
│   ├── performance/
│   │   ├── test_rendering_speed.py
│   │   ├── test_ai_scalability.py
│   │   └── test_memory_usage.py
│   ├── fixtures/
│   │   ├── mock_terminal.py
│   │   ├── mock_openai.py
│   │   ├── game_states.py
│   │   └── test_maps.py
│   └── conftest.py
├── .github/
│   └── workflows/
│       └── tests.yml         # CI/CD configuration
├── .env.example              # Example environment variables
├── pytest.ini                # Pytest configuration
└── setup.cfg                # Tool configuration
```

## Development Phases

### Phase 1: Foundation & Infrastructure (Week 1)

#### 1.1 Testing Infrastructure Setup
```python
# tests/conftest.py
import pytest
from unittest.mock import Mock
from blessed import Terminal

@pytest.fixture
def mock_terminal():
    """Mock terminal for UI testing"""
    terminal = Mock(spec=Terminal)
    terminal.width = 80
    terminal.height = 24
    terminal.move = Mock(return_value='')
    terminal.color_rgb = Mock(return_value='')
    terminal.on_color_rgb = Mock(return_value='')
    return terminal

@pytest.fixture
def game_config():
    """Standard game configuration for tests"""
    return {
        'map_width': 80,
        'map_height': 24,
        'seed': 42,  # Deterministic for tests
    }
```

#### 1.2 Core Systems with TDD

**Event System Test First:**
```python
# tests/unit/test_event_system.py
def test_event_subscription():
    event_bus = EventBus()
    handler = Mock()
    
    event_bus.subscribe('player_move', handler)
    event_bus.emit('player_move', x=10, y=20)
    
    handler.assert_called_once_with(x=10, y=20)

def test_event_unsubscription():
    event_bus = EventBus()
    handler = Mock()
    
    unsubscribe = event_bus.subscribe('test_event', handler)
    unsubscribe()
    event_bus.emit('test_event')
    
    handler.assert_not_called()
```

**Terminal Abstraction for Testability:**
```python
# src/ui/terminal.py
class TerminalInterface:
    """Abstract terminal interface for testing"""
    def move(self, x: int, y: int) -> str:
        raise NotImplementedError
    
    def color_rgb(self, r: int, g: int, b: int) -> str:
        raise NotImplementedError
    
    def render_char(self, x: int, y: int, char: str, fg=None, bg=None):
        raise NotImplementedError

class BlessedTerminal(TerminalInterface):
    """Real terminal implementation"""
    def __init__(self, term: Terminal):
        self.term = term
    
    def move(self, x: int, y: int) -> str:
        return self.term.move(y, x)
    
    def color_rgb(self, r: int, g: int, b: int) -> str:
        return self.term.color_rgb(r, g, b)

class MockTerminal(TerminalInterface):
    """Mock terminal for testing"""
    def __init__(self):
        self.buffer = {}
        self.cursor = (0, 0)
    
    def render_char(self, x: int, y: int, char: str, fg=None, bg=None):
        self.buffer[(x, y)] = {'char': char, 'fg': fg, 'bg': bg}
```

### Phase 2: UI Components with Colors (Week 2)

#### 2.1 Color System Tests
```python
# tests/unit/test_colors.py
def test_rgb_color_creation():
    color = RGBColor(255, 128, 0)  # Orange
    assert color.r == 255
    assert color.g == 128
    assert color.b == 0
    assert color.to_hex() == "#FF8000"

def test_color_palette():
    palette = ColorPalette()
    # Define game-specific colors
    assert palette.MAGE_BLUE == RGBColor(100, 150, 255)
    assert palette.DIVINE_GOLD == RGBColor(255, 215, 0)
    assert palette.MONSTER_RED == RGBColor(200, 50, 50)

def test_terminal_color_rendering(mock_terminal):
    renderer = Renderer(mock_terminal)
    renderer.draw_colored_char(10, 10, '@', RGBColor(255, 0, 0))
    
    assert mock_terminal.buffer[(10, 10)]['char'] == '@'
    assert mock_terminal.buffer[(10, 10)]['fg'] == RGBColor(255, 0, 0)
```

#### 2.2 Scrollable Message Pane Tests
```python
# tests/unit/test_message_pane.py
def test_message_pane_scrolling():
    pane = MessagePane(width=40, height=5)
    
    # Add more messages than can fit
    for i in range(10):
        pane.add_message(f"Message {i}")
    
    # Should show last 5 messages
    visible = pane.get_visible_messages()
    assert len(visible) == 5
    assert visible[0] == "Message 5"
    assert visible[4] == "Message 9"

def test_message_pane_scrollback():
    pane = MessagePane(width=40, height=5, max_history=100)
    
    # Add many messages
    for i in range(20):
        pane.add_message(f"Message {i}")
    
    # Scroll up
    pane.scroll_up(5)
    visible = pane.get_visible_messages()
    assert visible[0] == "Message 10"
```

### Phase 3: Procedural Generation (Weeks 3-4)

#### 3.1 Map Generation Tests with Hypothesis
```python
# tests/unit/test_map_generation.py
from hypothesis import given, strategies as st

@given(
    width=st.integers(min_value=20, max_value=100),
    height=st.integers(min_value=20, max_value=50),
    seed=st.integers()
)
def test_map_generation_properties(width, height, seed):
    """Property-based testing for map generation"""
    generator = MapGenerator(seed=seed)
    level = generator.generate(width, height)
    
    # Properties that must always hold
    assert level.width == width
    assert level.height == height
    assert level.has_connected_path()  # All areas reachable
    assert level.has_stairs_up()
    assert level.has_stairs_down()
    assert 0.3 <= level.wall_ratio() <= 0.5  # Reasonable wall density

def test_dungeon_connectivity():
    """Ensure all rooms are connected"""
    generator = DungeonGenerator(seed=42)
    level = generator.generate(80, 24)
    
    # Use flood fill from starting position
    reachable = level.get_reachable_tiles(level.player_start)
    total_walkable = level.count_walkable_tiles()
    
    assert reachable == total_walkable
```

#### 3.2 Resource Placement Tests
```python
# tests/unit/test_resource_placement.py
def test_resource_distribution():
    level = Level(80, 24)
    placer = ResourcePlacer(seed=42)
    
    placer.place_resources(level, {
        'iron_ore': 10,
        'wood': 15,
        'magic_crystal': 3
    })
    
    # Verify placement
    assert level.count_resource('iron_ore') == 10
    assert level.count_resource('wood') == 15
    assert level.count_resource('magic_crystal') == 3
    
    # Verify no overlapping resources
    resource_positions = level.get_resource_positions()
    assert len(resource_positions) == len(set(resource_positions))
```

### Phase 4: Entity System & AI (Weeks 5-6)

#### 4.1 Entity Component System Tests
```python
# tests/unit/test_entities.py
def test_entity_creation():
    entity = Entity()
    
    # Add components
    entity.add_component(Position(10, 20))
    entity.add_component(Health(100))
    entity.add_component(AI(behavior='mage'))
    
    # Verify components
    assert entity.get_component(Position).x == 10
    assert entity.get_component(Health).current == 100
    assert entity.has_component(AI)

def test_entity_system_processing():
    world = World()
    
    # Create entities
    mage1 = world.create_entity()
    mage1.add_component(Position(5, 5))
    mage1.add_component(Velocity(1, 0))
    
    # Add movement system
    movement_system = MovementSystem()
    world.add_system(movement_system)
    
    # Process one tick
    world.update(1.0)
    
    # Verify movement
    assert mage1.get_component(Position).x == 6
```

#### 4.2 AI Behavior Tests
```python
# tests/unit/test_ai_behaviors.py
def test_mage_resource_gathering():
    """Test mage AI for resource gathering"""
    world = create_test_world()
    mage = create_mage(world, x=10, y=10)
    
    # Place resource nearby
    world.add_resource(12, 10, 'iron_ore')
    
    # Run AI
    ai_system = AISystem()
    ai_system.process(mage, world)
    
    # Mage should move toward resource
    assert mage.get_component(Task).type == 'gather'
    assert mage.get_component(Task).target == (12, 10)

def test_mage_social_interaction():
    """Test mage social behaviors"""
    world = create_test_world()
    mage1 = create_mage(world, x=10, y=10, personality='friendly')
    mage2 = create_mage(world, x=11, y=10, personality='grumpy')
    
    # Trigger interaction
    social_system = SocialSystem()
    interaction = social_system.check_interaction(mage1, mage2)
    
    assert interaction is not None
    assert interaction.type in ['greeting', 'argument', 'trade']
```

### Phase 5: OpenAI Integration (Week 7)

#### 5.1 Mocked OpenAI Tests
```python
# tests/fixtures/mock_openai.py
class MockOpenAIClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_count = 0
    
    async def generate_backstory(self, mage_data):
        self.call_count += 1
        return self.responses.get('backstory', 
            "A humble mage from the northern villages.")
    
    async def generate_dialogue(self, context):
        self.call_count += 1
        return self.responses.get('dialogue',
            "Greetings, fellow mage!")

# tests/unit/test_openai_integration.py
@pytest.mark.asyncio
async def test_backstory_generation():
    client = MockOpenAIClient({
        'backstory': "Born under a blood moon, this mage..."
    })
    
    mage = create_mage()
    narrator = Narrator(client)
    
    backstory = await narrator.generate_backstory(mage)
    assert "blood moon" in backstory
    assert client.call_count == 1

@pytest.mark.asyncio
async def test_dialogue_generation_with_retry():
    # Test retry logic on failure
    client = MockOpenAIClient()
    client.generate_dialogue = Mock(side_effect=[
        Exception("API Error"),
        "Success on retry"
    ])
    
    dialogue_sys = DialogueSystem(client, max_retries=2)
    result = await dialogue_sys.generate(context={})
    
    assert result == "Success on retry"
    assert client.generate_dialogue.call_count == 2
```

### Phase 6: Performance Testing

#### 6.1 Rendering Performance Tests
```python
# tests/performance/test_rendering_speed.py
def test_turn_resolution_time(benchmark, mock_terminal):
    """Ensure turn resolves quickly for responsive gameplay"""
    game = create_test_game(mock_terminal)
    
    # Populate with many entities
    for i in range(100):
        create_mage(game.world, x=i%80, y=i//80)
    
    # Benchmark turn resolution
    result = benchmark(game.process_turn, 'w')  # Player moves up
    
    # Must resolve turn in under 100ms for responsiveness
    assert result.stats['mean'] < 0.100  # 100ms for turn resolution

def test_partial_rendering_efficiency(benchmark):
    """Test that only changed tiles are redrawn per turn"""
    renderer = Renderer(MockTerminal())
    level = create_test_level()
    
    # Initial full render
    renderer.render_full(level)
    
    # Move one entity
    level.move_entity(0, 0, 1, 0)
    
    # Benchmark partial update
    def partial_update():
        changed_tiles = level.get_changed_tiles()
        renderer.render_tiles(changed_tiles)
    
    result = benchmark(partial_update)
    
    # Should be very fast since only 2 tiles changed
    assert result.stats['mean'] < 0.001
    assert len(level.get_changed_tiles()) == 2  # Old and new position
```

#### 6.2 AI Scalability Tests
```python
# tests/performance/test_ai_scalability.py
@pytest.mark.parametrize("num_mages", [10, 50, 100, 200])
def test_ai_performance_scaling(benchmark, num_mages):
    """Test AI system performance with many mages"""
    world = create_large_world(200, 200)
    
    # Create many mages
    for i in range(num_mages):
        create_mage(world, x=i*2%200, y=i*2//200)
    
    ai_system = AISystem()
    
    # Benchmark AI update
    result = benchmark(ai_system.update_all, world)
    
    # Turn processing should scale linearly
    # 100 mages should resolve in < 50ms
    if num_mages <= 100:
        assert result.stats['mean'] < 0.05
```

## Testing Best Practices

### 1. Test Organization
- One test file per module
- Group related tests in classes
- Use descriptive test names that explain the behavior

### 2. Test Data Management
```python
# tests/fixtures/game_states.py
@pytest.fixture
def empty_world():
    return World(width=80, height=24)

@pytest.fixture
def populated_world():
    world = World(width=80, height=24)
    # Add standard test entities
    for i in range(5):
        create_mage(world, x=i*10, y=10)
    return world

@pytest.fixture
def combat_scenario():
    """Pre-configured combat scenario for testing"""
    world = World(width=40, height=20)
    player = create_player(world, x=20, y=10)
    monster = create_monster(world, x=25, y=10, type='goblin')
    return world, player, monster
```

### 3. Async Testing Patterns
```python
# For OpenAI integration
@pytest.fixture
async def mock_openai_client():
    client = AsyncMock()
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    )
    return client

@pytest.mark.asyncio
async def test_async_dialogue(mock_openai_client):
    dialogue = DialogueSystem(mock_openai_client)
    response = await dialogue.generate("Hello")
    assert response == "Test response"
```

### 4. Performance Testing Guidelines
- Set clear performance budgets
- Test with realistic data volumes
- Use parametrized tests for scaling
- Profile bottlenecks when tests fail

### 5. Integration Testing Strategy
```python
# tests/integration/test_game_loop.py
def test_full_game_tick():
    """Test complete game update cycle"""
    game = Game()
    
    # Simulate player input
    game.handle_input('w')  # Move up
    
    # Process turn
    game.process_turn()  # All entities act
    
    # Verify state changes
    assert game.player.y == 9  # Moved up
    assert len(game.messages) > 0  # Generated message
    assert game.world.turn_count == 1
```

## CI/CD Configuration

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=html --cov-report=term
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ --benchmark-only
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      
    - name: Check code quality
      run: |
        black --check src/ tests/
        flake8 src/ tests/
        mypy src/
```

## Development Workflow

### Daily TDD Cycle
1. **Morning Planning**
   - Review feature_status.md
   - Select next feature to implement
   - Write acceptance criteria

2. **Test Writing (30-45 min)**
   - Write failing unit tests
   - Write integration test skeleton
   - Define interfaces through tests

3. **Implementation (1-2 hours)**
   - Implement minimal code to pass tests
   - Focus on one test at a time
   - Commit after each passing test

4. **Refactoring (30 min)**
   - Improve code structure
   - Extract common patterns
   - Ensure all tests still pass

5. **Integration (30 min)**
   - Run full test suite
   - Update documentation
   - Update feature_status.md

### Code Review Checklist
- [ ] All new code has tests
- [ ] Tests are meaningful and test behavior, not implementation
- [ ] Code coverage is maintained above 80%
- [ ] Performance tests pass for affected systems
- [ ] No hardcoded values (use constants or config)
- [ ] Error handling is tested
- [ ] Documentation is updated

## Testing Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_map_generation.py

# Run tests matching pattern
pytest -k "test_mage"

# Run performance tests
pytest tests/performance/ --benchmark-only

# Run tests in parallel
pytest -n auto

# Run with verbose output
pytest -v

# Run only marked tests
pytest -m "slow"  # Run slow tests
pytest -m "not slow"  # Skip slow tests
```

## Testing Turn-Based Mechanics

### 1. Turn Order Testing
```python
def test_turn_order_resolution():
    """Ensure entities act in correct order"""
    world = create_test_world()
    
    # Create entities with different speeds
    fast_mage = create_mage(world, speed=10)
    slow_mage = create_mage(world, speed=5)
    player = create_player(world)
    
    # Process turn
    turn_log = world.process_turn('wait')
    
    # Verify order: player first, then by speed
    assert turn_log[0].entity == player
    assert turn_log[1].entity == fast_mage
    assert turn_log[2].entity == slow_mage
```

### 2. State Immutability Between Turns
```python
def test_no_state_changes_between_turns():
    """Verify nothing changes without player input"""
    game = create_test_game()
    initial_state = game.get_state_snapshot()
    
    # Wait without input
    time.sleep(1.0)
    
    # State should be identical
    assert game.get_state_snapshot() == initial_state
```

### 3. Action Economy Testing
```python
def test_multi_turn_actions():
    """Test actions that take multiple turns"""
    game = create_test_game()
    player = game.player
    
    # Start a multi-turn spell
    game.process_turn('cast_ritual')  # 3-turn ritual
    assert player.is_busy()
    assert player.turns_remaining == 3
    
    # Continue casting
    game.process_turn('continue')
    assert player.turns_remaining == 2
    
    # Complete spell
    game.process_turn('continue')
    game.process_turn('continue')
    assert not player.is_busy()
    assert 'Ritual complete' in game.messages
```

### 4. Turn Performance Scaling
```python
@pytest.mark.parametrize("entity_count", [10, 50, 100, 200])
def test_turn_performance_scaling(benchmark, entity_count):
    """Ensure turn resolution scales well"""
    world = create_large_world()
    
    # Create many entities
    for i in range(entity_count):
        create_mage(world, x=i%100, y=i//100)
    
    # Benchmark turn processing
    result = benchmark(world.process_turn, 'wait')
    
    # Should complete within target time
    assert result.stats['mean'] < 0.100  # 100ms target
```

## Common Testing Patterns

### 1. Testing Random/Procedural Systems
```python
def test_deterministic_generation():
    """Ensure same seed produces same result"""
    gen1 = MapGenerator(seed=42)
    gen2 = MapGenerator(seed=42)
    
    map1 = gen1.generate(50, 50)
    map2 = gen2.generate(50, 50)
    
    assert map1.to_string() == map2.to_string()
```

### 2. Testing Time-Based Features
```python
from freezegun import freeze_time

@freeze_time("2024-01-01 12:00:00")
def test_spell_cooldown():
    spell = DivineSpell('smite', cooldown=5.0)
    
    spell.cast()
    assert not spell.can_cast()  # On cooldown
    
    with freeze_time("2024-01-01 12:00:05"):
        assert spell.can_cast()  # Cooldown expired
```

### 3. Testing UI Updates
```python
def test_ui_message_with_color():
    ui = GameUI(MockTerminal())
    
    ui.add_message("Critical hit!", color=RGBColor(255, 0, 0))
    ui.render()
    
    # Verify colored message was rendered
    rendered = ui.terminal.get_rendered_text()
    assert "Critical hit!" in rendered
    assert ui.terminal.color_used == RGBColor(255, 0, 0)
```

## Conclusion

This TDD workflow ensures high-quality, maintainable code throughout the development of MageMines. By writing tests first, we define clear interfaces and behavior expectations, making the codebase more modular and easier to extend. The comprehensive testing strategy covers unit, integration, and performance testing, ensuring the game meets its ambitious goals while maintaining responsive turn-based gameplay.

The turn-based architecture simplifies many aspects of development:
- No complex timing or animation systems needed
- Easier to test deterministic turn resolution
- Clear action economy and game flow
- Efficient rendering through change tracking
- Better accessibility through unlimited thinking time