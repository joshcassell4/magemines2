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
    
    def format(self) -> str:
        """Format the stat for display."""
        return f"{self.label}: {self.value}"


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
        
    def set_stat(self, key: str, label: str, value: Any, color: Optional[Color] = None) -> None:
        """Set or update a stat."""
        new_stat = HeaderStat(label, value, color)
        old_formatted = self._stats.get(key).format() if key in self._stats else None
        new_formatted = new_stat.format()
        
        # Only mark for redraw if the formatted string changed
        if old_formatted != new_formatted:
            self._stats[key] = new_stat
            self._needs_full_redraw = True
            
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
                        
            # Write stat
            stat_text = stat.format()
            stat_color = stat.color or Color(200, 200, 200)
            for char in stat_text:
                if x_offset < self.width:
                    self.terminal.write_char(
                        Position(self.position.x + x_offset, self.position.y),
                        TerminalChar(char, stat_color, self.bg_color)
                    )
                    x_offset += 1
                    
        self._needs_full_redraw = False