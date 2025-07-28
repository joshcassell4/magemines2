"""Message log viewer overlay for viewing full message history."""

from typing import List, Optional
from ..core.terminal import TerminalInterface, Position, Color, TerminalChar
from .message_pane import Message, MessageCategory, MessagePane


class MessageLogViewer:
    """Overlay for viewing full message history with scrolling."""
    
    def __init__(self, terminal: TerminalInterface):
        """Initialize the message log viewer.
        
        Args:
            terminal: Terminal interface for rendering
        """
        self.terminal = terminal
        self.visible = False
        self.scroll_offset = 0
        self.selected_line = 0
        self._messages: List[Message] = []
        
        # Calculate overlay dimensions (80% of screen)
        self.width = int(terminal.width * 0.8)
        self.height = int(terminal.height * 0.8)
        self.x = (terminal.width - self.width) // 2
        self.y = (terminal.height - self.height) // 2
        
    def set_messages(self, messages: List[Message]) -> None:
        """Set the messages to display.
        
        Args:
            messages: List of messages from the message pane
        """
        self._messages = messages
        self.scroll_offset = 0
        self.selected_line = 0
        
    def toggle(self) -> None:
        """Toggle the visibility of the log viewer."""
        self.visible = not self.visible
        if self.visible:
            self.scroll_offset = 0
            
    def show(self) -> None:
        """Show the log viewer."""
        self.visible = True
        self.scroll_offset = 0
        
    def hide(self) -> None:
        """Hide the log viewer."""
        self.visible = False
        
    def scroll_up(self, lines: int = 1) -> None:
        """Scroll up in the message log."""
        self.scroll_offset = max(0, self.scroll_offset - lines)
        
    def scroll_down(self, lines: int = 1) -> None:
        """Scroll down in the message log."""
        max_offset = max(0, len(self._get_wrapped_lines()) - (self.height - 4))
        self.scroll_offset = min(max_offset, self.scroll_offset + lines)
        
    def page_up(self) -> None:
        """Scroll up by one page."""
        self.scroll_up(self.height - 4)
        
    def page_down(self) -> None:
        """Scroll down by one page."""
        self.scroll_down(self.height - 4)
        
    def handle_key(self, key: str) -> bool:
        """Handle keyboard input for the log viewer.
        
        Args:
            key: The key pressed
            
        Returns:
            True if the key was handled, False otherwise
        """
        if not self.visible:
            return False
            
        # Close on ESC
        if key == 'KEY_ESCAPE' or key == '\x1b':
            self.hide()
            return True
            
        # Scroll controls
        elif key == 'KEY_UP' or key == 'k':
            self.scroll_up()
            return True
        elif key == 'KEY_DOWN' or key == 'j':
            self.scroll_down()
            return True
        elif key == 'KEY_PGUP':
            self.page_up()
            return True
        elif key == 'KEY_PGDOWN':
            self.page_down()
            return True
        elif key == 'KEY_HOME':
            self.scroll_offset = 0
            return True
        elif key == 'KEY_END':
            max_offset = max(0, len(self._get_wrapped_lines()) - (self.height - 4))
            self.scroll_offset = max_offset
            return True
            
        return False
        
    def render(self) -> None:
        """Render the message log viewer."""
        if not self.visible:
            return
            
        # Draw background (clear the area)
        bg_color = Color(20, 20, 20)  # Dark gray background
        for y in range(self.height):
            for x in range(self.width):
                self.terminal.write_char(
                    Position(self.x + x, self.y + y),
                    TerminalChar(' ', bg_color=bg_color)
                )
                
        # Draw border
        self._draw_border()
        
        # Draw title
        title = " Message Log (ESC to close, arrows to scroll) "
        title_x = self.x + (self.width - len(title)) // 2
        for i, char in enumerate(title):
            self.terminal.write_char(
                Position(title_x + i, self.y),
                TerminalChar(char, Color(255, 255, 100))  # Bright yellow
            )
            
        # Draw messages
        wrapped_lines = self._get_wrapped_lines()
        visible_height = self.height - 4  # Minus borders and title
        
        # Calculate visible range
        start_idx = self.scroll_offset
        end_idx = min(len(wrapped_lines), start_idx + visible_height)
        
        # Draw visible lines
        for i, (line_text, color, turn, category) in enumerate(wrapped_lines[start_idx:end_idx]):
            y_pos = self.y + 2 + i  # Start after top border and spacing
            
            # Draw turn number if not a system message
            x_pos = self.x + 2
            if category != MessageCategory.SYSTEM:
                turn_str = f"[T{turn:3d}] "
                for char in turn_str:
                    self.terminal.write_char(
                        Position(x_pos, y_pos),
                        TerminalChar(char, Color(128, 128, 128))  # Gray
                    )
                    x_pos += 1
                    
            # Draw message text
            for char in line_text:
                if x_pos < self.x + self.width - 2:  # Don't overflow border
                    self.terminal.write_char(
                        Position(x_pos, y_pos),
                        TerminalChar(char, color)
                    )
                    x_pos += 1
                    
        # Draw scroll indicators
        self._draw_scroll_indicators(len(wrapped_lines), visible_height)
        
    def _draw_border(self) -> None:
        """Draw the border around the log viewer."""
        border_color = Color(100, 100, 100)  # Gray border
        
        # Corners
        self.terminal.write_char(
            Position(self.x, self.y),
            TerminalChar('+', border_color)
        )
        self.terminal.write_char(
            Position(self.x + self.width - 1, self.y),
            TerminalChar('+', border_color)
        )
        self.terminal.write_char(
            Position(self.x, self.y + self.height - 1),
            TerminalChar('+', border_color)
        )
        self.terminal.write_char(
            Position(self.x + self.width - 1, self.y + self.height - 1),
            TerminalChar('+', border_color)
        )
        
        # Horizontal lines
        for x in range(self.x + 1, self.x + self.width - 1):
            self.terminal.write_char(
                Position(x, self.y),
                TerminalChar('-', border_color)
            )
            self.terminal.write_char(
                Position(x, self.y + self.height - 1),
                TerminalChar('-', border_color)
            )
            
        # Vertical lines
        for y in range(self.y + 1, self.y + self.height - 1):
            self.terminal.write_char(
                Position(self.x, y),
                TerminalChar('|', border_color)
            )
            self.terminal.write_char(
                Position(self.x + self.width - 1, y),
                TerminalChar('|', border_color)
            )
            
    def _draw_scroll_indicators(self, total_lines: int, visible_height: int) -> None:
        """Draw scroll position indicators."""
        if total_lines <= visible_height:
            return
            
        # Calculate scroll bar position
        bar_height = max(1, int(visible_height * visible_height / total_lines))
        bar_position = int(self.scroll_offset * (visible_height - bar_height) / (total_lines - visible_height))
        
        # Draw scroll track
        for y in range(visible_height):
            self.terminal.write_char(
                Position(self.x + self.width - 2, self.y + 2 + y),
                TerminalChar(':', Color(60, 60, 60))  # Dark gray
            )
            
        # Draw scroll bar
        for y in range(bar_height):
            if bar_position + y < visible_height:
                self.terminal.write_char(
                    Position(self.x + self.width - 2, self.y + 2 + bar_position + y),
                    TerminalChar('#', Color(150, 150, 150))  # Light gray
                )
                
        # Draw arrows if can scroll
        if self.scroll_offset > 0:
            self.terminal.write_char(
                Position(self.x + self.width - 2, self.y + 1),
                TerminalChar('^', Color(200, 200, 200))
            )
            
        if self.scroll_offset < total_lines - visible_height:
            self.terminal.write_char(
                Position(self.x + self.width - 2, self.y + self.height - 2),
                TerminalChar('v', Color(200, 200, 200))
            )
            
    def _get_wrapped_lines(self) -> List[tuple[str, Color, int, MessageCategory]]:
        """Get all messages wrapped to fit the viewer width."""
        wrapped = []
        max_text_width = self.width - 4 - 8  # Minus borders and turn prefix
        
        for msg in self._messages:
            # Wrap long messages
            lines = self._wrap_text(msg.text, max_text_width)
            for line in lines:
                wrapped.append((line, msg.color, msg.turn, msg.category))
                
        return wrapped
        
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max width."""
        if len(text) <= max_width:
            return [text]
            
        lines = []
        current_line = ""
        
        for word in text.split():
            if len(current_line) + len(word) + 1 <= max_width:
                if current_line:
                    current_line += " "
                current_line += word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
                
        if current_line:
            lines.append(current_line)
            
        return lines