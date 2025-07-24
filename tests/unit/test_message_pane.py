"""Tests for the scrollable message pane UI component."""

import pytest
from unittest.mock import Mock, patch
from typing import List, Tuple

from magemines.ui.message_pane import (
    Message,
    MessageCategory,
    MessagePane,
    ScrollDirection,
    MessageFilter,
    MessageFormatter,
    WordWrapper,
)
from magemines.core.terminal import (
    Color,
    Position,
    TerminalChar,
    MockTerminal,
)
from magemines.core.events import EventBus, MessageEvent


class TestMessage:
    """Test the Message class."""
    
    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(
            text="You found a healing potion!",
            category=MessageCategory.DISCOVERY,
            turn=10
        )
        
        assert msg.text == "You found a healing potion!"
        assert msg.category == MessageCategory.DISCOVERY
        assert msg.turn == 10
        assert msg.timestamp > 0
        
    def test_message_with_color(self):
        """Test message with custom color."""
        color = Color(255, 215, 0)  # Gold
        msg = Message(
            text="Divine intervention!",
            category=MessageCategory.DIVINE,
            color=color
        )
        
        assert msg.color == color
        
    def test_message_default_color(self):
        """Test message gets default color from category."""
        msg = Message(
            text="Combat started!",
            category=MessageCategory.COMBAT
        )
        
        # Should get combat category default color
        assert msg.color is not None
        assert msg.color == MessageCategory.COMBAT.default_color()
        
    def test_message_formatting(self):
        """Test message formatting with turn number."""
        msg = Message(
            text="Test message",
            category=MessageCategory.GENERAL,
            turn=5
        )
        
        # Test with turn numbers
        formatted = msg.format(show_turn=True)
        assert formatted == "[5] Test message"
        
        # Test without turn numbers
        formatted = msg.format(show_turn=False)
        assert formatted == "Test message"


class TestMessageCategory:
    """Test message categories."""
    
    def test_category_enum(self):
        """Test all message categories exist."""
        assert MessageCategory.GENERAL
        assert MessageCategory.COMBAT
        assert MessageCategory.DISCOVERY
        assert MessageCategory.DIALOGUE
        assert MessageCategory.SPELL
        assert MessageCategory.DIVINE
        assert MessageCategory.WARNING
        assert MessageCategory.ERROR
        assert MessageCategory.SYSTEM
        
    def test_category_colors(self):
        """Test each category has a default color."""
        for category in MessageCategory:
            color = category.default_color()
            assert isinstance(color, Color)
            
    def test_category_display_names(self):
        """Test categories have display names."""
        assert MessageCategory.GENERAL.display_name() == "General"
        assert MessageCategory.COMBAT.display_name() == "Combat"
        assert MessageCategory.DIVINE.display_name() == "Divine"


class TestWordWrapper:
    """Test word wrapping functionality."""
    
    def test_wrap_short_text(self):
        """Test wrapping text shorter than width."""
        wrapper = WordWrapper(width=20)
        lines = wrapper.wrap("Hello world")
        
        assert len(lines) == 1
        assert lines[0] == "Hello world"
        
    def test_wrap_long_text(self):
        """Test wrapping text longer than width."""
        wrapper = WordWrapper(width=10)
        lines = wrapper.wrap("This is a very long message")
        
        assert len(lines) == 3
        assert lines[0] == "This is a"
        assert lines[1] == "very long"
        assert lines[2] == "message"
        
    def test_wrap_with_long_word(self):
        """Test wrapping with word longer than width."""
        wrapper = WordWrapper(width=5)
        lines = wrapper.wrap("Supercalifragilistic")
        
        # Should break the word
        assert len(lines) > 1
        assert all(len(line) <= 5 for line in lines)
        
    def test_wrap_preserves_spaces(self):
        """Test wrapping preserves meaningful spaces."""
        wrapper = WordWrapper(width=25)  # Make it wide enough to fit
        lines = wrapper.wrap("Item:  Healing Potion")
        
        assert len(lines) == 1
        assert "  " in lines[0]  # Double space preserved
        
    def test_wrap_empty_text(self):
        """Test wrapping empty text."""
        wrapper = WordWrapper(width=10)
        lines = wrapper.wrap("")
        
        assert len(lines) == 0


