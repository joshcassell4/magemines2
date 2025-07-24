"""Event system for turn-based game mechanics."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import heapq


class EventType(Enum):
    """Types of events in the game."""
    # Core events
    CUSTOM = auto()
    ALL = auto()  # Wildcard for subscribing to all events
    
    # Game events
    MOVE = auto()
    DAMAGE = auto()
    MESSAGE = auto()
    STATE_CHANGE = auto()
    TURN_START = auto()
    TURN_END = auto()
    
    # Entity events
    SPAWN = auto()
    DEATH = auto()
    LEVEL_UP = auto()
    
    # Item events
    PICKUP = auto()
    DROP = auto()
    USE = auto()
    
    # World events
    TILE_CHANGE = auto()
    WEATHER_CHANGE = auto()
    TIME_CHANGE = auto()


class EventPriority(Enum):
    """Priority levels for event handling."""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0
    
    def __lt__(self, other):
        """Allow priority comparison for sorting."""
        if isinstance(other, EventPriority):
            return self.value < other.value
        return NotImplemented


@dataclass
class Event:
    """Base event class."""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    handled: bool = False
    _sequence: int = field(default=0, init=False)
    
    def mark_handled(self) -> None:
        """Mark this event as handled to stop propagation."""
        self.handled = True
    
    def __lt__(self, other):
        """Allow event comparison for priority queue."""
        if isinstance(other, Event):
            # First by priority, then by sequence to maintain FIFO
            if self.priority != other.priority:
                return self.priority < other.priority
            return self._sequence < other._sequence
        return NotImplemented


# Specific game event types

class GameEvent(Event):
    """Base class for game-specific events."""
    pass


class MoveEvent(GameEvent):
    """Event for entity movement."""
    
    def __init__(self, entity_id: str, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        """Initialize move event."""
        super().__init__(EventType.MOVE, {
            "entity_id": entity_id,
            "from_pos": from_pos,
            "to_pos": to_pos
        })
        self.entity_id = entity_id
        self.from_pos = from_pos
        self.to_pos = to_pos


class DamageEvent(GameEvent):
    """Event for damage dealt."""
    
    def __init__(self, source: str, target: str, amount: int, damage_type: str = "physical"):
        """Initialize damage event."""
        super().__init__(EventType.DAMAGE, {
            "source": source,
            "target": target,
            "amount": amount,
            "damage_type": damage_type
        })
        self.source = source
        self.target = target
        self.amount = amount
        self.damage_type = damage_type


class MessageEvent(GameEvent):
    """Event for game messages."""
    
    def __init__(self, message: str, category: str = "general", color: Optional[Tuple[int, int, int]] = None):
        """Initialize message event."""
        super().__init__(EventType.MESSAGE, {
            "message": message,
            "category": category,
            "color": color
        })
        self.message = message
        self.category = category
        self.color = color


class StateChangeEvent(GameEvent):
    """Event for entity state changes."""
    
    def __init__(self, entity_id: str, old_state: str, new_state: str):
        """Initialize state change event."""
        super().__init__(EventType.STATE_CHANGE, {
            "entity_id": entity_id,
            "old_state": old_state,
            "new_state": new_state
        })
        self.entity_id = entity_id
        self.old_state = old_state
        self.new_state = new_state


# Event handling infrastructure

HandlerFunc = Callable[[Event], None]
FilterFunc = Callable[[Event], bool]


class EventBus:
    """Central event bus for game event management."""
    
    def __init__(self):
        """Initialize empty event bus."""
        # Dict of event_type -> list of (priority, handler, filter_func, token)
        self._handlers: Dict[EventType, List[Tuple[EventPriority, HandlerFunc, Optional[FilterFunc], str]]] = {}
        # Priority queue of events to process
        self._event_queue: List[Event] = []
        # Token counter for subscription tracking
        self._token_counter = 0
        # Sequence counter for FIFO ordering
        self._sequence_counter = 0
        
    def subscribe(
        self,
        event_type: EventType,
        handler: HandlerFunc,
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[FilterFunc] = None
    ) -> str:
        """Subscribe a handler to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Function to call when event occurs
            priority: Priority for handler ordering
            filter_func: Optional filter to check before calling handler
            
        Returns:
            Token that can be used to unsubscribe
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        # Generate unique token
        self._token_counter += 1
        token = f"sub_{self._token_counter}"
        
        # Add handler with priority
        handler_entry = (priority, handler, filter_func, token)
        self._handlers[event_type].append(handler_entry)
        
        # Sort by priority (lower value = higher priority)
        self._handlers[event_type].sort(key=lambda x: x[0].value)
        
        return token
    
    def unsubscribe(self, token: str) -> bool:
        """Unsubscribe a handler using its token.
        
        Args:
            token: Subscription token returned from subscribe
            
        Returns:
            True if handler was found and removed
        """
        for event_type, handlers in self._handlers.items():
            for i, (_, _, _, handler_token) in enumerate(handlers):
                if handler_token == token:
                    handlers.pop(i)
                    return True
        return False
    
    def emit(self, event: Event, immediate: bool = False) -> None:
        """Emit an event.
        
        Args:
            event: Event to emit
            immediate: If True, process immediately; if False, queue for later
        """
        # Assign sequence number for FIFO ordering
        event._sequence = self._sequence_counter
        self._sequence_counter += 1
        
        if immediate:
            self._process_event(event)
        else:
            heapq.heappush(self._event_queue, event)
    
    def process_queue(self, max_events: Optional[int] = None) -> int:
        """Process queued events.
        
        Args:
            max_events: Maximum number of events to process (None = all)
            
        Returns:
            Number of events processed
        """
        processed = 0
        while self._event_queue and (max_events is None or processed < max_events):
            event = heapq.heappop(self._event_queue)
            self._process_event(event)
            processed += 1
        return processed
    
    def _process_event(self, event: Event) -> None:
        """Process a single event."""
        # Get handlers for specific event type
        handlers = self._handlers.get(event.type, [])
        
        # Also get handlers subscribed to ALL events
        all_handlers = self._handlers.get(EventType.ALL, [])
        
        # Combine and sort all applicable handlers
        combined_handlers = list(handlers) + list(all_handlers)
        combined_handlers.sort(key=lambda x: x[0].value)
        
        # Call each handler
        for priority, handler, filter_func, token in combined_handlers:
            # Check if event is already handled
            if event.handled:
                break
                
            # Apply filter if present
            if filter_func and not filter_func(event):
                continue
                
            # Call handler
            handler(event)
    
    def clear_handlers(self, event_type: Optional[EventType] = None) -> None:
        """Clear handlers.
        
        Args:
            event_type: If specified, only clear handlers for this type.
                       If None, clear all handlers.
        """
        if event_type is None:
            self._handlers.clear()
        else:
            self._handlers.pop(event_type, None)
    
    def register_handlers(self, obj: Any) -> List[str]:
        """Register all EventHandler decorated methods from an object.
        
        Args:
            obj: Object to scan for EventHandler decorators
            
        Returns:
            List of subscription tokens
        """
        tokens = []
        
        # Scan object for methods with _event_handler attribute
        for attr_name in dir(obj):
            attr = getattr(obj, attr_name)
            if hasattr(attr, '_event_handler_info'):
                info = attr._event_handler_info
                token = self.subscribe(
                    info['event_type'],
                    attr,
                    info['priority'],
                    info['filter_func']
                )
                tokens.append(token)
        
        return tokens


def EventHandler(
    event_type: EventType,
    priority: EventPriority = EventPriority.NORMAL,
    filter_func: Optional[FilterFunc] = None
):
    """Decorator to mark a method as an event handler.
    
    Args:
        event_type: Type of event this handler processes
        priority: Priority for handler ordering
        filter_func: Optional filter function
    """
    def decorator(func):
        # Store handler info on the function
        func._event_handler_info = {
            'event_type': event_type,
            'priority': priority,
            'filter_func': filter_func
        }
        return func
    
    return decorator