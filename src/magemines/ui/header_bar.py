"""Header bar UI component for displaying game stats."""

from dataclasses import dataclass
from typing import Dict, Any, Optional

from ..core.terminal import (
    Color,
    Position,
    TerminalChar,
    TerminalInterface,
)


@dataclass
class HeaderStat:
    """A single stat to display in the header."""
    label: str
    value: Any
    color: Optional[Color] = None
    position: Optional[int] = None  # X position where this stat starts
    
    def format(self) -> str:
        """Format the stat for display."""
        return f"{self.label}: {self.value}"
    
    def format_label(self) -> str:
        """Get just the label part."""
        return f"{self.label}: "
    
    def format_value(self) -> str:
        """Get just the value part."""
        return str(self.value)


class HeaderBar:
    """Header bar for displaying game stats without borders."""
    
    def __init__(
        self,
        terminal: TerminalInterface,
        position: Position,
        width: int,
        bg_color: Optional[Color] = None
    ):
        """Initialize header bar."""
        self.terminal = terminal
        self.position = position
        self.width = width
        self.bg_color = bg_color or Color(30, 30, 30)  # Dark gray background
        self._stats: Dict[str, HeaderStat] = {}
        self._last_rendered: Dict[str, str] = {}
        self._needs_full_redraw = True
        self._stat_positions: Dict[str, tuple[int, int]] = {}  # key -> (start_x, value_start_x)
        
    def set_stat(self, key: str, label: str, value: Any, color: Optional[Color] = None) -> None:
        """Set or update a stat."""
        new_stat = HeaderStat(label, value, color)
        
        # Check if this is a new stat or if the label changed
        if key not in self._stats or self._stats[key].label != label:
            self._stats[key] = new_stat
            self._needs_full_redraw = True
        else:
            # Only the value changed, update it without full redraw
            old_value = self._stats[key].format_value()
            new_value = new_stat.format_value()
            if old_value != new_value:
                self._stats[key] = new_stat
                # Mark for partial redraw
                if key in self._stat_positions and not self._needs_full_redraw:
                    self._redraw_stat_value(key)
            
    def remove_stat(self, key: str) -> None:
        """Remove a stat."""
        if key in self._stats:
            del self._stats[key]
            self._needs_full_redraw = True
            
    def clear_stats(self) -> None:
        """Clear all stats."""
        if self._stats:
            self._stats.clear()
            self._needs_full_redraw = True
            
    def render(self) -> None:
        """Render the header bar."""
        if not self._needs_full_redraw:
            return
            
        # Build the header string
        parts = []
        for key, stat in self._stats.items():
            parts.append(stat.format())
            
        # Join with separator
        header_text = " | ".join(parts)
        
        # Truncate if too long
        if len(header_text) > self.width:
            header_text = header_text[:self.width - 3] + "..."
            
        # Clear the entire header line with background color
        for x in range(self.width):
            self.terminal.write_char(
                Position(self.position.x + x, self.position.y),
                TerminalChar(' ', Color.WHITE, self.bg_color)
            )
            
        # Clear position tracking
        self._stat_positions.clear()
        
        # Write the header text
        x_offset = 0
        for part_idx, (key, stat) in enumerate(self._stats.items()):
            if part_idx > 0:
                # Write separator
                sep = " | "
                for char in sep:
                    if x_offset < self.width:
                        self.terminal.write_char(
                            Position(self.position.x + x_offset, self.position.y),
                            TerminalChar(char, Color(128, 128, 128), self.bg_color)
                        )
                        x_offset += 1
                        
            # Track start position of this stat
            stat_start_x = x_offset
            
            # Write label
            label_text = stat.format_label()
            stat_color = stat.color or Color(200, 200, 200)
            for char in label_text:
                if x_offset < self.width:
                    self.terminal.write_char(
                        Position(self.position.x + x_offset, self.position.y),
                        TerminalChar(char, stat_color, self.bg_color)
                    )
                    x_offset += 1
            
            # Track value start position
            value_start_x = x_offset
            
            # Write value
            value_text = stat.format_value()
            for char in value_text:
                if x_offset < self.width:
                    self.terminal.write_char(
                        Position(self.position.x + x_offset, self.position.y),
                        TerminalChar(char, stat_color, self.bg_color)
                    )
                    x_offset += 1
                    
            # Store positions for this stat
            self._stat_positions[key] = (stat_start_x, value_start_x)
                    
        self._needs_full_redraw = False
    
    def _redraw_stat_value(self, key: str) -> None:
        """Redraw only the value portion of a stat."""
        if key not in self._stats or key not in self._stat_positions:
            return
            
        stat = self._stats[key]
        _, value_start_x = self._stat_positions[key]
        value_text = stat.format_value()
        stat_color = stat.color or Color(200, 200, 200)
        
        # Clear the old value (assume max 10 chars for a number)
        for i in range(10):
            x = value_start_x + i
            if x < self.width:
                self.terminal.write_char(
                    Position(self.position.x + x, self.position.y),
                    TerminalChar(' ', Color.WHITE, self.bg_color)
                )
        
        # Write the new value
        for i, char in enumerate(value_text):
            x = value_start_x + i
            if x < self.width:
                self.terminal.write_char(
                    Position(self.position.x + x, self.position.y),
                    TerminalChar(char, stat_color, self.bg_color)
                )