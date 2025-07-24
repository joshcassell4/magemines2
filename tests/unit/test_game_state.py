"""Tests for game state management system."""

import json
import pytest
from unittest.mock import Mock, patch, mock_open
from typing import Any, Dict
import time

from magemines.core.state import (
    GameState,
    StateManager,
    StateTransition,
    StateSerializer,
    GamePhase,
    TurnState,
    WorldState,
    PlayerState,
    EntityState,
    Position,
    SaveMetadata,
    StateValidationError,
    StateTransitionError,
)


class TestGamePhase:
    """Test game phase enum."""
    
    def test_game_phases_exist(self):
        """Test that all game phases are defined."""
        assert GamePhase.MENU
        assert GamePhase.PLAYING
        assert GamePhase.PAUSED
        assert GamePhase.GAME_OVER
        assert GamePhase.VICTORY
        
    def test_phase_transitions(self):
        """Test valid phase transitions."""
        # Define valid transitions
        valid_transitions = {
            GamePhase.MENU: [GamePhase.PLAYING],
            GamePhase.PLAYING: [GamePhase.PAUSED, GamePhase.GAME_OVER, GamePhase.VICTORY],
            GamePhase.PAUSED: [GamePhase.PLAYING, GamePhase.MENU],
            GamePhase.GAME_OVER: [GamePhase.MENU],
            GamePhase.VICTORY: [GamePhase.MENU],
        }
        
        # Test that valid transitions are allowed
        for from_phase, to_phases in valid_transitions.items():
            for to_phase in to_phases:
                # This should not raise
                assert from_phase != to_phase or from_phase == GamePhase.MENU


class TestPosition:
    """Test position data class."""
    
    def test_position_creation(self):
        """Test creating a position."""
        pos = Position(10, 20)
        assert pos.x == 10
        assert pos.y == 20
        
    def test_position_equality(self):
        """Test position equality."""
        pos1 = Position(5, 5)
        pos2 = Position(5, 5)
        pos3 = Position(5, 6)
        
        assert pos1 == pos2
        assert pos1 != pos3
        
    def test_position_to_dict(self):
        """Test converting position to dict."""
        pos = Position(15, 25)
        data = pos.to_dict()
        
        assert data == {"x": 15, "y": 25}
        
    def test_position_from_dict(self):
        """Test creating position from dict."""
        data = {"x": 30, "y": 40}
        pos = Position.from_dict(data)
        
        assert pos.x == 30
        assert pos.y == 40


class TestPlayerState:
    """Test player state management."""
    
    def test_player_state_creation(self):
        """Test creating player state."""
        state = PlayerState(
            position=Position(10, 10),
            divine_power=45,
            max_divine_power=50,
            spells_known=["heal", "smite"]
        )
        
        assert state.position.x == 10
        assert state.position.y == 10
        assert state.divine_power == 45
        assert state.max_divine_power == 50
        assert "heal" in state.spells_known
        assert "smite" in state.spells_known
        
    def test_player_state_defaults(self):
        """Test player state with defaults."""
        state = PlayerState()
        
        assert state.position.x == 0
        assert state.position.y == 0
        assert state.divine_power == 50
        assert state.max_divine_power == 50
        assert state.spells_known == []
        
    def test_player_state_serialization(self):
        """Test serializing player state."""
        state = PlayerState(
            position=Position(5, 5),
            divine_power=30,
            spells_known=["heal"]
        )
        
        data = state.to_dict()
        
        assert data["position"] == {"x": 5, "y": 5}
        assert data["divine_power"] == 30
        assert data["max_divine_power"] == 50
        assert data["spells_known"] == ["heal"]
        
    def test_player_state_deserialization(self):
        """Test deserializing player state."""
        data = {
            "position": {"x": 15, "y": 20},
            "divine_power": 25,
            "max_divine_power": 60,
            "spells_known": ["heal", "inspire", "smite"]
        }
        
        state = PlayerState.from_dict(data)
        
        assert state.position.x == 15
        assert state.position.y == 20
        assert state.divine_power == 25
        assert state.max_divine_power == 60
        assert len(state.spells_known) == 3


class TestEntityState:
    """Test entity state management."""
    
    def test_entity_state_creation(self):
        """Test creating entity state."""
        state = EntityState(
            id="mage_001",
            type="mage",
            position=Position(10, 15),
            health=75,
            max_health=100,
            data={"name": "Aldric", "level": 3}
        )
        
        assert state.id == "mage_001"
        assert state.type == "mage"
        assert state.position.x == 10
        assert state.position.y == 15
        assert state.health == 75
        assert state.max_health == 100
        assert state.data["name"] == "Aldric"
        assert state.data["level"] == 3
        
    def test_entity_state_serialization(self):
        """Test entity state serialization."""
        state = EntityState(
            id="goblin_001",
            type="monster",
            position=Position(20, 20),
            health=10,
            max_health=10
        )
        
        data = state.to_dict()
        
        assert data["id"] == "goblin_001"
        assert data["type"] == "monster"
        assert data["position"] == {"x": 20, "y": 20}
        assert data["health"] == 10
        assert data["max_health"] == 10
        assert data["data"] == {}


