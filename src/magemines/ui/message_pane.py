"""Scrollable message pane UI component."""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Set, Tuple

from ..core.terminal import (
    Color,
    Position, 
    TerminalChar,
    TerminalInterface,
)
from ..core.events import EventBus, EventHandler, EventType, MessageEvent


class MessageCategory(Enum):
    """Categories for messages with associated colors."""
    GENERAL = auto()
    COMBAT = auto()
    DISCOVERY = auto()
    DIALOGUE = auto()
    SPELL = auto()
    DIVINE = auto()
    WARNING = auto()
    ERROR = auto()
    SYSTEM = auto()
    
    def default_color(self) -> Color:
        """Get default color for this category."""
        colors = {
            MessageCategory.GENERAL: Color(192, 192, 192),  # Light gray
            MessageCategory.COMBAT: Color(255, 100, 100),   # Light red
            MessageCategory.DISCOVERY: Color(255, 215, 0),   # Gold
            MessageCategory.DIALOGUE: Color(100, 200, 255), # Light blue
            MessageCategory.SPELL: Color(200, 100, 255),    # Purple
            MessageCategory.DIVINE: Color(255, 255, 100),   # Bright yellow
            MessageCategory.WARNING: Color(255, 165, 0),    # Orange
            MessageCategory.ERROR: Color(255, 0, 0),        # Red
            MessageCategory.SYSTEM: Color(128, 128, 128),   # Gray
        }
        return colors.get(self, Color(192, 192, 192))
    
    def display_name(self) -> str:
        """Get display name for this category."""
        return self.name.capitalize()


class ScrollDirection(Enum):
    """Scroll directions."""
    UP = auto()
    DOWN = auto()


@dataclass
class Message:
    """A single message with metadata."""
    text: str
    category: MessageCategory
    turn: int = 0
    timestamp: float = field(default_factory=time.time)
    color: Optional[Color] = None
    
    def __post_init__(self):
        """Set default color if not provided."""
        if self.color is None:
            self.color = self.category.default_color()
    
    def format(self, show_turn: bool = True) -> str:
        """Format message for display."""
        if show_turn and self.category != MessageCategory.SYSTEM:
            return f"[T{self.turn}] {self.text}"
        return self.text


class WordWrapper:
    """Handles word wrapping for messages."""
    
    def __init__(self, width: int):
        """Initialize word wrapper with max width."""
        self.width = width
        
    def wrap(self, text: str) -> List[str]:
        """Wrap text to fit within width."""
        if not text:
            return []
        
        lines = []
        current_line = ""
        
        # Process character by character to preserve spaces
        i = 0
        while i < len(text):
            # Find next word boundary
            word_start = i
            while i < len(text) and text[i] != ' ':
                i += 1
            word = text[word_start:i]
            
            # Include trailing spaces
            space_start = i
            while i < len(text) and text[i] == ' ':
                i += 1
            spaces = text[space_start:i]
            
            # Check if word fits on current line
            if not current_line:
                # First word on line
                if len(word) > self.width:
                    # Break long word
                    for j in range(0, len(word), self.width):
                        lines.append(word[j:j+self.width])
                    current_line = ""
                else:
                    current_line = word + spaces
            else:
                # Check if adding word exceeds width
                if len(current_line) + len(word) <= self.width:
                    current_line += word + spaces
                else:
                    # Start new line
                    lines.append(current_line.rstrip())
                    if len(word) > self.width:
                        # Break long word
                        for j in range(0, len(word), self.width):
                            lines.append(word[j:j+self.width])
                        current_line = ""
                    else:
                        current_line = word + spaces
        
        # Add remaining line
        if current_line.strip():
            lines.append(current_line.rstrip())
            
        return lines


@dataclass
class MessageFilter:
    """Filter for messages."""
    categories: Optional[List[MessageCategory]] = None
    min_turn: Optional[int] = None
    max_turn: Optional[int] = None
    search_text: Optional[str] = None
    
    def apply(self, messages: List[Message]) -> List[Message]:
        """Apply filter to messages."""
        filtered = messages
        
        # Filter by categories
        if self.categories:
            filtered = [m for m in filtered if m.category in self.categories]
            
        # Filter by turn range
        if self.min_turn is not None:
            filtered = [m for m in filtered if m.turn >= self.min_turn]
        if self.max_turn is not None:
            filtered = [m for m in filtered if m.turn <= self.max_turn]
            
        # Filter by search text
        if self.search_text:
            search_lower = self.search_text.lower()
            filtered = [m for m in filtered if search_lower in m.text.lower()]
            
        return filtered