class TestMessageFilter:
    """Test message filtering."""
    
    def test_filter_by_category(self):
        """Test filtering messages by category."""
        messages = [
            Message("Combat!", MessageCategory.COMBAT),
            Message("Hello", MessageCategory.DIALOGUE),
            Message("Spell cast", MessageCategory.SPELL),
            Message("Fight!", MessageCategory.COMBAT),
        ]
        
        filter = MessageFilter(categories=[MessageCategory.COMBAT])
        filtered = filter.apply(messages)
        
        assert len(filtered) == 2
        assert all(msg.category == MessageCategory.COMBAT for msg in filtered)
        
    def test_filter_multiple_categories(self):
        """Test filtering by multiple categories."""
        messages = [
            Message("Combat!", MessageCategory.COMBAT),
            Message("Hello", MessageCategory.DIALOGUE),
            Message("Spell cast", MessageCategory.SPELL),
            Message("Error!", MessageCategory.ERROR),
        ]
        
        filter = MessageFilter(categories=[
            MessageCategory.COMBAT,
            MessageCategory.SPELL
        ])
        filtered = filter.apply(messages)
        
        assert len(filtered) == 2
        assert filtered[0].text == "Combat!"
        assert filtered[1].text == "Spell cast"
        
    def test_filter_by_turn_range(self):
        """Test filtering by turn range."""
        messages = [
            Message("Early", MessageCategory.GENERAL, turn=1),
            Message("Mid", MessageCategory.GENERAL, turn=50),
            Message("Late", MessageCategory.GENERAL, turn=100),
        ]
        
        filter = MessageFilter(min_turn=40, max_turn=80)
        filtered = filter.apply(messages)
        
        assert len(filtered) == 1
        assert filtered[0].text == "Mid"
        
    def test_filter_by_text_search(self):
        """Test filtering by text search."""
        messages = [
            Message("You found gold!", MessageCategory.DISCOVERY),
            Message("Combat started", MessageCategory.COMBAT),
            Message("Found a potion", MessageCategory.DISCOVERY),
        ]
        
        filter = MessageFilter(search_text="found")
        filtered = filter.apply(messages)
        
        assert len(filtered) == 2
        assert "found" in filtered[0].text.lower()
        assert "found" in filtered[1].text.lower()
        
    def test_filter_none_shows_all(self):
        """Test no filter shows all messages."""
        messages = [
            Message("One", MessageCategory.GENERAL),
            Message("Two", MessageCategory.COMBAT),
            Message("Three", MessageCategory.SPELL),
        ]
        
        filter = MessageFilter()  # No filters
        filtered = filter.apply(messages)
        
        assert len(filtered) == 3