class TestWorldState:
    """Test world state management."""
    
    def test_world_state_creation(self):
        """Test creating world state."""
        state = WorldState(
            current_level=2,
            seed=12345,
            discovered_tiles={(0, 0), (0, 1), (1, 0)},
            level_data={"1": {"cleared": True}, "2": {"cleared": False}}
        )
        
        assert state.current_level == 2
        assert state.seed == 12345
        assert (0, 0) in state.discovered_tiles
        assert state.level_data["1"]["cleared"] is True
        
    def test_world_state_defaults(self):
        """Test world state defaults."""
        state = WorldState()
        
        assert state.current_level == 1
        assert state.seed is not None  # Should generate random seed
        assert len(state.discovered_tiles) == 0
        assert state.level_data == {}
        
    def test_world_state_serialization(self):
        """Test world state serialization."""
        state = WorldState(
            current_level=3,
            seed=42,
            discovered_tiles={(5, 5), (5, 6)}
        )
        
        data = state.to_dict()
        
        assert data["current_level"] == 3
        assert data["seed"] == 42
        # Sets are converted to lists for JSON
        tiles = data["discovered_tiles"]
        assert [5, 5] in tiles
        assert [5, 6] in tiles


class TestTurnState:
    """Test turn state management."""
    
    def test_turn_state_creation(self):
        """Test creating turn state."""
        state = TurnState(
            turn_number=100,
            current_phase="player_action",
            entities_acted=["mage_001", "goblin_001"]
        )
        
        assert state.turn_number == 100
        assert state.current_phase == "player_action"
        assert "mage_001" in state.entities_acted
        
    def test_turn_state_defaults(self):
        """Test turn state defaults."""
        state = TurnState()
        
        assert state.turn_number == 0
        assert state.current_phase == "player_action"
        assert state.entities_acted == []
        
    def test_turn_state_next_turn(self):
        """Test advancing to next turn."""
        state = TurnState(turn_number=5)
        state.entities_acted = ["mage_001"]
        
        state.next_turn()
        
        assert state.turn_number == 6
        assert state.entities_acted == []
        assert state.current_phase == "player_action"


class TestGameState:
    """Test the main game state class."""
    
    def test_game_state_creation(self):
        """Test creating game state."""
        state = GameState(
            phase=GamePhase.PLAYING,
            turn=TurnState(turn_number=10),
            world=WorldState(current_level=2),
            player=PlayerState(divine_power=30)
        )
        
        assert state.phase == GamePhase.PLAYING
        assert state.turn.turn_number == 10
        assert state.world.current_level == 2
        assert state.player.divine_power == 30
        assert state.entities == {}
        assert state.message_log == []
        
    def test_game_state_defaults(self):
        """Test game state with defaults."""
        state = GameState()
        
        assert state.phase == GamePhase.MENU
        assert state.turn.turn_number == 0
        assert state.world.current_level == 1
        assert state.player.divine_power == 50
        
    def test_add_entity(self):
        """Test adding entities to game state."""
        state = GameState()
        
        entity = EntityState(
            id="mage_001",
            type="mage",
            position=Position(5, 5)
        )
        
        state.add_entity(entity)
        
        assert "mage_001" in state.entities
        assert state.entities["mage_001"] == entity
        
    def test_remove_entity(self):
        """Test removing entities from game state."""
        state = GameState()
        entity = EntityState(id="goblin_001", type="monster")
        
        state.add_entity(entity)
        assert "goblin_001" in state.entities
        
        state.remove_entity("goblin_001")
        assert "goblin_001" not in state.entities
        
    def test_get_entity(self):
        """Test getting entity by ID."""
        state = GameState()
        entity = EntityState(id="mage_001", type="mage")
        
        state.add_entity(entity)
        
        retrieved = state.get_entity("mage_001")
        assert retrieved == entity
        
        # Non-existent entity
        assert state.get_entity("fake_id") is None
        
    def test_add_message(self):
        """Test adding messages to log."""
        state = GameState()
        
        state.add_message("Welcome to MageMines!")
        state.add_message("You cast heal.", "spell")
        
        assert len(state.message_log) == 2
        assert state.message_log[0]["message"] == "Welcome to MageMines!"
        assert state.message_log[0]["category"] == "general"
        assert state.message_log[1]["message"] == "You cast heal."
        assert state.message_log[1]["category"] == "spell"
        
    def test_message_log_limit(self):
        """Test message log size limit."""
        state = GameState()
        
        # Add many messages
        for i in range(1500):
            state.add_message(f"Message {i}")
            
        # Should be limited to 1000
        assert len(state.message_log) == 1000
        # Oldest messages should be removed
        assert state.message_log[0]["message"] == "Message 500"
        assert state.message_log[-1]["message"] == "Message 1499"


