"""Configuration management system for MageMines.

This module provides a centralized configuration system that loads settings
from JSON files and makes them available throughout the application.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging


class ConfigError(Exception):
    """Raised when there's an error in configuration loading or validation."""
    pass


class ConfigSection(Enum):
    """Configuration sections available in the system."""
    GAME = "game"
    DISPLAY = "display"
    MAP_GENERATION = "map_generation"
    ENTITIES = "entities"
    UI = "ui"
    AI = "ai"
    DIVINE_POWERS = "divine_powers"
    RESOURCES = "resources"
    COMBAT = "combat"
    PERFORMANCE = "performance"
    DEBUG = "debug"


@dataclass
class GameConfig:
    """Core game settings."""
    seed: Optional[int] = None
    difficulty: str = "normal"
    turn_duration_ms: int = 100
    max_turns: Optional[int] = None
    autosave_interval: int = 100
    autosave_enabled: bool = True
    
    
@dataclass
class DisplayConfig:
    """Display and rendering settings."""
    width: int = 80
    height: int = 24
    fullscreen: bool = True
    color_mode: str = "rgb"  # rgb, 256, 16, mono
    font_size: Optional[int] = None
    vsync: bool = True
    fps_limit: int = 60
    show_fps: bool = False
    

@dataclass 
class MapGenerationConfig:
    """Map generation parameters."""
    default_width: int = 80
    default_height: int = 50
    
    # Room generation
    min_room_size: int = 4
    max_room_size: int = 12
    max_rooms_base: int = 20
    rooms_per_level: float = 0.5
    
    # Corridor generation  
    corridor_style: str = "l_shaped"  # l_shaped, diagonal, mixed
    corridor_width: int = 1
    door_chance: float = 0.2
    
    # Level themes
    town_frequency: int = 5  # Town every N levels
    cave_frequency: int = 5  # Cave every N levels
    
    # Cellular automata (caves)
    cave_fill_probability: float = 0.45
    cave_smoothing_iterations: int = 5
    cave_neighbor_threshold: int = 4
    
    # Town generation
    town_building_min_size: int = 4
    town_building_max_size: int = 8
    town_street_width: int = 3
    town_building_door_chance: float = 1.0
    

@dataclass
class EntityConfig:
    """Entity system configuration."""
    max_entities_per_level: int = 100
    entity_spawn_rate: float = 0.1
    
    # Mage configuration
    mage_base_health: int = 100
    mage_base_mana: int = 50
    mage_base_speed: int = 100
    mage_vision_range: int = 8
    mage_max_inventory: int = 20
    
    # Monster configuration
    monster_spawn_chance: float = 0.05
    monster_difficulty_scaling: float = 0.1
    monster_pack_chance: float = 0.2
    monster_pack_size_min: int = 2
    monster_pack_size_max: int = 5


@dataclass
class UIConfig:
    """User interface configuration."""
    # Message pane
    message_pane_width: int = 40
    message_pane_height: int = 8
    message_history_size: int = 1000
    message_categories: List[str] = field(default_factory=lambda: [
        "system", "info", "warning", "error", "combat", 
        "magic", "divine", "dialogue", "discovery"
    ])
    
    # Colors (RGB tuples)
    color_scheme: Dict[str, List[int]] = field(default_factory=lambda: {
        "background": [0, 0, 0],
        "foreground": [255, 255, 255],
        "wall": [128, 128, 128],
        "floor": [64, 64, 64],
        "door_closed": [139, 69, 19],
        "door_open": [160, 82, 45],
        "water": [0, 119, 190],
        "lava": [207, 16, 32],
        "player": [255, 255, 255],
        "mage": [100, 149, 237],
        "monster": [220, 20, 60],
        "item": [255, 215, 0],
        "spell_effect": [255, 255, 0]
    })
    
    # Header bar
    header_show_turn: bool = True
    header_show_depth: bool = True
    header_show_mana: bool = True
    header_show_fps: bool = False
    
    # Loading overlay
    loading_spinner_speed: float = 0.1
    loading_styles: List[str] = field(default_factory=lambda: [
        "spinner", "dots", "progress_bar"
    ])


