"""Terminal abstraction layer for testable rendering."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any
import sys

try:
    from blessed import Terminal
except ImportError:
    Terminal = None  # For testing without blessed


@dataclass(frozen=True)
class Color:
    """RGB color representation."""
    
    r: int
    g: int
    b: int
    
    def __post_init__(self) -> None:
        """Validate RGB values are in valid range."""
        for value, name in [(self.r, 'r'), (self.g, 'g'), (self.b, 'b')]:
            if not 0 <= value <= 255:
                raise ValueError(f"Color {name} must be 0-255, got {value}")
                
    def to_hex(self) -> str:
        """Convert to hex color string."""
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"
    
    def to_rgb(self) -> tuple[int, int, int]:
        """Convert to RGB tuple."""
        return (self.r, self.g, self.b)
        
    def __eq__(self, other: object) -> bool:
        """Compare colors for equality."""
        if not isinstance(other, Color):
            return False
        return self.r == other.r and self.g == other.g and self.b == other.b


# Predefined colors
Color.WHITE = Color(255, 255, 255)
Color.BLACK = Color(0, 0, 0)
Color.RED = Color(255, 0, 0)
Color.GREEN = Color(0, 255, 0)
Color.BLUE = Color(0, 0, 255)
Color.MAGE_BLUE = Color(100, 150, 255)
Color.DIVINE_GOLD = Color(255, 215, 0)


@dataclass(frozen=True)
class Position:
    """2D position in terminal coordinates."""
    
    x: int
    y: int
    
    def __add__(self, other: 'Position') -> 'Position':
        """Add two positions together."""
        return Position(self.x + other.x, self.y + other.y)
        
    def in_bounds(self, width: int, height: int) -> bool:
        """Check if position is within bounds."""
        return 0 <= self.x < width and 0 <= self.y < height
        
    def __hash__(self) -> int:
        """Make Position hashable for use in sets/dicts."""
        return hash((self.x, self.y))


@dataclass
class TerminalChar:
    """A character with color information."""
    
    char: str
    fg: Color = None
    bg: Color = None
    
    def __post_init__(self) -> None:
        """Set default colors if not provided."""
        if self.fg is None:
            self.fg = Color.WHITE
        if self.bg is None:
            self.bg = Color.BLACK


class TerminalInterface(ABC):
    """Abstract interface for terminal operations."""
    
    @property
    @abstractmethod
    def width(self) -> int:
        """Get terminal width."""
        pass
        
    @property
    @abstractmethod
    def height(self) -> int:
        """Get terminal height."""
        pass
        
    @abstractmethod
    def clear(self) -> None:
        """Clear the terminal screen."""
        pass
        
    @abstractmethod
    def move_cursor(self, pos: Position) -> None:
        """Move cursor to position."""
        pass
        
    @abstractmethod
    def write_char(self, pos: Position, char: TerminalChar) -> None:
        """Write a character at position with color."""
        pass
        
    @abstractmethod
    def write_text(self, pos: Position, text: str, 
                   fg: Optional[Color] = None, bg: Optional[Color] = None) -> None:
        """Write text at position with optional color."""
        pass
        
    @abstractmethod
    def get_key(self) -> Optional[str]:
        """Get a key press from the user."""
        pass
        
    @abstractmethod
    def setup(self) -> None:
        """Set up terminal for game use."""
        pass
        
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up terminal state."""
        pass