class TestMessagePane:
    """Test the message pane UI component."""
    
    def test_message_pane_creation(self):
        """Test creating a message pane."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(
            terminal=terminal,
            position=Position(0, 0),
            width=40,
            height=10,
            max_messages=100
        )
        
        assert pane.width == 40
        assert pane.height == 10
        assert pane.position.x == 0
        assert pane.position.y == 0
        assert pane.max_messages == 100
        assert len(pane.messages) == 0
        
    def test_add_message(self):
        """Test adding messages to pane."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        
        pane.add_message("Hello world", MessageCategory.GENERAL)
        pane.add_message("Combat started", MessageCategory.COMBAT)
        
        assert len(pane.messages) == 2
        assert pane.messages[0].text == "Hello world"
        assert pane.messages[1].text == "Combat started"
        
    def test_message_limit(self):
        """Test message buffer limit."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 40, 10, max_messages=5)
        
        # Add more than max messages
        for i in range(10):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
            
        # Should only keep last 5
        assert len(pane.messages) == 5
        assert pane.messages[0].text == "Message 5"
        assert pane.messages[-1].text == "Message 9"
        
    def test_render_empty_pane(self):
        """Test rendering empty message pane."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(10, 5), 20, 5)
        
        pane.render()
        
        # Should draw border
        screen = terminal.get_screen_content()
        
        # Check corners
        assert screen[5][10] == "┌"
        assert screen[5][29] == "┐"
        assert screen[9][10] == "└"
        assert screen[9][29] == "┘"
        
        # Check title
        title_start = 11
        for i, char in enumerate("Messages"):
            assert screen[5][title_start + i] == char
            
    def test_render_messages(self):
        """Test rendering messages in pane."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 30, 6)
        
        pane.add_message("First message", MessageCategory.GENERAL)
        pane.add_message("Second message", MessageCategory.COMBAT)
        
        pane.render()
        
        screen = terminal.get_screen_content()
        
        # Messages should appear inside border (1 char padding)
        # First message at y=1 (inside border)
        assert "First message" in screen[1]
        assert "Second message" in screen[2]
        
    def test_scroll_up(self):
        """Test scrolling up through messages."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 30, 5)
        
        # Add more messages than can fit (3 lines for messages in 5-line pane)
        for i in range(10):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
            
        # Initially shows latest messages
        pane.render()
        assert pane.scroll_offset == 0
        
        # Scroll up
        pane.scroll(ScrollDirection.UP, lines=3)
        assert pane.scroll_offset == 3
        
        pane.render()
        screen = terminal.get_screen_content()
        
        # Should show earlier messages
        assert "Message 4" in screen[1]  # Instead of Message 7
        
    def test_scroll_down(self):
        """Test scrolling down through messages."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 30, 5)
        
        # Add messages and scroll up first
        for i in range(10):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
            
        pane.scroll(ScrollDirection.UP, lines=5)
        assert pane.scroll_offset == 5
        
        # Now scroll down
        pane.scroll(ScrollDirection.DOWN, lines=2)
        assert pane.scroll_offset == 3
        
    def test_scroll_limits(self):
        """Test scroll limits."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 30, 5)
        
        # Add 5 messages
        for i in range(5):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
            
        # Can't scroll down from bottom
        pane.scroll(ScrollDirection.DOWN, lines=1)
        assert pane.scroll_offset == 0
        
        # Can scroll up
        pane.scroll(ScrollDirection.UP, lines=10)  # Try to scroll too far
        # Should stop at max valid offset
        assert pane.scroll_offset == 2  # 5 messages - 3 visible lines
        
    def test_word_wrap_in_pane(self):
        """Test word wrapping in message pane."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 20, 5)
        
        # Add long message that needs wrapping
        pane.add_message(
            "This is a very long message that needs to be wrapped",
            MessageCategory.GENERAL
        )
        
        pane.render()
        
        # Message should be wrapped across multiple lines
        assert len(pane._get_wrapped_messages()) > 1
        
    def test_colored_messages(self):
        """Test rendering colored messages."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 30, 5)
        
        # Add messages with different categories
        pane.add_message("Combat!", MessageCategory.COMBAT)
        pane.add_message("Found gold!", MessageCategory.DISCOVERY)
        
        pane.render()
        
        # Check that colors were applied
        operations = terminal.operations
        
        # Should have write operations with colors
        colored_writes = [
            op for op in operations 
            if op.get('type') == 'write_char' and op.get('char') and op['char'].fg != Color(255, 255, 255)
        ]
        
        assert len(colored_writes) > 0
        
    def test_filter_integration(self):
        """Test filtering messages in pane."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 30, 5)
        
        # Add various messages
        pane.add_message("Combat started", MessageCategory.COMBAT)
        pane.add_message("Hello there", MessageCategory.DIALOGUE)
        pane.add_message("Spell cast", MessageCategory.SPELL)
        pane.add_message("Enemy attacks", MessageCategory.COMBAT)
        
        # Apply combat filter
        filter = MessageFilter(categories=[MessageCategory.COMBAT])
        pane.set_filter(filter)
        
        # Should only show combat messages
        visible = pane._get_visible_messages()
        assert len(visible) == 2
        assert all(msg.category == MessageCategory.COMBAT for msg in visible)
        
    def test_event_integration(self):
        """Test integration with event system."""
        terminal = MockTerminal(80, 24)
        event_bus = EventBus()
        
        pane = MessagePane(
            terminal=terminal,
            position=Position(0, 0),
            width=30,
            height=5,
            event_bus=event_bus
        )
        
        # Emit message event
        event = MessageEvent(
            message="Event-based message!",
            category="discovery",
            color=(255, 215, 0)
        )
        
        event_bus.emit(event, immediate=True)
        
        # Message should appear in pane
        assert len(pane.messages) == 1
        assert pane.messages[0].text == "Event-based message!"
        assert pane.messages[0].category == MessageCategory.DISCOVERY
        assert pane.messages[0].color == Color(255, 215, 0)
        
    def test_scroll_indicators(self):
        """Test scroll position indicators."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 30, 5)
        
        # Add many messages
        for i in range(20):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
            
        pane.render()
        
        # Should show scroll indicator at bottom
        screen = terminal.get_screen_content()
        
        # Look for up arrow indicator when scrollable (height-2 = 3)
        bottom_right = screen[3][28] if len(screen[3]) > 28 else ""  # Inside border
        assert bottom_right == "▲" or bottom_right == "↑"
        
        # Scroll up
        pane.scroll(ScrollDirection.UP, lines=5)
        pane.render()
        
        # Should show both indicators
        screen = terminal.get_screen_content()
        indicator = screen[3][28] if len(screen[3]) > 28 else ""
        assert indicator == "▼" or indicator == "↓"
        
    def test_page_up_down(self):
        """Test page up/down functionality."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 30, 10)
        
        # Add many messages
        for i in range(50):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
            
        # Page up should scroll by visible height
        visible_lines = pane.height - 2  # Minus border
        pane.page_up()
        
        assert pane.scroll_offset == visible_lines
        
        # Page down should scroll back
        pane.page_down()
        assert pane.scroll_offset == 0
        
    def test_home_end_keys(self):
        """Test home/end key functionality."""
        terminal = MockTerminal(80, 24)
        pane = MessagePane(terminal, Position(0, 0), 30, 5)
        
        # Add messages
        for i in range(20):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
            
        # Home should go to oldest
        pane.scroll_to_top()
        assert pane.scroll_offset == pane._max_scroll_offset()
        
        # End should go to newest
        pane.scroll_to_bottom()
        assert pane.scroll_offset == 0