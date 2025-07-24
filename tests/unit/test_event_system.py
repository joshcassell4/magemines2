"""Tests for the event system."""

import pytest
from unittest.mock import Mock
from typing import Any, Dict

from magemines.core.events import (
    Event,
    EventBus,
    EventType,
    EventPriority,
    EventHandler,
    GameEvent,
    MoveEvent,
    DamageEvent,
    MessageEvent,
    StateChangeEvent,
)


class TestEvent:
    """Test the base Event class."""
    
    def test_event_creation(self):
        """Test creating a basic event."""
        event = Event(EventType.CUSTOM, {"data": "test"})
        
        assert event.type == EventType.CUSTOM
        assert event.data == {"data": "test"}
        assert event.timestamp > 0
        assert event.handled is False
        
    def test_event_with_priority(self):
        """Test creating event with priority."""
        event = Event(
            EventType.CUSTOM,
            {"data": "test"},
            priority=EventPriority.HIGH
        )
        
        assert event.priority == EventPriority.HIGH
        
    def test_event_mark_handled(self):
        """Test marking event as handled."""
        event = Event(EventType.CUSTOM, {})
        assert event.handled is False
        
        event.mark_handled()
        assert event.handled is True


class TestGameEvents:
    """Test specific game event types."""
    
    def test_move_event(self):
        """Test move event creation."""
        event = MoveEvent(
            entity_id="player",
            from_pos=(10, 10),
            to_pos=(11, 10)
        )
        
        assert event.type == EventType.MOVE
        assert event.entity_id == "player"
        assert event.from_pos == (10, 10)
        assert event.to_pos == (11, 10)
        assert event.data["entity_id"] == "player"
        
    def test_damage_event(self):
        """Test damage event creation."""
        event = DamageEvent(
            source="goblin",
            target="mage_001",
            amount=10,
            damage_type="physical"
        )
        
        assert event.type == EventType.DAMAGE
        assert event.source == "goblin"
        assert event.target == "mage_001"
        assert event.amount == 10
        assert event.damage_type == "physical"
        
    def test_message_event(self):
        """Test message event creation."""
        event = MessageEvent(
            message="Aldric found a healing potion!",
            category="discovery",
            color=(255, 215, 0)
        )
        
        assert event.type == EventType.MESSAGE
        assert event.message == "Aldric found a healing potion!"
        assert event.category == "discovery"
        assert event.color == (255, 215, 0)
        
    def test_state_change_event(self):
        """Test state change event."""
        event = StateChangeEvent(
            entity_id="mage_001",
            old_state="idle",
            new_state="combat"
        )
        
        assert event.type == EventType.STATE_CHANGE
        assert event.entity_id == "mage_001"
        assert event.old_state == "idle"
        assert event.new_state == "combat"