@dataclass
class AIConfig:
    """AI and behavior configuration."""
    # Pathfinding
    pathfinding_algorithm: str = "astar"  # astar, dijkstra, jps
    pathfinding_max_steps: int = 1000
    pathfinding_cache_size: int = 100
    
    # Mage AI
    mage_ai_think_time: float = 0.1
    mage_ai_update_frequency: int = 1
    mage_task_priorities: Dict[str, float] = field(default_factory=lambda: {
        "survive": 1.0,
        "eat": 0.8,
        "gather": 0.6,
        "craft": 0.5,
        "socialize": 0.4,
        "explore": 0.3
    })
    
    # OpenAI integration
    openai_enabled: bool = False
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 150
    openai_cache_responses: bool = True
    openai_retry_attempts: int = 3
    openai_timeout: int = 30


@dataclass
class DivinePowersConfig:
    """Divine powers and spells configuration."""
    starting_divine_power: int = 100
    divine_power_regen_rate: float = 0.5
    divine_power_max: int = 1000
    
    # Spell costs
    spell_costs: Dict[str, int] = field(default_factory=lambda: {
        "heal": 20,
        "smite": 30,
        "inspire": 15,
        "reveal": 10,
        "terraform": 50,
        "summon": 40,
        "teleport": 25
    })
    
    # Spell cooldowns (in turns)
    spell_cooldowns: Dict[str, int] = field(default_factory=lambda: {
        "heal": 5,
        "smite": 10,
        "inspire": 20,
        "reveal": 3,
        "terraform": 50,
        "summon": 30,
        "teleport": 15
    })


@dataclass
class ResourceConfig:
    """Resource and crafting configuration."""
    resource_types: List[str] = field(default_factory=lambda: [
        "wood", "stone", "iron", "gold", "crystal", "herb", "food"
    ])
    
    resource_spawn_rates: Dict[str, float] = field(default_factory=lambda: {
        "wood": 0.1,
        "stone": 0.08,
        "iron": 0.04,
        "gold": 0.02,
        "crystal": 0.01,
        "herb": 0.06,
        "food": 0.08
    })
    
    resource_stack_sizes: Dict[str, int] = field(default_factory=lambda: {
        "wood": 20,
        "stone": 20,
        "iron": 10,
        "gold": 10,
        "crystal": 5,
        "herb": 30,
        "food": 50
    })


@dataclass
class CombatConfig:
    """Combat system configuration."""
    base_attack_damage: int = 10
    base_defense: int = 5
    critical_hit_chance: float = 0.05
    critical_hit_multiplier: float = 2.0
    
    # Status effects
    status_effect_durations: Dict[str, int] = field(default_factory=lambda: {
        "poisoned": 10,
        "stunned": 2,
        "blessed": 20,
        "cursed": 15,
        "burning": 5,
        "frozen": 3
    })


@dataclass
class PerformanceConfig:
    """Performance and optimization settings."""
    # Rendering
    partial_rendering: bool = True
    dirty_rect_tracking: bool = True
    render_distance: int = 30
    
    # Entity processing
    entity_update_budget_ms: int = 50
    max_pathfinding_per_turn: int = 10
    
    # Memory
    level_cache_size: int = 5
    entity_pool_size: int = 1000
    message_buffer_size: int = 1000
    
    # Threading
    use_threading: bool = False
    worker_threads: int = 2


@dataclass
class DebugConfig:
    """Debug and development settings."""
    debug_mode: bool = False
    show_room_numbers: bool = False
    show_pathfinding: bool = False
    show_entity_states: bool = False
    show_tile_coordinates: bool = False
    immortal_player: bool = False
    unlimited_mana: bool = False
    reveal_all_maps: bool = False
    fast_map_generation: bool = False
    log_level: str = "INFO"
    log_file: Optional[str] = "magemines.log"