class TestStateTransition:
    """Test state transitions."""
    
    def test_valid_phase_transition(self):
        """Test valid phase transitions."""
        state = GameState(phase=GamePhase.MENU)
        
        # Valid transition
        transition = StateTransition(
            from_phase=GamePhase.MENU,
            to_phase=GamePhase.PLAYING
        )
        
        assert transition.is_valid()
        
    def test_invalid_phase_transition(self):
        """Test invalid phase transitions."""
        # Invalid transition
        transition = StateTransition(
            from_phase=GamePhase.PLAYING,
            to_phase=GamePhase.MENU  # Can't go directly from playing to menu
        )
        
        assert not transition.is_valid()
        
    def test_transition_with_validation(self):
        """Test transition with custom validation."""
        def validator(state: GameState) -> bool:
            # Only allow if player has enough divine power
            return state.player.divine_power >= 10
            
        state = GameState()
        state.player.divine_power = 5
        
        transition = StateTransition(
            from_phase=GamePhase.MENU,
            to_phase=GamePhase.PLAYING,
            validator=validator
        )
        
        assert not transition.can_transition(state)
        
        state.player.divine_power = 15
        assert transition.can_transition(state)


class TestStateSerializer:
    """Test state serialization."""
    
    def test_serialize_game_state(self):
        """Test serializing complete game state."""
        state = GameState(
            phase=GamePhase.PLAYING,
            turn=TurnState(turn_number=50),
            world=WorldState(current_level=3, seed=42),
            player=PlayerState(divine_power=35)
        )
        
        # Add some entities
        state.add_entity(EntityState(
            id="mage_001",
            type="mage",
            position=Position(10, 10),
            data={"name": "Aldric"}
        ))
        
        # Add messages
        state.add_message("Game started")
        
        # Serialize
        serializer = StateSerializer()
        data = serializer.serialize(state)
        
        assert data["phase"] == "PLAYING"
        assert data["turn"]["turn_number"] == 50
        assert data["world"]["current_level"] == 3
        assert data["player"]["divine_power"] == 35
        assert "mage_001" in data["entities"]
        assert len(data["message_log"]) == 1
        
    def test_deserialize_game_state(self):
        """Test deserializing game state from data."""
        data = {
            "phase": "PLAYING",
            "turn": {
                "turn_number": 25,
                "current_phase": "entity_action",
                "entities_acted": ["mage_001"]
            },
            "world": {
                "current_level": 2,
                "seed": 12345,
                "discovered_tiles": [[5, 5], [5, 6]],
                "level_data": {}
            },
            "player": {
                "position": {"x": 10, "y": 10},
                "divine_power": 40,
                "max_divine_power": 50,
                "spells_known": ["heal"]
            },
            "entities": {
                "goblin_001": {
                    "id": "goblin_001",
                    "type": "monster",
                    "position": {"x": 15, "y": 15},
                    "health": 5,
                    "max_health": 10,
                    "data": {}
                }
            },
            "message_log": [
                {
                    "turn": 24,
                    "message": "Combat started",
                    "category": "combat"
                }
            ]
        }
        
        serializer = StateSerializer()
        state = serializer.deserialize(data)
        
        assert state.phase == GamePhase.PLAYING
        assert state.turn.turn_number == 25
        assert state.world.current_level == 2
        assert state.player.divine_power == 40
        assert "goblin_001" in state.entities
        assert len(state.message_log) == 1
        
    def test_save_to_file(self):
        """Test saving state to file."""
        state = GameState()
        serializer = StateSerializer()
        
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            metadata = serializer.save_to_file(state, "test_save.json")
            
        # Check file was opened for writing
        mock_file.assert_called_once_with("test_save.json", "w", encoding="utf-8")
        
        # Check JSON was written
        handle = mock_file()
        written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
        data = json.loads(written_data)
        
        assert "metadata" in data
        assert "state" in data
        assert data["metadata"]["version"] == "1.0.0"
        
    def test_load_from_file(self):
        """Test loading state from file."""
        save_data = {
            "metadata": {
                "version": "1.0.0",
                "timestamp": "2024-01-20T10:00:00Z",
                "turn": 100,
                "play_time": 3600
            },
            "state": {
                "phase": "PLAYING",
                "turn": {"turn_number": 100},
                "world": {"current_level": 1, "seed": 42},
                "player": {"position": {"x": 0, "y": 0}},
                "entities": {},
                "message_log": []
            }
        }
        
        mock_file = mock_open(read_data=json.dumps(save_data))
        serializer = StateSerializer()
        
        with patch("builtins.open", mock_file):
            state, metadata = serializer.load_from_file("test_save.json")
            
        assert state.phase == GamePhase.PLAYING
        assert state.turn.turn_number == 100
        assert metadata.version == "1.0.0"
        assert metadata.turn == 100


