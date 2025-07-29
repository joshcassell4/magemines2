# MageMines Product Requirements Document (PRD)

## Executive Summary

MageMines is a terminal-based roguelike god-game that combines elements from Dwarf Fortress, Dungeons & Dragons, and Populous. Players assume the role of a divine entity guiding a group of AI-controlled mages through procedurally generated dungeons. The game features rich character interactions powered by OpenAI, turn-based tactical gameplay, and emergent storytelling through simulation.

## Vision Statement

Create an immersive terminal-based roguelike where players experience the joy of divine intervention, watching their mages develop unique personalities, form relationships, and overcome challenges through a combination of their own initiative and the player's divine guidance.

## Core Concepts

### 1. Divine Player Role
- Players are invincible gods observing and guiding mages
- Cannot directly control mages, only influence through divine spells
- Success depends on mage survival and prosperity
- Focus on strategic intervention rather than micromanagement

### 2. Autonomous Mages
- Each mage has AI-generated backstory and personality
- Mages act independently based on their traits and needs
- Form relationships, rivalries, and alliances with other mages
- Learn and improve skills through experience

### 3. Emergent Storytelling
- Stories emerge from mage interactions and adventures
- AI-generated dialogue creates unique conversations
- Player actions influence but don't dictate narrative
- Each playthrough generates unique tales

## Game Mechanics

### Turn-Based System
- **Roguelike Time**: Time advances only when player acts
- **Action Economy**: Each divine spell costs action points
- **Turn Order**: Player → Environmental effects → Mages (by initiative) → Monsters
- **No Real-Time Elements**: Players have unlimited thinking time

### Divine Spells
- **Direct Intervention**
  - Healing: Restore mage health
  - Smite: Damage enemies threatening mages
  - Shield: Temporary protection
  - Teleport: Emergency evacuation

- **Environmental**
  - Weather Control: Rain, storms, sunshine
  - Terrain Shaping: Create/remove obstacles
  - Light/Darkness: Illuminate or obscure areas
  - Bless Ground: Create safe zones

- **Influence**
  - Inspire: Boost mage morale and skills
  - Fear: Terrify enemies
  - Calm: Reduce aggression and panic
  - Vision: Grant knowledge of distant areas

- **Information**
  - Scry: View distant locations
  - Divine Sight: Reveal hidden elements
  - Prophecy: Hints about future events
  - Know Alignment: Understand creature intentions

### Mage Behaviors

#### Basic Needs
- **Hunger**: Must find and consume food
- **Rest**: Require sleep to maintain effectiveness
- **Safety**: Seek shelter from threats
- **Social**: Desire interaction with other mages

#### Activities
- **Resource Gathering**: Wood, stone, ore, herbs, magical crystals
- **Crafting**: Tools, weapons, potions, magical items
- **Combat**: Fight monsters, defend territory
- **Exploration**: Map new areas, find treasures
- **Research**: Learn new spells and abilities

#### Social Dynamics
- **Relationships**: Friendship, romance, rivalry, mentorship
- **Communication**: Context-aware AI dialogue
- **Cooperation**: Team up for difficult tasks
- **Conflict**: Disputes over resources or ideology

### World Generation

#### Dungeon Levels
- **Procedural Generation**: NetHack-inspired algorithms
- **Themed Floors**: Caves, ruins, libraries, temples
- **Interconnected**: Multiple paths between levels
- **Persistent**: Changes remain between visits

#### Features
- **Rooms**: Various sizes and purposes
- **Corridors**: Connect rooms with tactical considerations
- **Stairs**: Up/down level transitions
- **Special Rooms**: Shops, shrines, treasure vaults
- **Environmental Hazards**: Traps, unstable floors, magical zones

#### Resources
- **Basic Materials**: Wood, stone, iron ore
- **Magical Components**: Crystals, essence, rare herbs
- **Food**: Mushrooms, roots, magical fruits
- **Water Sources**: Fountains, streams, wells

### Monsters and Threats
- **Wandering Monsters**: Random encounters
- **Lairs**: Monster homes with treasures
- **Intelligent Foes**: Enemies with strategies
- **Environmental Dangers**: Cave-ins, floods, magical storms
- **Boss Creatures**: Powerful level guardians

## Technical Architecture

### Core Systems

#### Terminal Rendering
- **Blessed Library**: Cross-platform terminal control
- **RGB Color Support**: Rich visual experience
- **Partial Updates**: Only redraw changed tiles
- **ASCII Art**: Traditional roguelike aesthetics

#### Turn-Based Engine
- **Event Queue**: Ordered action resolution
- **State Management**: Consistent game state
- **Save System**: JSON-based persistent saves
- **Undo Prevention**: Roguelike permadeath