class ConfigurationManager:
    """Manages loading and access to all configuration."""
    
    def __init__(self, config_dir: Optional[Union[str, Path]] = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files.
                       Defaults to 'config' in project root.
        """
        if config_dir is None:
            # Find project root (where pyproject.toml is)
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "pyproject.toml").exists():
                    config_dir = current / "config"
                    break
                current = current.parent
            else:
                config_dir = Path.cwd() / "config"
                
        self.config_dir = Path(config_dir)
        self.configs: Dict[ConfigSection, Any] = {}
        self._config_classes = {
            ConfigSection.GAME: GameConfig,
            ConfigSection.DISPLAY: DisplayConfig,
            ConfigSection.MAP_GENERATION: MapGenerationConfig,
            ConfigSection.ENTITIES: EntityConfig,
            ConfigSection.UI: UIConfig,
            ConfigSection.AI: AIConfig,
            ConfigSection.DIVINE_POWERS: DivinePowersConfig,
            ConfigSection.RESOURCES: ResourceConfig,
            ConfigSection.COMBAT: CombatConfig,
            ConfigSection.PERFORMANCE: PerformanceConfig,
            ConfigSection.DEBUG: DebugConfig
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def load_all(self) -> None:
        """Load all configuration files."""
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load each configuration section
        for section in ConfigSection:
            self.load_section(section)
            
        # Load overrides if they exist
        self._load_overrides()
        
    def load_section(self, section: ConfigSection) -> Any:
        """Load a specific configuration section.
        
        Args:
            section: The configuration section to load.
            
        Returns:
            The loaded configuration object.
        """
        config_file = self.config_dir / f"{section.value}.json"
        config_class = self._config_classes[section]
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                # Create config object from loaded data
                config_obj = config_class(**data)
            except (json.JSONDecodeError, TypeError) as e:
                self.logger.warning(f"Error loading {config_file}: {e}")
                self.logger.info(f"Using default configuration for {section.value}")
                config_obj = config_class()
        else:
            # Create default configuration
            config_obj = config_class()
            # Save default configuration
            self._save_section(section, config_obj)
            self.logger.info(f"Created default configuration file: {config_file}")
            
        self.configs[section] = config_obj
        return config_obj
        
    def _save_section(self, section: ConfigSection, config_obj: Any) -> None:
        """Save a configuration section to file.
        
        Args:
            section: The configuration section.
            config_obj: The configuration object to save.
        """
        config_file = self.config_dir / f"{section.value}.json"
        
        # Convert dataclass to dict
        data = asdict(config_obj)
        
        # Write with pretty formatting
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _load_overrides(self) -> None:
        """Load configuration overrides from overrides.json."""
        override_file = self.config_dir / "overrides.json"
        
        if not override_file.exists():
            return
            
        try:
            with open(override_file, 'r') as f:
                overrides = json.load(f)
                
            # Apply overrides to each section
            for section_name, section_overrides in overrides.items():
                try:
                    section = ConfigSection(section_name)
                    if section in self.configs:
                        config_obj = self.configs[section]
                        # Apply each override
                        for key, value in section_overrides.items():
                            if hasattr(config_obj, key):
                                setattr(config_obj, key, value)
                                self.logger.info(
                                    f"Applied override: {section_name}.{key} = {value}"
                                )
                except ValueError:
                    self.logger.warning(f"Unknown section in overrides: {section_name}")
                    
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.error(f"Error loading overrides: {e}")
            
    def get(self, section: ConfigSection) -> Any:
        """Get a configuration section.
        
        Args:
            section: The configuration section to retrieve.
            
        Returns:
            The configuration object for the section.
            
        Raises:
            ConfigError: If the section hasn't been loaded.
        """
        if section not in self.configs:
            raise ConfigError(f"Configuration section {section.value} not loaded")
        return self.configs[section]
        
    def reload(self) -> None:
        """Reload all configuration files."""
        self.logger.info("Reloading configuration...")
        self.configs.clear()
        self.load_all()
        
    def save_all(self) -> None:
        """Save all current configurations to files."""
        for section, config_obj in self.configs.items():
            self._save_section(section, config_obj)
        self.logger.info("Saved all configurations")
        
    def create_default_configs(self) -> None:
        """Create all default configuration files."""
        for section, config_class in self._config_classes.items():
            config_file = self.config_dir / f"{section.value}.json"
            if not config_file.exists():
                config_obj = config_class()
                self._save_section(section, config_obj)
                self.logger.info(f"Created default config: {config_file}")
                

# Global configuration instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance.
    
    Returns:
        The configuration manager.
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
        _config_manager.load_all()
    return _config_manager


def get_config(section: ConfigSection) -> Any:
    """Convenience function to get a configuration section.
    
    Args:
        section: The configuration section to retrieve.
        
    Returns:
        The configuration object for the section.
    """
    return get_config_manager().get(section)