class TestEventBus:
    """Test the event bus system."""
    
    def test_event_bus_creation(self):
        """Test creating an event bus."""
        bus = EventBus()
        assert bus is not None
        assert len(bus._handlers) == 0
        assert len(bus._event_queue) == 0
        
    def test_subscribe_handler(self):
        """Test subscribing to events."""
        bus = EventBus()
        handler = Mock()
        
        bus.subscribe(EventType.MOVE, handler)
        
        assert EventType.MOVE in bus._handlers
        assert handler in [h[1] for h in bus._handlers[EventType.MOVE]]
        
    def test_subscribe_with_priority(self):
        """Test subscription with priority."""
        bus = EventBus()
        high_priority = Mock()
        low_priority = Mock()
        
        bus.subscribe(EventType.MOVE, low_priority, EventPriority.LOW)
        bus.subscribe(EventType.MOVE, high_priority, EventPriority.HIGH)
        
        # High priority should be first
        handlers = bus._handlers[EventType.MOVE]
        assert handlers[0][1] == high_priority
        assert handlers[1][1] == low_priority
        
    def test_unsubscribe_handler(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        handler = Mock()
        
        # Subscribe
        token = bus.subscribe(EventType.MOVE, handler)
        assert handler in [h[1] for h in bus._handlers[EventType.MOVE]]
        
        # Unsubscribe using token
        bus.unsubscribe(token)
        assert handler not in [h[1] for h in bus._handlers.get(EventType.MOVE, [])]
        
    def test_emit_event_immediate(self):
        """Test emitting event with immediate processing."""
        bus = EventBus()
        handler = Mock()
        
        bus.subscribe(EventType.MOVE, handler)
        
        event = MoveEvent("player", (0, 0), (1, 0))
        bus.emit(event, immediate=True)
        
        handler.assert_called_once_with(event)
        
    def test_emit_event_queued(self):
        """Test emitting event to queue."""
        bus = EventBus()
        handler = Mock()
        
        bus.subscribe(EventType.MOVE, handler)
        
        event = MoveEvent("player", (0, 0), (1, 0))
        bus.emit(event, immediate=False)
        
        # Handler not called yet
        handler.assert_not_called()
        
        # Event should be in queue
        assert len(bus._event_queue) == 1
        
        # Process queue
        bus.process_queue()
        handler.assert_called_once_with(event)
        
    def test_event_stops_propagation(self):
        """Test that handled events stop propagation."""
        bus = EventBus()
        
        handler1 = Mock()
        handler2 = Mock()
        
        # Handler1 will mark event as handled
        def handling_handler(event):
            handler1(event)
            event.mark_handled()
            
        bus.subscribe(EventType.MOVE, handling_handler)
        bus.subscribe(EventType.MOVE, handler2)
        
        event = MoveEvent("player", (0, 0), (1, 0))
        bus.emit(event, immediate=True)
        
        handler1.assert_called_once()
        handler2.assert_not_called()  # Should not be called
        
    def test_wildcard_subscription(self):
        """Test subscribing to all events."""
        bus = EventBus()
        handler = Mock()
        
        bus.subscribe(EventType.ALL, handler)
        
        # Should receive all event types
        move_event = MoveEvent("player", (0, 0), (1, 0))
        damage_event = DamageEvent("goblin", "player", 5)
        
        bus.emit(move_event, immediate=True)
        bus.emit(damage_event, immediate=True)
        
        assert handler.call_count == 2
        handler.assert_any_call(move_event)
        handler.assert_any_call(damage_event)
        
    def test_event_filtering(self):
        """Test event handler with filtering."""
        bus = EventBus()
        handler = Mock()
        
        # Only handle player move events
        def filter_func(event):
            return event.entity_id == "player"
            
        bus.subscribe(EventType.MOVE, handler, filter_func=filter_func)
        
        player_move = MoveEvent("player", (0, 0), (1, 0))
        mage_move = MoveEvent("mage_001", (5, 5), (6, 5))
        
        bus.emit(player_move, immediate=True)
        bus.emit(mage_move, immediate=True)
        
        # Only player move should be handled
        handler.assert_called_once_with(player_move)
        
    def test_event_queue_priority(self):
        """Test that queued events are processed by priority."""
        bus = EventBus()
        handler = Mock()
        
        bus.subscribe(EventType.ALL, handler)
        
        # Add events with different priorities
        low_event = Event(EventType.CUSTOM, {"id": "low"}, EventPriority.LOW)
        normal_event = Event(EventType.CUSTOM, {"id": "normal"}, EventPriority.NORMAL)
        high_event = Event(EventType.CUSTOM, {"id": "high"}, EventPriority.HIGH)
        
        # Add in random order
        bus.emit(normal_event, immediate=False)
        bus.emit(low_event, immediate=False)
        bus.emit(high_event, immediate=False)
        
        # Process queue
        bus.process_queue()
        
        # Check order - high, normal, low
        calls = handler.call_args_list
        assert calls[0][0][0].data["id"] == "high"
        assert calls[1][0][0].data["id"] == "normal"
        assert calls[2][0][0].data["id"] == "low"
        
    def test_clear_handlers(self):
        """Test clearing all handlers."""
        bus = EventBus()
        handler1 = Mock()
        handler2 = Mock()
        
        bus.subscribe(EventType.MOVE, handler1)
        bus.subscribe(EventType.DAMAGE, handler2)
        
        bus.clear_handlers()
        
        # No handlers should remain
        assert len(bus._handlers) == 0
        
        # Events should not be handled
        bus.emit(MoveEvent("player", (0, 0), (1, 0)), immediate=True)
        handler1.assert_not_called()
        
    def test_clear_specific_event_handlers(self):
        """Test clearing handlers for specific event type."""
        bus = EventBus()
        move_handler = Mock()
        damage_handler = Mock()
        
        bus.subscribe(EventType.MOVE, move_handler)
        bus.subscribe(EventType.DAMAGE, damage_handler)
        
        # Clear only move handlers
        bus.clear_handlers(EventType.MOVE)
        
        # Move handler should be gone
        bus.emit(MoveEvent("player", (0, 0), (1, 0)), immediate=True)
        move_handler.assert_not_called()
        
        # Damage handler should still work
        bus.emit(DamageEvent("goblin", "player", 5), immediate=True)
        damage_handler.assert_called_once()


class TestEventHandler:
    """Test the EventHandler decorator/class."""
    
    def test_event_handler_decorator(self):
        """Test using EventHandler as a decorator."""
        bus = EventBus()
        
        class GameSystem:
            def __init__(self):
                self.moves_handled = 0
                
            @EventHandler(EventType.MOVE)
            def handle_move(self, event: MoveEvent):
                self.moves_handled += 1
                
        system = GameSystem()
        
        # Register handlers with bus
        bus.register_handlers(system)
        
        # Emit event
        bus.emit(MoveEvent("player", (0, 0), (1, 0)), immediate=True)
        
        assert system.moves_handled == 1
        
    def test_multiple_event_handlers(self):
        """Test class with multiple event handlers."""
        bus = EventBus()
        
        class CombatSystem:
            def __init__(self):
                self.events = []
                
            @EventHandler(EventType.DAMAGE)
            def handle_damage(self, event: DamageEvent):
                self.events.append(("damage", event))
                
            @EventHandler(EventType.STATE_CHANGE)
            def handle_state_change(self, event: StateChangeEvent):
                self.events.append(("state", event))
                
        system = CombatSystem()
        bus.register_handlers(system)
        
        # Emit different events
        damage_event = DamageEvent("goblin", "player", 10)
        state_event = StateChangeEvent("player", "idle", "combat")
        
        bus.emit(damage_event, immediate=True)
        bus.emit(state_event, immediate=True)
        
        assert len(system.events) == 2
        assert system.events[0] == ("damage", damage_event)
        assert system.events[1] == ("state", state_event)


class TestEventIntegration:
    """Test event system integration scenarios."""
    
    def test_turn_based_event_flow(self):
        """Test typical turn-based game event flow."""
        bus = EventBus()
        
        # Track event order
        event_log = []
        
        def log_handler(event_name):
            def handler(event):
                event_log.append(event_name)
            return handler
            
        # Subscribe to different event types
        bus.subscribe(EventType.TURN_START, log_handler("turn_start"))
        bus.subscribe(EventType.MOVE, log_handler("move"))
        bus.subscribe(EventType.DAMAGE, log_handler("damage"))
        bus.subscribe(EventType.MESSAGE, log_handler("message"))
        bus.subscribe(EventType.TURN_END, log_handler("turn_end"))
        
        # Simulate a turn
        bus.emit(Event(EventType.TURN_START, {"turn": 1}), immediate=False)
        bus.emit(MoveEvent("player", (0, 0), (1, 0)), immediate=False)
        bus.emit(DamageEvent("trap", "player", 5), immediate=False)
        bus.emit(MessageEvent("You triggered a trap!"), immediate=False)
        bus.emit(Event(EventType.TURN_END, {"turn": 1}), immediate=False)
        
        # Process all events
        bus.process_queue()
        
        # Check order
        assert event_log == [
            "turn_start",
            "move",
            "damage",
            "message",
            "turn_end"
        ]
        
    def test_event_causes_event_chain(self):
        """Test events that trigger other events."""
        bus = EventBus()
        
        events_processed = []
        
        def damage_handler(event: DamageEvent):
            events_processed.append(f"damage_{event.target}")
            # Damage causes a message
            bus.emit(
                MessageEvent(f"{event.target} takes {event.amount} damage!"),
                immediate=True
            )
            
        def message_handler(event: MessageEvent):
            events_processed.append(f"message_{event.message[:10]}")
            
        bus.subscribe(EventType.DAMAGE, damage_handler)
        bus.subscribe(EventType.MESSAGE, message_handler)
        
        # Initial damage event
        bus.emit(DamageEvent("goblin", "player", 10), immediate=True)
        
        # Should process damage then message
        assert events_processed == [
            "damage_player",
            "message_player tak"
        ]