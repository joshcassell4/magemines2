# MageMines Feature Status

Last Updated: 2025-07-27

## Overview

MageMines is a terminal-based god-game combining elements from Dwarf Fortress, D&D, and Populous. The player controls divine powers to guide and assist AI-controlled mages who gather resources, craft items, fight monsters, and interact socially.

## Core Requirements

- [x] Basic game loop with player movement
- [x] Terminal rendering with blessed library
- [x] RGB color support for rich visuals ⚡ **COMPLETED** (Phase 2)
- [x] Procedural map generation (NetHack-style) ⚡ **COMPLETED** (Phase 3)
- [x] Multiple dungeon levels ⚡ **COMPLETED** (Phase 3)
- [ ] AI-controlled mage entities (Phase 4 - Not Started)
- [ ] OpenAI integration for backstories and dialogue (Phase 6 - Not Started)
- [ ] Divine spell system (Phase 5 - Not Started)
- [ ] Resource gathering and crafting (Phase 7 - Not Started)
- [ ] Magic item generation (Phase 8 - Not Started)
- [x] Scrollable message/dialogue pane ⚡ **COMPLETED** (Phase 2)
- [x] Performance optimization (no flicker/lag during turn updates) ⚡ **COMPLETED** (Phase 2)
- [x] Loading indicators for async operations ⚡ **COMPLETED** (Phase 2)

## Development Phases

### Phase 1: Foundation & Testing Infrastructure
**Status**: Completed  
**Target**: Week 1
**Completion Date**: 2025-07-24

- [x] Basic game structure exists
- [x] Create workflow.md with TDD strategy
- [x] Create feature_status.md
- [x] Set up .env file and update .gitignore
- [x] Add testing framework (pytest, pytest-mock, etc.)
- [x] Create terminal abstraction layer for testing
- [x] Implement event system ⚡ **COMPLETED** (Started: 2025-07-24, Completed: 2025-07-24)
- [x] Create game state management ⚡ **COMPLETED** (Started: 2025-07-24, Completed: 2025-07-24)
- [ ] ~~Set up CI/CD with GitHub Actions~~ (Skipped for now)

### Phase 2: Enhanced UI with Colors
**Status**: Completed  
**Target**: Week 2  
**Completion Date**: 2025-07-25

- [x] Implement RGB color system using blessed ⚡ **COMPLETED** (Started: 2025-07-25, Completed: 2025-07-25)
- [x] Create color palette for game elements ⚡ **COMPLETED** (2025-07-25)
  - [x] Mage colors (blue shades)
  - [x] Divine spell effects (gold/white)
  - [x] Monster colors (red/purple)
  - [x] Resource colors (earth tones)
  - [x] UI chrome colors
