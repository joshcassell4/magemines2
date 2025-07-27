"""Tests for the configuration system."""

import json
import pytest
from pathlib import Path
import tempfile
import shutil

from magemines.core.config import (
    ConfigurationManager, ConfigSection, ConfigError,
    GameConfig, DisplayConfig, MapGenerationConfig,
    UIConfig, DebugConfig
)


class TestConfigurationManager:
    """Test the ConfigurationManager class."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for test configs."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir)
        
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create a ConfigurationManager with temp directory."""
        return ConfigurationManager(temp_config_dir)
        
    def test_init_creates_directory(self, temp_config_dir):
        """Test that initialization creates config directory."""
        # Remove the directory first
        shutil.rmtree(temp_config_dir)
        assert not temp_config_dir.exists()
        
        # Create manager
        manager = ConfigurationManager(temp_config_dir)
        manager.load_all()
        
        # Directory should be created
        assert temp_config_dir.exists()
        
    def test_load_creates_default_configs(self, config_manager):
        """Test that loading creates default config files."""
        config_manager.load_all()
        
        # Check that all config files were created
        for section in ConfigSection:
            config_file = config_manager.config_dir / f"{section.value}.json"
            assert config_file.exists()
            
    def test_load_section_returns_correct_type(self, config_manager):
        """Test that loading sections returns correct config types."""
        game_config = config_manager.load_section(ConfigSection.GAME)
        assert isinstance(game_config, GameConfig)
        
        display_config = config_manager.load_section(ConfigSection.DISPLAY)
        assert isinstance(display_config, DisplayConfig)
        
    def test_get_section(self, config_manager):
        """Test getting configuration sections."""
        config_manager.load_all()
        
        game_config = config_manager.get(ConfigSection.GAME)
        assert isinstance(game_config, GameConfig)
        assert game_config.difficulty == "normal"
        
    def test_get_unloaded_section_raises_error(self, config_manager):
        """Test that getting unloaded section raises error."""
        with pytest.raises(ConfigError):
            config_manager.get(ConfigSection.GAME)
            
    def test_save_and_reload(self, config_manager):
        """Test saving and reloading configuration."""
        config_manager.load_all()
        
        # Modify a value
        game_config = config_manager.get(ConfigSection.GAME)
        game_config.difficulty = "hard"
        game_config.turn_duration_ms = 200
        
        # Save
        config_manager.save_all()
        
        # Create new manager and load
        new_manager = ConfigurationManager(config_manager.config_dir)
        new_manager.load_all()
        
        # Check values persisted
        loaded_config = new_manager.get(ConfigSection.GAME)
        assert loaded_config.difficulty == "hard"
        assert loaded_config.turn_duration_ms == 200
        
    def test_override_system(self, config_manager):
        """Test configuration override system."""
        config_manager.load_all()
        
        # Create override file
        override_file = config_manager.config_dir / "overrides.json"
        overrides = {
            "game": {
                "difficulty": "expert",
                "autosave_interval": 50
            },
            "debug": {
                "debug_mode": True,
                "immortal_player": True
            }
        }
        
        with open(override_file, 'w') as f:
            json.dump(overrides, f)
            
        # Reload to apply overrides
        config_manager.reload()
        
        # Check overrides applied
        game_config = config_manager.get(ConfigSection.GAME)
        assert game_config.difficulty == "expert"
        assert game_config.autosave_interval == 50
        
        debug_config = config_manager.get(ConfigSection.DEBUG)
        assert debug_config.debug_mode is True
        assert debug_config.immortal_player is True
        
    def test_invalid_json_uses_defaults(self, config_manager):
        """Test that invalid JSON files result in default configs."""
        # Create invalid JSON file
        invalid_file = config_manager.config_dir / "game.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
            
        # Load should succeed with defaults
        game_config = config_manager.load_section(ConfigSection.GAME)
        assert isinstance(game_config, GameConfig)
        assert game_config.difficulty == "normal"  # Default value
        
    def test_partial_config_fills_defaults(self, config_manager):
        """Test that partial configs are filled with defaults."""
        # Create partial config
        partial_file = config_manager.config_dir / "game.json"
        with open(partial_file, 'w') as f:
            json.dump({"difficulty": "hard"}, f)
            
        # Load should fill in missing values
        game_config = config_manager.load_section(ConfigSection.GAME)
        assert game_config.difficulty == "hard"  # From file
        assert game_config.turn_duration_ms == 100  # Default
        
    def test_create_default_configs(self, config_manager):
        """Test creating all default configs at once."""
        config_manager.create_default_configs()
        
        # Check all files exist
        for section in ConfigSection:
            config_file = config_manager.config_dir / f"{section.value}.json"
            assert config_file.exists()
            
            # Verify it's valid JSON
            with open(config_file, 'r') as f:
                data = json.load(f)
                assert isinstance(data, dict)


class TestConfigClasses:
    """Test individual configuration classes."""
    
    def test_game_config_defaults(self):
        """Test GameConfig default values."""
        config = GameConfig()
        assert config.seed is None
        assert config.difficulty == "normal"
        assert config.turn_duration_ms == 100
        assert config.autosave_enabled is True
        
    def test_ui_config_defaults(self):
        """Test UIConfig default values."""
        config = UIConfig()
        assert config.message_pane_width == 40
        assert config.message_history_size == 1000
        assert "system" in config.message_categories
        assert config.color_scheme["background"] == [0, 0, 0]
        
    def test_map_generation_config_defaults(self):
        """Test MapGenerationConfig defaults."""
        config = MapGenerationConfig()
        assert config.min_room_size == 4
        assert config.max_room_size == 12
        assert config.corridor_style == "l_shaped"
        assert config.door_chance == 0.2
        
    def test_debug_config_defaults(self):
        """Test DebugConfig defaults."""
        config = DebugConfig()
        assert config.debug_mode is False
        assert config.immortal_player is False
        assert config.log_level == "INFO"
        

class TestGlobalFunctions:
    """Test global configuration functions."""
    
    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton."""
        from magemines.core.config import get_config_manager, _config_manager
        
        # Clear any existing instance
        import magemines.core.config
        magemines.core.config._config_manager = None
        
        # First call creates instance
        manager1 = get_config_manager()
        assert manager1 is not None
        
        # Second call returns same instance
        manager2 = get_config_manager()
        assert manager1 is manager2
        
    def test_get_config_convenience(self):
        """Test get_config convenience function."""
        from magemines.core.config import get_config, get_config_manager
        
        # Ensure manager is loaded
        get_config_manager().load_all()
        
        # Get config through convenience function
        game_config = get_config(ConfigSection.GAME)
        assert isinstance(game_config, GameConfig)