#### Configuration System
- **JSON-Based**: Human-readable configuration files
- **Hot-Reload**: Development mode config updates
- **User Overrides**: Default + user configuration merge
- **Validation**: Schema-based config validation

#### Storage Architecture
- **Save Games**: JSON format with versioning
- **Configuration**: Layered JSON config system
- **Game Data**: JSON definitions for items, spells, monsters
- **Compression**: Optional save compression for large games

#### AI Integration
- **OpenAI GPT-4o-mini**: Backstory and dialogue generation
- **Caching System**: Reduce API calls
- **Fallback Dialogue**: Offline mode support
- **Context Management**: Maintain conversation coherence

### User Interface

#### Main View
```
################################################################################
#..........#############.......................................................#
#..........#  Library  #................<......................................#
#..........#############.......................................................#
#...@...............................###########################################
#...M...............................#                                         #
#...........M.......................#  Messages:                             #
#...........m.......................#  Aldric: "I sense danger ahead..."     #
#...................................#  You cast Divine Light!                #
#...................................#  Marina found a healing potion.        #
#...............................>...#  Goblin attacks Aldric for 3 damage!   #
#...................................#                                         #
################################################################################
HP: ∞  MP: 45/50  Mages: 3/3  Level: 2  Turn: 1,234
```

#### UI Components
- **Map Display**: Main game world view
- **Message Log**: Scrollable history of events
- **Status Bar**: Player and mage statistics
- **Spell Menu**: Available divine interventions
- **Mage Details**: Individual mage information

### Controls

#### Movement (Vim-style)
- **h**: Move west (left)
- **j**: Move south (down)  
- **k**: Move north (up)
- **l**: Move east (right)
- **y**: Move northwest (diagonal up-left)
- **u**: Move northeast (diagonal up-right)
- **b**: Move southwest (diagonal down-left)
- **n**: Move southeast (diagonal down-right)
- **.**: Wait/rest in place

#### Actions
- **Spells**: Number keys for quick cast
- **Examine**: x to examine tile
- **Inventory**: i for inventory
- **Menus**: Tab for spell list, m for mage roster
- **System**: Q to quit, S to save, ? for help

*Note: All keybindings are configurable via config.json*

## Development Approach

### Test-Driven Development (TDD)
- Write tests before implementation
- Maintain >80% code coverage
- Automated testing with pytest
- Performance benchmarks for turn resolution

### Modular Architecture
- **Core Engine**: Turn management, rendering
- **Entity System**: Flexible ECS for game objects
- **AI Module**: Behavior trees and decision making
- **World Generation**: Pluggable map generators
- **UI Layer**: Separated rendering concerns

### Development Phases

#### Phase 1: Foundation (Complete)
- ✅ Project setup with uv and Makefile
- ✅ Terminal abstraction layer
- ✅ Testing infrastructure
- ⏳ Event system
- ⏳ Game state management

#### Phase 2: Basic Gameplay
- Procedural map generation
- Player movement and viewing
- Basic mage entities
- Simple resource system
- Turn-based game loop

#### Phase 3: AI Integration
- OpenAI integration
- Mage personalities
- Dynamic dialogue system
- Social interactions
- Backstory generation

#### Phase 4: Divine Powers
- Spell system implementation
- Mana/divine power resource
- Spell effects and targeting
- Visual feedback system

#### Phase 5: Advanced Features
- Combat system
- Crafting mechanics
- Magic items
- Monster AI
- Level progression

## Success Metrics

### Technical
- Turn resolution < 100ms
- Support 100+ entities per level
- 0% flicker during updates
- <500MB memory usage

### Gameplay
- Average session length > 30 minutes
- Mage survival rate 20-80% (varies by difficulty)
- Unique stories generated each playthrough
- Meaningful player choices affect outcomes

### Quality
- No crashes during normal gameplay
- Save system reliability 100%
- AI responses coherent and contextual
- Consistent roguelike "feel"

## Future Expansions

### Planned Features
- Multiplayer god competition/cooperation
- Mod support via JSON configuration and data files
- Advanced AI personalities
- Seasonal events and challenges
- Achievement system
- Custom keybinding profiles for different playstyles

### Potential Platforms
- Web version using terminal emulation
- Native desktop applications
- Cloud saves and sharing
- Community story archive

## Design Principles

### Roguelike Adherence
- **Permadeath**: Dead mages stay dead
- **Procedural Generation**: Unique worlds
- **Turn-Based**: Player controls pacing
- **Resource Management**: Scarcity drives decisions
- **Discovery**: Hidden mechanics to uncover

### Player Agency
- **Meaningful Choices**: Every spell matters
- **Multiple Solutions**: Many ways to help mages
- **Emergent Gameplay**: Unexpected combinations
- **Risk/Reward**: Divine power is limited

### Accessibility
- **Color Options**: Colorblind modes
- **Speed**: No reflexes required
- **Complexity Ramp**: Gradual introduction
- **Help System**: Comprehensive documentation