class MockTerminal(TerminalInterface):
    """Mock terminal implementation for testing."""
    
    def __init__(self, width: int = 80, height: int = 24):
        """Initialize mock terminal."""
        self._width = width
        self._height = height
        self.buffer: dict[tuple[int, int], TerminalChar] = {}
        self.cursor_pos = Position(0, 0)
        self.operations: list[dict[str, Any]] = []
        self.input_queue: list[str] = []
        self._dirty_positions: set[Position] = set()
        
    @property
    def width(self) -> int:
        """Get terminal width."""
        return self._width
        
    @property
    def height(self) -> int:
        """Get terminal height."""
        return self._height
        
    def clear(self) -> None:
        """Clear the terminal screen."""
        self.buffer.clear()
        self.operations.append({"type": "clear"})
        
    def move_cursor(self, pos: Position) -> None:
        """Move cursor to position."""
        self.cursor_pos = pos
        self.operations.append({"type": "move_cursor", "pos": pos})
        
    def write_char(self, pos: Position, char: TerminalChar) -> None:
        """Write a character at position with color."""
        self.buffer[(pos.x, pos.y)] = char
        self._dirty_positions.add(pos)
        self.operations.append({
            "type": "write_char",
            "pos": pos,
            "char": char
        })
        
    def write_text(self, pos: Position, text: str,
                   fg: Optional[Color] = None, bg: Optional[Color] = None) -> None:
        """Write text at position with optional color."""
        x, y = pos.x, pos.y
        for char in text:
            char_obj = TerminalChar(char, fg or Color.WHITE, bg or Color.BLACK)
            self.write_char(Position(x, y), char_obj)
            x += 1
            if x >= self.width:
                x = 0
                y += 1
                
    def get_key(self) -> Optional[str]:
        """Get a key press from the user."""
        if self.input_queue:
            return self.input_queue.pop(0)
        return None
        
    def setup(self) -> None:
        """Set up terminal for game use."""
        self.operations.append({"type": "setup"})
        
    def cleanup(self) -> None:
        """Clean up terminal state."""
        self.operations.append({"type": "cleanup"})
        
    # Additional methods for testing
    def get_char_at(self, pos: Position) -> Optional[TerminalChar]:
        """Get character at position."""
        return self.buffer.get((pos.x, pos.y))
        
    def get_screen_content(self) -> list[str]:
        """Get screen content as list of strings."""
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                char = self.buffer.get((x, y))
                if char:
                    line += char.char
                else:
                    line += " "
            lines.append(line.rstrip())
        return lines
        
    def add_key(self, key: str) -> None:
        """Add a key to the input queue."""
        self.input_queue.append(key)
        
    def count_operations(self, op_type: str) -> int:
        """Count operations of specific type."""
        return sum(1 for op in self.operations if op["type"] == op_type)
        
    def clear_dirty(self) -> None:
        """Clear dirty position tracking."""
        self._dirty_positions.clear()
        
    def get_dirty_positions(self) -> set[Position]:
        """Get positions that have been modified."""
        return self._dirty_positions.copy()


class BlessedTerminal(TerminalInterface):
    """Real terminal implementation using blessed."""
    
    def __init__(self):
        """Initialize blessed terminal."""
        if Terminal is None:
            raise ImportError("blessed library is required for BlessedTerminal")
        self._term = Terminal()
        self._contexts = []
        
    @property
    def width(self) -> int:
        """Get terminal width."""
        return self._term.width
        
    @property
    def height(self) -> int:
        """Get terminal height."""
        return self._term.height
        
    def clear(self) -> None:
        """Clear the terminal screen."""
        print(self._term.clear, end='', flush=True)
        
    def move_cursor(self, pos: Position) -> None:
        """Move cursor to position."""
        # Blessed uses y, x order
        print(self._term.move(pos.y, pos.x), end='', flush=True)
        
    def write_char(self, pos: Position, char: TerminalChar) -> None:
        """Write a character at position with color."""
        # Move to position
        output = self._term.move(pos.y, pos.x)
        
        # Apply colors
        try:
            num_colors = getattr(self._term, 'number_of_colors', 0)
            if num_colors >= 256:
                output += self._term.color_rgb(char.fg.r, char.fg.g, char.fg.b)
                output += self._term.on_color_rgb(char.bg.r, char.bg.g, char.bg.b)
        except (AttributeError, TypeError):
            # Handle mocked terminals that don't have color support
            pass
        
        # Write character
        output += char.char
        
        # Reset to normal
        output += str(self._term.normal)
        
        print(output, end='', flush=True)
        
    def write_text(self, pos: Position, text: str,
                   fg: Optional[Color] = None, bg: Optional[Color] = None) -> None:
        """Write text at position with optional color."""
        # For efficiency, write the whole text at once
        output = self._term.move(pos.y, pos.x)
        
        try:
            num_colors = getattr(self._term, 'number_of_colors', 0)
            if fg and bg and num_colors >= 256:
                output += self._term.color_rgb(fg.r, fg.g, fg.b)
                output += self._term.on_color_rgb(bg.r, bg.g, bg.b)
        except (AttributeError, TypeError):
            # Handle mocked terminals
            pass
            
        output += text
        output += str(self._term.normal)
        
        print(output, end='', flush=True)
        
    def get_key(self) -> Optional[str]:
        """Get a key press from the user."""
        key = self._term.inkey(timeout=0)
        if key:
            return str(key)
        return None
        
    def setup(self) -> None:
        """Set up terminal for game use."""
        # Store contexts for cleanup
        self._contexts = [
            self._term.fullscreen(),
            self._term.cbreak(),
            self._term.hidden_cursor()
        ]
        # Enter all contexts
        for ctx in self._contexts:
            if hasattr(ctx, '__enter__'):
                ctx.__enter__()
            else:
                # Handle mocked context managers
                if hasattr(ctx, '__call__'):
                    ctx()
            
    def cleanup(self) -> None:
        """Clean up terminal state."""
        # Exit all contexts in reverse order
        for ctx in reversed(self._contexts):
            if hasattr(ctx, '__exit__'):
                ctx.__exit__(None, None, None)
        self._contexts = []