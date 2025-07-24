"""Game state management system."""

import json
import time
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from copy import deepcopy

from .events import EventBus, Event, EventType


class GamePhase(Enum):
    """Game phases/screens."""
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class StateValidationError(Exception):
    """Raised when state validation fails."""
    pass


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


@dataclass
class Position:
    """2D position in the game world."""
    x: int
    y: int
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'Position':
        """Create from dictionary."""
        return cls(x=data["x"], y=data["y"])


@dataclass
class PlayerState:
    """State of the player/god."""
    position: Position = field(default_factory=lambda: Position(0, 0))
    divine_power: int = 50
    max_divine_power: int = 50
    spells_known: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "position": self.position.to_dict(),
            "divine_power": self.divine_power,
            "max_divine_power": self.max_divine_power,
            "spells_known": self.spells_known.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerState':
        """Create from dictionary."""
        return cls(
            position=Position.from_dict(data.get("position", {"x": 0, "y": 0})),
            divine_power=data.get("divine_power", 50),
            max_divine_power=data.get("max_divine_power", 50),
            spells_known=data.get("spells_known", []).copy()
        )


@dataclass
class EntityState:
    """State of a game entity (mage, monster, etc)."""
    id: str
    type: str
    position: Position = field(default_factory=lambda: Position(0, 0))
    health: int = 100
    max_health: int = 100
    data: Dict[str, Any] = field(default_factory=dict)  # Type-specific data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "position": self.position.to_dict(),
            "health": self.health,
            "max_health": self.max_health,
            "data": self.data.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityState':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            position=Position.from_dict(data["position"]),
            health=data["health"],
            max_health=data["max_health"],
            data=data.get("data", {}).copy()
        )


@dataclass
class WorldState:
    """State of the game world."""
    current_level: int = 1
    seed: int = field(default_factory=lambda: random.randint(0, 2**32))
    discovered_tiles: Set[Tuple[int, int]] = field(default_factory=set)
    level_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "current_level": self.current_level,
            "seed": self.seed,
            "discovered_tiles": [list(tile) for tile in self.discovered_tiles],  # Convert set of tuples to list of lists
            "level_data": self.level_data.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorldState':
        """Create from dictionary."""
        # Convert list of lists back to set of tuples
        discovered = set()
        for tile in data.get("discovered_tiles", []):
            discovered.add(tuple(tile))
            
        return cls(
            current_level=data["current_level"],
            seed=data["seed"],
            discovered_tiles=discovered,
            level_data=data.get("level_data", {}).copy()
        )


@dataclass
class TurnState:
    """State of the current turn."""
    turn_number: int = 0
    current_phase: str = "player_action"  # player_action, entity_action, environment
    entities_acted: List[str] = field(default_factory=list)
    
    def next_turn(self) -> None:
        """Advance to the next turn."""
        self.turn_number += 1
        self.current_phase = "player_action"
        self.entities_acted.clear()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "turn_number": self.turn_number,
            "current_phase": self.current_phase,
            "entities_acted": self.entities_acted.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TurnState':
        """Create from dictionary."""
        return cls(
            turn_number=data.get("turn_number", 0),
            current_phase=data.get("current_phase", "player_action"),
            entities_acted=data.get("entities_acted", []).copy()
        )