## JSON File Structures

### Configuration Files

#### config.json (User Configuration)
```json
{
  "version": "1.0.0",
  "keybindings": {
    "movement": {
      "north": "k",
      "south": "j",
      "east": "l",
      "west": "h",
      "northeast": "u",
      "northwest": "y",
      "southeast": "n",
      "southwest": "b",
      "wait": "."
    },
    "actions": {
      "examine": "x",
      "inventory": "i",
      "spell_menu": "Tab",
      "mage_roster": "m",
      "save": "S",
      "quit": "Q",
      "help": "?"
    }
  },
  "display": {
    "terminal_width": 80,
    "terminal_height": 24,
    "message_log_size": 100,
    "color_mode": "rgb",
    "color_scheme": "default"
  },
  "gameplay": {
    "autosave_turns": 100,
    "difficulty": "normal",
    "pause_on_danger": true
  },
  "ai": {
    "model": "gpt-4o-mini",
    "temperature": 0.8,
    "max_tokens": 150,
    "cache_responses": true
  }
}
```

#### colors.json (Color Schemes)
```json
{
  "schemes": {
    "default": {
      "player": [100, 150, 255],
      "mage": [150, 200, 255],
      "wall": [128, 128, 128],
      "floor": [64, 64, 64],
      "divine_spell": [255, 215, 0],
      "danger": [255, 0, 0],
      "safe": [0, 255, 0]
    },
    "colorblind": {
      "player": [0, 114, 178],
      "mage": [86, 180, 233],
      "wall": [128, 128, 128],
      "floor": [64, 64, 64],
      "divine_spell": [240, 228, 66],
      "danger": [213, 94, 0],
      "safe": [0, 158, 115]
    }
  }
}
```

### Game Data Files

#### items.json
```json
{
  "version": "1.0.0",
  "items": {
    "healing_potion": {
      "name": "Healing Potion",
      "symbol": "!",
      "color": [255, 0, 0],
      "category": "consumable",
      "effects": {
        "heal": 20
      },
      "rarity": "common",
      "value": 50
    }
  }
}
```

#### spells.json
```json
{
  "version": "1.0.0",
  "divine_spells": {
    "heal": {
      "name": "Divine Healing",
      "cost": 5,
      "range": 5,
      "target": "single_mage",
      "effects": {
        "heal": 30
      },
      "description": "Restore health to a wounded mage"
    }
  }
}
```

### Save Game Format

#### saves/save_[timestamp].json
```json
{
  "metadata": {
    "version": "1.0.0",
    "timestamp": "2024-01-20T15:30:00Z",
    "turn": 1234,
    "play_time": 3600,
    "seed": 42
  },
  "player": {
    "divine_power": 45,
    "max_divine_power": 50,
    "spells_known": ["heal", "smite", "inspire"],
    "view_position": {"x": 10, "y": 15}
  },
  "world": {
    "current_level": 2,
    "levels": {
      "1": {
        "width": 80,
        "height": 24,
        "tiles": "base64_compressed_data",
        "discovered": "base64_compressed_data"
      }
    }
  },
  "mages": [
    {
      "id": "mage_001",
      "name": "Aldric",
      "position": {"x": 12, "y": 10},
      "stats": {
        "health": 75,
        "max_health": 100,
        "level": 3
      },
      "personality": {
        "traits": ["brave", "curious"],
        "backstory": "Generated backstory...",
        "relationships": {
          "mage_002": 75
        }
      },
      "inventory": ["healing_potion", "iron_sword"],
      "ai_context": "compressed_conversation_history"
    }
  ],
  "message_log": [
    {
      "turn": 1234,
      "message": "Aldric found a healing potion!",
      "type": "discovery"
    }
  ]
}
```

### Benefits of JSON Architecture

1. **Human Readable**: Easy to debug and modify save files
2. **Version Control Friendly**: Text-based format works well with git
3. **Extensible**: Easy to add new fields without breaking compatibility
4. **Moddable**: Players can create custom items, spells, and configurations
5. **Cross-Platform**: JSON works everywhere Python runs
6. **Validation**: Can use JSON Schema for validation
7. **Compression**: Large data (like tile maps) can be base64 encoded and compressed

## Technical Requirements

### Minimum System
- Python 3.11+
- Terminal with 80x24 character support
- 256 color terminal (RGB preferred)
- Internet connection for AI features
- 100MB free disk space

### Recommended System
- Modern terminal emulator
- RGB color support
- 1GB RAM
- SSD for save/load performance

## Conclusion

MageMines aims to create a unique roguelike experience where players experience the joy and frustration of divine guidance. By combining autonomous AI-driven characters with strategic divine intervention, the game creates emergent narratives that are different every time while maintaining the classic roguelike challenge and depth.