class TestStateManager:
    """Test the state manager."""
    
    def test_state_manager_creation(self):
        """Test creating state manager."""
        manager = StateManager()
        
        assert manager.current_state is not None
        assert manager.current_state.phase == GamePhase.MENU
        assert manager._event_bus is not None
        
    def test_state_manager_with_initial_state(self):
        """Test creating manager with initial state."""
        initial = GameState(phase=GamePhase.PLAYING)
        manager = StateManager(initial_state=initial)
        
        assert manager.current_state == initial
        
    def test_transition_phase(self):
        """Test phase transitions."""
        manager = StateManager()
        
        # Valid transition
        manager.transition_phase(GamePhase.PLAYING)
        assert manager.current_state.phase == GamePhase.PLAYING
        
        # Invalid transition should raise
        with pytest.raises(StateTransitionError):
            manager.transition_phase(GamePhase.MENU)
            
    def test_update_state(self):
        """Test updating state fields."""
        manager = StateManager()
        
        # Update player divine power
        manager.update_state("player.divine_power", 30)
        assert manager.current_state.player.divine_power == 30
        
        # Update nested field
        manager.update_state("world.current_level", 5)
        assert manager.current_state.world.current_level == 5
        
    def test_state_validation(self):
        """Test state validation."""
        manager = StateManager()
        state = manager.current_state
        
        # Valid state
        assert manager.validate_state()
        
        # Invalid divine power
        state.player.divine_power = -10
        assert not manager.validate_state()
        
        # Invalid level
        state.player.divine_power = 50
        state.world.current_level = 0
        assert not manager.validate_state()
        
    def test_state_snapshots(self):
        """Test state snapshot functionality."""
        manager = StateManager()
        
        # Take initial snapshot
        manager.take_snapshot("initial")
        
        # Modify state
        manager.current_state.player.divine_power = 25
        manager.current_state.turn.turn_number = 10
        
        # Take another snapshot
        manager.take_snapshot("after_turns")
        
        # Restore first snapshot
        manager.restore_snapshot("initial")
        assert manager.current_state.player.divine_power == 50
        assert manager.current_state.turn.turn_number == 0
        
        # Restore second snapshot
        manager.restore_snapshot("after_turns")
        assert manager.current_state.player.divine_power == 25
        assert manager.current_state.turn.turn_number == 10
        
    def test_save_and_load_game(self):
        """Test save/load functionality."""
        manager = StateManager()
        
        # Set up some state
        manager.transition_phase(GamePhase.PLAYING)
        manager.current_state.turn.turn_number = 50
        manager.current_state.player.divine_power = 35
        
        # Save
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            manager.save_game("test.save")
            
        # Create new manager and load
        new_manager = StateManager()
        
        save_data = {
            "metadata": {
                "version": "1.0.0",
                "timestamp": "2024-01-20T10:00:00Z",
                "turn": 50,
                "play_time": 1800
            },
            "state": {
                "phase": "PLAYING",
                "turn": {"turn_number": 50, "current_phase": "player_action", "entities_acted": []},
                "world": {"current_level": 1, "seed": 42, "discovered_tiles": [], "level_data": {}},
                "player": {
                    "position": {"x": 0, "y": 0},
                    "divine_power": 35,
                    "max_divine_power": 50,
                    "spells_known": []
                },
                "entities": {},
                "message_log": []
            }
        }
        
        mock_file = mock_open(read_data=json.dumps(save_data))
        with patch("builtins.open", mock_file):
            new_manager.load_game("test.save")
            
        assert new_manager.current_state.phase == GamePhase.PLAYING
        assert new_manager.current_state.turn.turn_number == 50
        assert new_manager.current_state.player.divine_power == 35
        
    def test_state_change_events(self):
        """Test that state changes emit events."""
        manager = StateManager()
        event_handler = Mock()
        
        # Subscribe to state change events
        manager._event_bus.subscribe("STATE_CHANGE", event_handler)
        
        # Change state
        manager.update_state("player.divine_power", 25)
        
        # Handler should be called
        event_handler.assert_called_once()
        event = event_handler.call_args[0][0]
        assert event.data["field"] == "player.divine_power"
        assert event.data["old_value"] == 50
        assert event.data["new_value"] == 25