@dataclass
class GameState:
    """Complete game state."""
    phase: GamePhase = GamePhase.MENU
    turn: TurnState = field(default_factory=TurnState)
    world: WorldState = field(default_factory=WorldState)
    player: PlayerState = field(default_factory=PlayerState)
    entities: Dict[str, EntityState] = field(default_factory=dict)
    message_log: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_entity(self, entity: EntityState) -> None:
        """Add an entity to the game."""
        self.entities[entity.id] = entity
        
    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from the game."""
        self.entities.pop(entity_id, None)
        
    def get_entity(self, entity_id: str) -> Optional[EntityState]:
        """Get an entity by ID."""
        return self.entities.get(entity_id)
        
    def add_message(self, message: str, category: str = "general") -> None:
        """Add a message to the log."""
        self.message_log.append({
            "turn": self.turn.turn_number,
            "message": message,
            "category": category,
            "timestamp": time.time()
        })
        
        # Limit message log size
        if len(self.message_log) > 1000:
            self.message_log = self.message_log[-1000:]


@dataclass
class StateTransition:
    """Represents a valid state transition."""
    from_phase: GamePhase
    to_phase: GamePhase
    validator: Optional[Callable[[GameState], bool]] = None
    
    def is_valid(self) -> bool:
        """Check if this transition is structurally valid."""
        # Define valid transitions
        valid_transitions = {
            GamePhase.MENU: [GamePhase.PLAYING],
            GamePhase.PLAYING: [GamePhase.PAUSED, GamePhase.GAME_OVER, GamePhase.VICTORY],
            GamePhase.PAUSED: [GamePhase.PLAYING, GamePhase.MENU],
            GamePhase.GAME_OVER: [GamePhase.MENU],
            GamePhase.VICTORY: [GamePhase.MENU],
        }
        
        return self.to_phase in valid_transitions.get(self.from_phase, [])
        
    def can_transition(self, state: GameState) -> bool:
        """Check if transition is allowed given current state."""
        if not self.is_valid():
            return False
            
        if self.validator:
            return self.validator(state)
            
        return True


@dataclass
class SaveMetadata:
    """Metadata for a saved game."""
    version: str = "1.0.0"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    turn: int = 0
    play_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SaveMetadata':
        """Create from dictionary."""
        return cls(**data)


class StateSerializer:
    """Handles serialization of game state."""
    
    def serialize(self, state: GameState) -> Dict[str, Any]:
        """Serialize game state to dictionary."""
        return {
            "phase": state.phase.name,
            "turn": state.turn.to_dict(),
            "world": state.world.to_dict(),
            "player": state.player.to_dict(),
            "entities": {
                id: entity.to_dict() 
                for id, entity in state.entities.items()
            },
            "message_log": state.message_log.copy()
        }
    
    def deserialize(self, data: Dict[str, Any]) -> GameState:
        """Deserialize game state from dictionary."""
        state = GameState(
            phase=GamePhase[data["phase"]],
            turn=TurnState.from_dict(data["turn"]),
            world=WorldState.from_dict(data["world"]),
            player=PlayerState.from_dict(data["player"])
        )
        
        # Add entities
        for entity_data in data.get("entities", {}).values():
            state.add_entity(EntityState.from_dict(entity_data))
            
        # Add messages
        state.message_log = data.get("message_log", []).copy()
        
        return state
    
    def save_to_file(self, state: GameState, filepath: str) -> SaveMetadata:
        """Save game state to file."""
        metadata = SaveMetadata(
            turn=state.turn.turn_number,
            # In a real game, track actual play time
            play_time=state.turn.turn_number * 5.0  # Estimate 5 seconds per turn
        )
        
        save_data = {
            "metadata": metadata.to_dict(),
            "state": self.serialize(state)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2)
            
        return metadata
    
    def load_from_file(self, filepath: str) -> Tuple[GameState, SaveMetadata]:
        """Load game state from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
            
        metadata = SaveMetadata.from_dict(save_data["metadata"])
        state = self.deserialize(save_data["state"])
        
        return state, metadata


class StateManager:
    """Manages game state and transitions."""
    
    def __init__(self, initial_state: Optional[GameState] = None):
        """Initialize state manager."""
        self.current_state = initial_state or GameState()
        self._event_bus = EventBus()
        self._snapshots: Dict[str, GameState] = {}
        self._serializer = StateSerializer()
        
    def transition_phase(self, new_phase: GamePhase) -> None:
        """Transition to a new game phase."""
        transition = StateTransition(
            from_phase=self.current_state.phase,
            to_phase=new_phase
        )
        
        if not transition.can_transition(self.current_state):
            raise StateTransitionError(
                f"Cannot transition from {self.current_state.phase} to {new_phase}"
            )
            
        old_phase = self.current_state.phase
        self.current_state.phase = new_phase
        
        # Emit phase change event
        self._emit_state_change("phase", old_phase, new_phase)
        
    def update_state(self, field_path: str, value: Any) -> None:
        """Update a field in the game state."""
        # Parse field path (e.g., "player.divine_power")
        parts = field_path.split('.')
        obj = self.current_state
        
        # Navigate to parent object
        for part in parts[:-1]:
            obj = getattr(obj, part)
            
        # Get old value
        old_value = getattr(obj, parts[-1])
        
        # Set new value
        setattr(obj, parts[-1], value)
        
        # Emit state change event
        self._emit_state_change(field_path, old_value, value)
        
    def validate_state(self) -> bool:
        """Validate current game state."""
        try:
            # Basic validation rules
            if self.current_state.player.divine_power < 0:
                return False
                
            if self.current_state.player.divine_power > self.current_state.player.max_divine_power:
                return False
                
            if self.current_state.world.current_level < 1:
                return False
                
            if self.current_state.turn.turn_number < 0:
                return False
                
            # All entities should have valid positions and health
            for entity in self.current_state.entities.values():
                if entity.health < 0 or entity.health > entity.max_health:
                    return False
                    
            return True
            
        except Exception:
            return False
            
    def take_snapshot(self, name: str) -> None:
        """Take a snapshot of current state."""
        self._snapshots[name] = deepcopy(self.current_state)
        
    def restore_snapshot(self, name: str) -> None:
        """Restore a saved snapshot."""
        if name not in self._snapshots:
            raise KeyError(f"No snapshot named '{name}'")
            
        self.current_state = deepcopy(self._snapshots[name])
        
    def save_game(self, filepath: str) -> None:
        """Save current game to file."""
        self._serializer.save_to_file(self.current_state, filepath)
        
    def load_game(self, filepath: str) -> None:
        """Load game from file."""
        state, metadata = self._serializer.load_from_file(filepath)
        self.current_state = state
        
    def _emit_state_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """Emit a state change event."""
        event = Event(
            type="STATE_CHANGE",  # Using string since we can't import EventType here
            data={
                "field": field,
                "old_value": old_value,
                "new_value": new_value
            }
        )
        self._event_bus.emit(event, immediate=True)