- [x] Implement scrollable message pane ⚡ **COMPLETED** (Started: 2025-07-24, Completed: 2025-07-24)
  - [x] Message history buffer (1000 message limit)
  - [x] Scroll controls (-/+ keys)
  - [x] Message categories/filtering
  - [x] Color-coded messages
  - [x] Turn tick prefixes ([T#] for non-system messages)
  - [x] Input buffer overflow prevention (0.01s timeout)
  - [x] Larger message pane (8 lines) for AI dialogue
  - [x] Side-by-side layout (map left, messages right)
  - [x] Adaptive layout for different terminal sizes
  - [x] Descriptive movement blocking messages
- [x] Add loading/processing indicators ⚡ **COMPLETED** (Started: 2025-07-25, Completed: 2025-07-25)
  - [x] Async operation overlay with multiple styles (spinner, dots, progress bar)
  - [x] Progress bars with percentage display
  - [x] Input locking during processing
  - [x] Demo keys: l (spinner), p (progress), d (dots), c (cancel)
- [x] Optimize rendering pipeline ⚡ **COMPLETED** (Started: 2025-07-25, Completed: 2025-07-28)
  - [x] Changed tile tracking per turn
  - [x] Partial screen updates only
  - [x] Efficient turn-based rendering
  - [x] Message pane caching and incremental updates
  - [x] Header bar with stats display (turn counter)
  - [x] Only redraw changed portions of UI
  - [x] **Advanced Performance Optimizations** ⚡ **COMPLETED** (2025-07-28)
    - [x] Double buffering system with dirty region tracking
    - [x] Batch renderer for minimizing terminal I/O operations
    - [x] Color cache to avoid repeated RGB conversions
    - [x] Optimized message pane showing only current turn messages
    - [x] Message log viewer overlay (L key) for viewing full history
    - [x] OptimizedGameMap with per-tile change tracking
    - [x] Entity position tracking with minimal redraws
    - [x] Zero full-screen redraws during normal gameplay
    - [x] 80-90% reduction in terminal I/O operations

### Phase 3: Procedural World Generation
**Status**: Completed  
**Target**: Weeks 3-4
**Started**: 2025-07-25
**Completed**: 2025-07-25

- [x] Implement level generation algorithms ⚡ **COMPLETED** (2025-07-25)
  - [x] Room and corridor generation
  - [x] Dungeon connectivity validation (fixed isolated room bug)
  - [x] Multiple generation themes (Dungeon, Cave, Town)
  - [x] Diagonal corridor support with Bresenham's algorithm
  - [x] Configurable corridor styles (L-shaped vs diagonal)
  - [x] Minimum spanning tree connectivity guarantee
- [x] Multi-level dungeon system ⚡ **COMPLETED** (2025-07-25)
  - [x] Level transitions (stairs up/down with < and > keys)
  - [x] Level persistence (levels remain when revisited)
  - [x] Depth-based difficulty (more rooms, larger rooms, more complex layouts)
  - [x] DungeonLevel class for level representation
  - [x] LevelManager for multi-level coordination
  - [x] Town on level 1, caves every 5 levels, dungeons elsewhere
  - [x] Proper spawn positions when changing levels
  - [x] Header bar shows current depth
  - [x] Messages inform player about stairs
- [ ] Resource distribution system
  - [ ] Resource types definition
  - [ ] Placement algorithms
  - [ ] Rarity tiers
- [x] Environmental features (Partially Complete)
  - [x] Doors ⚡ **COMPLETED** (2025-07-25)
    - [x] Door placement in dungeons (20% chance per room)
    - [x] Door placement in towns (all buildings have doors)
    - [x] Door opening command ('o' key)
    - [x] Doors block movement until opened
    - [x] Fixed door connectivity issues in town generation
    - [x] Informative messages when bumping into doors
  - [ ] Traps
  - [ ] Special rooms (temples, libraries)
  - [ ] Destructible terrain

### Phase 4: Entity System & Mage AI
**Status**: In Progress ⚡ **STARTED** (2025-07-27)  
**Target**: Weeks 5-6

- [x] Entity Component System (ECS) ⚡ **COMPLETED** (2025-07-27)
  - [x] Core components (Position, Health, Inventory, Renderable, Stats, Name)
  - [x] AI components (Behavior states, Task targeting, Memory storage)
  - [x] Magic components (MagicUser, Spell, MagicEffect)
  - [x] Social components (Faction with reputation tracking)
  - [x] Entity manager with component indexing
  - [x] Spatial entity tracking in GameMap
- [x] Mage types implemented ⚡ **COMPLETED** (2025-07-27)
  - [x] Apprentice Mage (friendly, weak, cyan 'a')
  - [x] Elemental Mage (fire/ice/lightning variants, territorial, colored 'M')
  - [x] Ancient Scholar (high wisdom, utility spells, purple 'S')
  - [x] Mad Hermit (unpredictable, random spells, purple 'h')
  - [x] Archmage (boss-level, multiple schools, magenta 'A')
- [x] Mage AI behaviors ⚡ **COMPLETED** (2025-07-27)
  - [x] Basic behavior state machine (idle, patrol, study, erratic, boss, flee, attack, cast)
  - [x] Turn-based AI processing after player moves
  - [x] Movement with collision detection
  - [x] Hostile faction detection and engagement
  - [ ] Task prioritization system (need-based AI)
  - [ ] Resource gathering behaviors
  - [ ] Pathfinding (A*) - currently using simple movement
  - [x] Combat behaviors (approach and cast spells)
  - [x] Fleeing/self-preservation
- [ ] Social interaction system
  - [x] Faction system with hostility levels
  - [x] Reputation tracking between entities
  - [ ] Conversation triggers
  - [ ] Trade negotiations
  - [ ] Group dynamics
- [x] Magic system foundation ⚡ **COMPLETED** (2025-07-27)
  - [x] 13 spells across 4 schools (arcane, elemental, nature, dark)
  - [x] Spell properties (mana cost, range, cast time, cooldowns)
  - [x] Mana pools and regeneration
  - [x] Spell casting state machine
  - [ ] Actual spell effects (damage, healing, buffs, debuffs)
- [ ] Mage progression
  - [x] Basic stats system (strength, intelligence, dexterity, wisdom)
  - [ ] Skill advancement
  - [ ] Experience/leveling
  - [ ] Specializations

### Phase 5: Divine Powers & Spells
**Status**: Not Started  
**Target**: Week 7

- [ ] Divine spell system
  - [ ] Spell definitions and effects
  - [ ] Area of effect calculations
  - [ ] Mana/divine power resource
  - [ ] Cooldown management
- [ ] Spell categories
  - [ ] Direct intervention (healing, smite)
  - [ ] Environmental (weather, terrain)
  - [ ] Influence (inspire, fear)
  - [ ] Information (reveal, scry)
- [ ] Spell targeting
  - [ ] Single target
  - [ ] Area effects
  - [ ] Global effects
- [ ] Visual feedback
  - [ ] Spell animations (ASCII)
  - [ ] Color effects
  - [ ] Screen shake/effects

### Phase 6: OpenAI Integration
**Status**: Not Started  
**Target**: Week 8

- [ ] OpenAI client wrapper
  - [ ] API key management
  - [ ] Request queuing
  - [ ] Error handling/retry
  - [ ] Token usage tracking
- [ ] Backstory generation
  - [ ] Mage history templates
  - [ ] Personality generation
  - [ ] Name generation
  - [ ] Relationship generation
- [ ] Dynamic dialogue
  - [ ] Context building
  - [ ] Conversation flow
  - [ ] Memory integration
  - [ ] Personality consistency
- [ ] UI integration
  - [ ] Loading indicators
  - [ ] Message formatting
  - [ ] Conversation history

### Phase 7: Resources & Crafting
**Status**: In Progress ⚡ **STARTED** (2025-07-27)
**Target**: Week 9

- [x] Resource types ⚡ **COMPLETED** (2025-07-27)
  - [x] Basic materials (wood, stone, ore)
  - [x] Magic materials (crystals, essence)
  - [x] Food/consumables (mushrooms, herbs)
- [x] Basic gathering mechanics ⚡ **COMPLETED** (2025-07-27)
  - [x] Resource placement in map generation
    - [x] Dynamic resource density based on depth (2% base + 10% per level)
    - [x] Resource clustering algorithm (60% chance to cluster near existing resources)
    - [x] Resource type selection based on rarity tiers
    - [x] All 7 resource types: Wood, Stone, Ore, Crystal, Essence, Mushrooms, Herbs
  - [x] 'g' key to gather resources
  - [x] Resource removal from map when gathered
  - [x] Resource display on map with unique symbols
  - [ ] Tool requirements
  - [ ] Skill-based yields
  - [ ] Resource depletion
- [ ] Crafting system
  - [ ] Recipe definitions
  - [ ] Crafting stations
  - [ ] Quality levels
  - [ ] Failure chances
- [x] Item management ⚡ **COMPLETED** (2025-07-27)
  - [x] Inventory system (Completed - 2025-07-27)
    - [x] Entity Component System integration
    - [x] 20-slot inventory with capacity management
    - [x] Resource stacking with per-type stack limits
    - [x] Overflow handling when inventory is full
    - [x] Add/remove resource operations
    - [x] Resource counting and empty/full state tracking
  - [x] Inventory UI overlay (toggleable with 'i' key)
    - [x] Centered box display with borders
    - [x] Resource grouping by type
    - [x] Color-coded resource display
    - [x] Current count and stack limit display
  - [x] Item stacking (part of inventory system)
  - [ ] Storage containers
  - [ ] Item decay

### Phase 8: Combat & Magic Items
**Status**: Not Started  
**Target**: Week 10

- [ ] Combat system
  - [ ] Turn-based resolution
  - [ ] Damage calculations
  - [ ] Status effects
  - [ ] Death/respawn
- [ ] Monster entities
  - [ ] Monster types
  - [ ] AI behaviors
  - [ ] Loot tables
  - [ ] Spawning system
- [ ] Magic item generation
  - [ ] Item properties
  - [ ] Rarity tiers
  - [ ] Procedural naming
  - [ ] Cursed items
- [ ] Equipment system
  - [ ] Equipment slots
  - [ ] Stat modifications
  - [ ] Set bonuses
  - [ ] Item identification

### Phase 9: Save/Load & Persistence
**Status**: Not Started  
**Target**: Week 11

- [ ] Save/Load System
  - [ ] Game state serialization
  - [ ] Player inventory persistence
  - [ ] Entity state saving
  - [ ] Map state preservation
- [ ] Level Serialization
  - [ ] Level data compression
  - [ ] Disk-based level storage
  - [ ] LRU cache for active levels
  - [ ] Lazy loading of distant levels
- [ ] Save File Management
  - [ ] Multiple save slots
  - [ ] Autosave functionality
  - [ ] Save file versioning
  - [ ] Save corruption detection
- [ ] Cloud Save Support (Future)
  - [ ] Steam Cloud integration
  - [ ] Cross-platform saves
  - [ ] Save sync conflict resolution

## Technical Architecture

### Project Structure
```
src/magemines/
├── core/          # Foundation (terminal, events, state)
├── game/          # Game logic (loop, map, entities)
├── ui/            # UI components (messages, header, overlays)
└── __main__.py    # Entry point
```

### Architectural Strengths (from Code Review)
- Clean, modular architecture with clear separation of concerns
- Robust terminal abstraction layer enabling comprehensive testing
- Feature-rich UI with color support, scrollable message pane, and loading indicators
- Sophisticated procedural map generation with multiple algorithms
- Excellent terminal rendering optimization (partial updates only)
- Strong testing infrastructure with both unit and integration tests
- Event-driven architecture foundation in place

### Areas for Improvement (from Code Review)
- Missing service layer for AI/OpenAI integration
- No clear data/persistence layer
- Configuration scattered across modules
- Monolithic game_loop.py (225 lines) needs refactoring
- Large map_generator.py (800+ lines) needs splitting
- Many ad-hoc test files need organization
- No seed management for reproducible generation
- Missing error recovery mechanisms

### Core Systems
- **Turn-Based Game Loop**: Player input → World update → Entity actions → Render
- **Event System**: Decoupled communication between game systems  
- **Entity Component System**: Placeholder - needs full implementation
- **Terminal Abstraction**: Testable rendering layer
- **State Management**: Centralized game state (save/load not implemented)
- **Action Queue**: Turn order and action resolution system (not implemented)

### Performance Requirements
- **Turn Resolution**: < 100ms for responsive gameplay
- **Entity Count**: Support 100+ active entities per turn
- **Memory**: < 500MB RAM usage
- **Rendering**: Partial updates only (no full redraws)
- **Input Response**: Immediate input acknowledgment
- **AI Processing**: All entity decisions within turn budget

### Testing Requirements
- **Unit Test Coverage**: > 80%
- **Integration Tests**: Full game loop testing
- **Performance Tests**: Automated benchmarks
- **CI/CD**: Automated testing on push

### Testing Infrastructure Status
- Good unit test coverage for core systems
- Terminal abstraction enables UI testing without real terminal
- **Issue**: Many ad-hoc test files in root test directory need organization
- **Recommendation**: Move experimental tests to `tests/playground/` or `tests/experiments/`
- Missing performance benchmarks despite requirements

## Known Issues

### Fixed Issues
- ~~Recursion depth error when going below certain dungeon levels~~ **FIXED** (2025-07-25)
  - Converted recursive flood fill algorithms to iterative approach using deque
  - Tested successfully up to level 30 and with 100x100 maps
- ~~Town connectivity issues with isolated buildings~~ **FIXED** (2025-07-27)
  - Towns now place 2-3 doors per building (was 1)
  - Added post-generation connectivity checking with flood fill
  - Automatic path creation between disconnected regions
  - Added perimeter roads and cross roads for better connectivity
  - Tested with 100% connectivity success rate
- ~~Resource symbol conflicts~~ **FIXED** (2025-07-27)
  - Stone resource was using '*' which conflicted with altar symbol
  - Changed stone symbol to 's' across all files
  - All resources now have unique visual representations
- ~~Unicode character compatibility~~ **FIXED** (2025-07-27)
  - Converted all Unicode symbols to ASCII for better terminal compatibility
  - Altar: ▲ → ^, Chest: □ → $, Lava: ≈ → %
  - Crystal/Essence: ♦/◊ → *, Mushroom: ♠ → m, Herbs: ♣ → h
  - Added special handling for crystal/essence disambiguation using TileType
  - Game now runs properly in all terminal environments

### Critical Issues (from Code Review)
1. **Memory Management**: LevelManager keeps all visited levels in memory indefinitely
   - **Solution**: Implement LRU cache for levels, serialize distant levels to disk
   
2. **Missing Core Gameplay**: Current implementation is a dungeon crawler without god-game mechanics
   - **Priority**: Entity Component System → Basic mage AI → Divine intervention → Resources → Combat
   
3. **Error Handling**: Many functions lack proper error handling
   - File I/O operations, terminal operations, map generation edge cases need attention
   
4. **Performance Concerns**:
   - No profiling or optimization for large maps
   - Dijkstra's algorithm used for all connectivity checks
   - No spatial partitioning for entity queries

### Next Steps for Mage System (2025-07-27)

1. **Complete Spell Effects Implementation** ⚡ **PARTIALLY COMPLETED** (2025-07-29)
   - ✅ Implement damage calculation and health reduction
   - ✅ Add healing effects for nature spells
   - ✅ Add spell visual feedback in message pane
   - ✅ Add player Health component (100 HP)
   - ✅ Death handling and entity removal
   - Create buff/debuff system (shields, slows, curses)
   - Implement area-of-effect damage for fireball
   - Add teleportation mechanics

2. **Enhance AI Behaviors**
   - Implement A* pathfinding to replace simple movement
   - Add need-based AI (mana management, health awareness)
   - Create mage-to-mage interactions (helping allies, group tactics)
   - Implement resource gathering behaviors for mages
   - Add dialogue triggers when player is near friendly mages

3. **Combat System**
   - Add health display in entity rendering
   - Implement death and entity removal
   - Create loot drops from defeated mages
   - Add combat messages to message pane
   - Implement player combat abilities (currently player can't fight back)

4. **Magic Item & Spell Learning**
   - Create spell scrolls as loot items
   - Implement spell teaching from Ancient Scholars
   - Add spell trading between mages
   - Create magical artifacts that boost mage abilities

5. **Performance & Polish**
   - Optimize entity rendering (only redraw moved entities)
   - Add mage spawn limits based on dungeon depth
   - Create mage spawn points in special rooms
   - Balance mana costs and spell power
   - Add spell particle effects using ASCII animation

### Immediate Priorities (Next Sprint - from Review)
1. **~~Implement Entity Component System~~** ✅ COMPLETED
   - ~~Create base Entity class with components~~
   - ~~Position, Renderable, AI, Inventory components~~
   - ~~Entity manager with spatial indexing~~

2. **~~Basic Mage AI~~** ✅ MOSTLY COMPLETED
   - ~~Simple behavior state machine~~
   - A* pathfinding implementation (still needed)
   - ~~Basic combat and spell casting~~

3. **Divine Intervention Framework** (Next Phase)
   - Spell targeting system for player
   - Area-of-effect calculations
   - Divine power resource (separate from mage mana)

4. **Configuration System**
   - Centralized game settings
   - Difficulty parameters
   - Debug options

## Future Enhancements

### Original Roadmap
- **Multiplayer**: Multiple gods competing/cooperating
- **Mod Support**: Lua scripting for custom content
- **Advanced AI**: Neural network-based mage behaviors
- **Procedural Quests**: Dynamic story generation
- **Voice Acting**: AI-generated mage voices
- **Graphical Mode**: Optional tile-based renderer

### Additional Features (from Code Review)

#### Gameplay Features
1. **Mage Personalities & Traits**
   - Personality system affecting behavior
   - Traits that modify abilities
   - Relationship dynamics between mages

2. **Dynamic Events**
   - Random events (cave-ins, discoveries)
   - Weather system affecting gameplay
   - Day/night cycle

3. **Progression Systems**
   - Divine favor/reputation
   - Unlockable spells and abilities
   - Achievement system

4. **Advanced AI Features**
   - Mage learning from experiences
   - Group tactics and cooperation
   - Emergent storytelling from AI interactions

#### Technical Features
1. **Replay System**
   - Record and replay game sessions
   - Share interesting scenarios
   - Debug tool for AI behavior

2. **Enhanced Mod Support**
   - Plugin system for custom content
   - Lua scripting for game rules
   - Custom map generators

3. **Accessibility**
   - Screen reader support
   - Configurable color schemes
   - Input remapping

4. **Performance Optimizations**
   - Object pooling for entities
   - Lazy loading for game assets
   - Compression for saved levels
   - Cache pathfinding results
   - Implement dirty rectangle rendering

## Dependencies

### Current
- blessed==1.20.0 (terminal UI)
- openai (AI integration)
- Python >= 3.11

### Planned
- pytest (testing)
- pytest-mock (mocking)
- pytest-asyncio (async testing)
- pytest-benchmark (performance)
- hypothesis (property testing)
- python-dotenv (environment management)

## Configuration

### Environment Variables
```
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
GAME_SEED=random
DEBUG_MODE=false
```

### Game Settings
- Map dimensions: 80x24 (default)
- Message history: 1000 lines
- Max mages: 100
- Dungeon levels: 10

## Development Timeline (from Code Review)

### Estimated Timeline for Core Features
- **Entity System + Basic AI**: 2 weeks
- **Divine Spells + Resources**: 2 weeks  
- **Combat + Balancing**: 1 week
- **Polish + OpenAI**: 2 weeks

### Development Priority Order
1. **High Priority**: Entity system, basic AI, divine spells
2. **Medium Priority**: Resource system, combat, save/load
3. **Low Priority**: OpenAI integration, advanced AI, multiplayer

## Project Summary

**Current Status**: Phases 1-3 Completed, Phase 4 In Progress (Entity System & Mage AI)

**Recent Progress (2025-07-28)**:
- **Major Performance Overhaul**: Implemented advanced rendering optimizations
  - Double buffering with dirty region tracking eliminates flicker
  - Batch rendering reduces terminal I/O by 80-90%
  - Color caching avoids repeated RGB conversions
  - OptimizedGameMap tracks per-tile changes and entity positions
  - Message pane now shows only current turn messages for better performance
  - Added message log viewer (L key) for viewing full message history
  - Achieved zero full-screen redraws during normal gameplay

**Previous Progress (2025-07-27)**:
- Implemented full Entity Component System with 10+ component types
- Created 5 different mage types with unique behaviors and abilities
- Built magic system foundation with 13 spells across 4 schools
- Implemented AI behavior state machine with 8 different behaviors
- Added faction and reputation system for social dynamics
- Integrated entities into game loop with turn-based processing
- Mages now spawn, move, and interact with the player

**Strengths**: The project now has a working entity system with intelligent mages that move around, cast spells (animations pending), and react to the player based on faction alignment. The foundation for the god-game mechanics is now in place. Performance has been massively improved with zero screen flicker, minimal terminal I/O, and efficient rendering that tracks only changed elements.

**Current Gap**: Spell effects are not yet implemented (mages cast spells but they don't actually do damage/healing), and the player still needs divine intervention abilities to truly make this a god-game.

**Next Steps**: Complete spell effect implementation, add combat resolution, then move to Phase 5 (Divine Powers) to give the player god-like abilities to influence their mages.

## Contributing

This project uses PlayTest-Driven Development. Please ensure:
1. Tests are sometimes written before implementing features
   but playtesting is more important because good playing is the most important
   important feature.
1.5 prefer writing unit tests to single file test scripts for code coverage.
2. Try to maintain >80% code coverage
2.5 Good playing is more important than good unit testing, but unit testing is important
   for concrete things and can be managed and organized easier than other types of testing.
3. Run performance benchmarks
4. Update this status document
5. Follow the TDD workflow in workflow.md if the feature warrants it, but remember good playing is the most important
   feature so don't let tests stop you from making the game good. 
6. Thank you in advance. You are important.

## Recent Fixes

### Message Persistence Fix (2025-01-27)
- Fixed issue where welcome messages and "You open the door" messages persisted across turns
- Changed door opening messages from SYSTEM to GENERAL category
- Updated message filtering to truly only show current turn messages
- Added explicit turn=0 for all startup messages (welcome, instructions, mage spawns)
- Now only messages from the current turn are displayed in the message pane

### Inventory Display Fix (2025-01-27)
- Fixed issue where closing inventory panel would clear the entire game screen
- Removed incorrect `did_full_redraw = True` setting after inventory toggle
- Let the async_manager handle redraw coordination properly
- Same fix applied to message log viewer toggle