class MessageFormatter:
    """Formats messages for display."""
    pass  # Not used in tests yet


class MessagePane:
    """Scrollable message pane UI component."""
    
    def __init__(
        self,
        terminal: TerminalInterface,
        position: Position,
        width: int,
        height: int,
        max_messages: int = 1000,
        event_bus: Optional[EventBus] = None
    ):
        """Initialize message pane."""
        self.terminal = terminal
        self.position = position
        self.width = width
        self.height = height
        self.max_messages = max_messages
        self.messages: List[Message] = []
        self.scroll_offset = 0  # 0 = showing latest messages
        self._filter: Optional[MessageFilter] = None
        self._event_bus = event_bus
        self._current_turn = 0
        
        # Cache for wrapped messages and dirty tracking
        self._wrapped_cache: Optional[List[Tuple[str, Color]]] = None
        self._last_visible_lines: Optional[List[Tuple[str, Color]]] = None
        self._needs_full_redraw = True
        self._border_drawn = False
        
        # Subscribe to message events if event bus provided
        if self._event_bus:
            self._event_bus.subscribe(EventType.MESSAGE, self._handle_message_event)
    
    def add_message(
        self, 
        text: str, 
        category: MessageCategory,
        turn: Optional[int] = None,
        color: Optional[Color] = None
    ) -> None:
        """Add a message to the pane."""
        message = Message(
            text=text,
            category=category,
            turn=turn or self._current_turn,
            color=color
        )
        
        self.messages.append(message)
        
        # Trim to max messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
            
        # Always reset scroll to show new message
        self.scroll_offset = 0
        
        # Invalidate cache when new message added
        self._wrapped_cache = None
        self._needs_full_redraw = True
    
    def set_filter(self, filter: Optional[MessageFilter]) -> None:
        """Set message filter."""
        self._filter = filter
        self.scroll_offset = 0  # Reset scroll when filtering
        self._wrapped_cache = None
        self._needs_full_redraw = True
    
    def scroll(self, direction: ScrollDirection, lines: int = 1) -> None:
        """Scroll the message view."""
        old_offset = self.scroll_offset
        if direction == ScrollDirection.UP:
            self.scroll_offset = min(
                self.scroll_offset + lines,
                self._max_scroll_offset()
            )
        else:  # DOWN
            self.scroll_offset = max(0, self.scroll_offset - lines)
        
        # Only trigger redraw if scroll actually changed
        if old_offset != self.scroll_offset:
            self._needs_full_redraw = True
    
    def page_up(self) -> None:
        """Scroll up by one page."""
        visible_lines = self.height - 2  # Minus border
        self.scroll(ScrollDirection.UP, visible_lines)
    
    def page_down(self) -> None:
        """Scroll down by one page."""
        visible_lines = self.height - 2  # Minus border
        self.scroll(ScrollDirection.DOWN, visible_lines)
    
    def scroll_to_top(self) -> None:
        """Scroll to oldest messages."""
        self.scroll_offset = self._max_scroll_offset()
    
    def scroll_to_bottom(self) -> None:
        """Scroll to newest messages."""
        self.scroll_offset = 0
    
    def render(self) -> None:
        """Render the message pane."""
        # Draw border only once
        if not self._border_drawn:
            self._draw_border()
            self._border_drawn = True
            self._needs_full_redraw = True
        
        # Check if we need to redraw messages
        if not self._needs_full_redraw:
            return
        
        # Get wrapped messages (uses cache if available)
        wrapped_messages = self._get_wrapped_messages()
        total_lines = len(wrapped_messages)
        visible_lines = self.height - 2
        
        # Calculate which lines to show
        if self.scroll_offset > 0:
            start_idx = total_lines - visible_lines - self.scroll_offset
            end_idx = start_idx + visible_lines
            lines_to_show = wrapped_messages[start_idx:end_idx]
        else:
            # Show latest messages
            lines_to_show = wrapped_messages[-visible_lines:]
        
        # Only redraw if content changed
        if lines_to_show != self._last_visible_lines:
            # Draw the lines
            y = self.position.y + 1  # Inside border
            for i in range(visible_lines):
                # Get the line content or clear if no content
                if i < len(lines_to_show):
                    line, color = lines_to_show[i]
                else:
                    line, color = "", Color.WHITE
                
                # Only redraw this line if it changed
                old_line = self._last_visible_lines[i] if self._last_visible_lines and i < len(self._last_visible_lines) else ("", Color.WHITE)
                if (line, color) != old_line:
                    # Clear the line first
                    for x in range(self.position.x + 1, self.position.x + self.width - 1):
                        self.terminal.write_char(Position(x, y + i), TerminalChar(' '))
                    
                    # Write the text
                    x = self.position.x + 1
                    for char in line[:self.width - 2]:  # Ensure it fits
                        self.terminal.write_char(
                            Position(x, y + i),
                            TerminalChar(char, color)
                        )
                        x += 1
            
            self._last_visible_lines = lines_to_show
        
        # Draw scroll indicators
        self._draw_scroll_indicators()
        
        # Reset redraw flag
        self._needs_full_redraw = False
    
    def _draw_border(self) -> None:
        """Draw the pane border."""
        # Use ASCII characters for better compatibility
        # Corners
        self.terminal.write_char(
            Position(self.position.x, self.position.y),
            TerminalChar('+')
        )
        self.terminal.write_char(
            Position(self.position.x + self.width - 1, self.position.y),
            TerminalChar('+')
        )
        self.terminal.write_char(
            Position(self.position.x, self.position.y + self.height - 1),
            TerminalChar('+')
        )
        self.terminal.write_char(
            Position(self.position.x + self.width - 1, self.position.y + self.height - 1),
            TerminalChar('+')
        )
        
        # Horizontal lines
        for x in range(self.position.x + 1, self.position.x + self.width - 1):
            self.terminal.write_char(
                Position(x, self.position.y),
                TerminalChar('-')
            )
            self.terminal.write_char(
                Position(x, self.position.y + self.height - 1),
                TerminalChar('-')
            )
        
        # Vertical lines
        for y in range(self.position.y + 1, self.position.y + self.height - 1):
            self.terminal.write_char(
                Position(self.position.x, y),
                TerminalChar('|')
            )
            self.terminal.write_char(
                Position(self.position.x + self.width - 1, y),
                TerminalChar('|')
            )
        
        # Title
        title = " Messages "
        title_x = self.position.x + (self.width - len(title)) // 2
        for i, char in enumerate(title):
            if title_x + i >= self.position.x + self.width - 1:
                break
            self.terminal.write_char(
                Position(title_x + i, self.position.y),
                TerminalChar(char, Color(255, 255, 100))  # Bright yellow for title
            )
    
    def _draw_scroll_indicators(self) -> None:
        """Draw scroll position indicators."""
        wrapped_messages = self._get_wrapped_messages()
        total_lines = len(wrapped_messages)
        visible_lines = self.height - 2
        
        if total_lines <= visible_lines:
            return  # No scrolling needed
        
        # Can scroll up? (older messages)
        if self.scroll_offset < self._max_scroll_offset():
            self.terminal.write_char(
                Position(self.position.x + self.width - 2, self.position.y + 1),
                TerminalChar('^')
            )
        
        # Can scroll down? (newer messages)
        if self.scroll_offset > 0:
            self.terminal.write_char(
                Position(self.position.x + self.width - 2, self.position.y + self.height - 2),
                TerminalChar('v')
            )
    
    def _get_visible_messages(self) -> List[Message]:
        """Get messages that should be visible (after filtering)."""
        messages = self.messages
        
        if self._filter:
            messages = self._filter.apply(messages)
            
        return messages
    
    def _get_wrapped_messages(self) -> List[Tuple[str, Color]]:
        """Get all messages wrapped to fit width."""
        # Use cache if available and valid
        if self._wrapped_cache is not None:
            return self._wrapped_cache
        
        wrapper = WordWrapper(self.width - 2)
        wrapped = []
        
        for msg in self._get_visible_messages():
            lines = wrapper.wrap(msg.format())
            for line in lines:
                wrapped.append((line, msg.color))
        
        # Cache the result
        self._wrapped_cache = wrapped
        return wrapped
    
    def _max_scroll_offset(self) -> int:
        """Calculate maximum scroll offset."""
        wrapped_messages = self._get_wrapped_messages()
        total_lines = len(wrapped_messages)
        visible_lines = self.height - 2
        
        return max(0, total_lines - visible_lines)
    
    @EventHandler(EventType.MESSAGE)
    def _handle_message_event(self, event: MessageEvent) -> None:
        """Handle message events from the event bus."""
        # Convert string category to enum
        try:
            category = MessageCategory[event.category.upper()]
        except (KeyError, AttributeError):
            category = MessageCategory.GENERAL
        
        # Convert color tuple to Color object if needed
        color = None
        if event.color:
            if isinstance(event.color, tuple) and len(event.color) == 3:
                color = Color(*event.color)
            elif isinstance(event.color, Color):
                color = event.color
        
        self.add_message(
            text=event.message,
            category=category,
            color=color
        )