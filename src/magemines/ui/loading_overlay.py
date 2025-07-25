"""Loading overlay and progress indicator UI components."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List, Tuple
import time

from ..core.terminal import (
    Color,
    Position,
    TerminalChar,
    TerminalInterface,
)


class LoadingStyle(Enum):
    """Different loading indicator styles."""
    SPINNER = auto()
    DOTS = auto()
    PROGRESS_BAR = auto()


@dataclass
class LoadingIndicator:
    """Configuration for a loading indicator."""
    message: str
    style: LoadingStyle = LoadingStyle.SPINNER
    progress: Optional[float] = None  # 0.0 to 1.0 for progress bars
    color: Color = Color.DIVINE_GOLD
    

class LoadingOverlay:
    """Loading overlay that blocks input and shows progress."""
    
    # Spinner animation frames
    SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    DOTS_FRAMES = ['.', '..', '...', '....']
    
    def __init__(self, terminal: TerminalInterface):
        """Initialize loading overlay."""
        self.terminal = terminal
        self._active = False
        self._start_time = 0.0
        self._frame_index = 0
        self._last_frame_time = 0.0
        self._indicator: Optional[LoadingIndicator] = None
        self._saved_screen: List[List[Optional[TerminalChar]]] = []
        self._overlay_drawn = False
        self._last_animation_pos: Optional[Tuple[int, int]] = None
        self._last_progress: Optional[float] = None
        
    @property
    def active(self) -> bool:
        """Check if overlay is active."""
        return self._active
        
    def show(self, indicator: LoadingIndicator) -> None:
        """Show loading overlay with given indicator."""
        # Update the indicator (allow changing while active)
        self._indicator = indicator
        
        if not self._active:
            # First time showing
            self._active = True
            self._start_time = time.time()
            self._frame_index = 0
            self._last_frame_time = self._start_time
            self._overlay_drawn = False
            self._last_animation_pos = None
            self._last_progress = None
            
            # Save current screen content in area where overlay will be drawn
            self._save_screen_area()
        
        # Force full redraw on show
        self._overlay_drawn = False
        self.render()
        
    def hide(self) -> None:
        """Hide loading overlay and restore screen."""
        if not self._active:
            return
            
        self._active = False
        self._indicator = None
        self._overlay_drawn = False
        self._last_animation_pos = None
        self._last_progress = None
        
        # Restore saved screen content
        self._restore_screen_area()
        
    def update_progress(self, progress: float, message: Optional[str] = None) -> None:
        """Update progress for progress bar style indicators."""
        if not self._active or not self._indicator:
            return
            
        self._indicator.progress = max(0.0, min(1.0, progress))
        if message:
            self._indicator.message = message
            
        self.render()
        
    def render(self) -> None:
        """Render the loading overlay."""
        if not self._active or not self._indicator:
            return
            
        # Update animation frame based on time
        current_time = time.time()
        frame_changed = False
        if current_time - self._last_frame_time > 0.1:  # 10 FPS animation
            old_frame = self._frame_index
            self._frame_index = (self._frame_index + 1) % self._get_frame_count()
            self._last_frame_time = current_time
            frame_changed = old_frame != self._frame_index
            
        # Calculate overlay dimensions and position
        overlay_width = max(40, len(self._indicator.message) + 10)
        overlay_height = 7
        overlay_x = (self.terminal.width - overlay_width) // 2
        overlay_y = (self.terminal.height - overlay_height) // 2
        
        # Draw overlay background with border only if not drawn yet
        if not self._overlay_drawn:
            self._draw_overlay_box(overlay_x, overlay_y, overlay_width, overlay_height)
            self._overlay_drawn = True
            # Force redraw of content on first draw
            frame_changed = True
        
        # Only redraw content if frame changed or progress changed
        if frame_changed or (self._indicator.style == LoadingStyle.PROGRESS_BAR and 
                           self._indicator.progress != self._last_progress):
            # Draw loading indicator based on style
            if self._indicator.style == LoadingStyle.SPINNER:
                self._draw_spinner(overlay_x, overlay_y, overlay_width, frame_changed)
            elif self._indicator.style == LoadingStyle.DOTS:
                self._draw_dots(overlay_x, overlay_y, overlay_width, frame_changed)
            elif self._indicator.style == LoadingStyle.PROGRESS_BAR:
                self._draw_progress_bar(overlay_x, overlay_y, overlay_width)
            
    def _save_screen_area(self) -> None:
        """Save screen content that will be covered by overlay."""
        # Calculate overlay dimensions
        overlay_width = max(40, len(self._indicator.message) + 10) if self._indicator else 50
        overlay_height = 7
        overlay_x = (self.terminal.width - overlay_width) // 2
        overlay_y = (self.terminal.height - overlay_height) // 2
        
        # Store overlay dimensions for restoration
        self._saved_overlay_dims = (overlay_x, overlay_y, overlay_width, overlay_height)
        
        # For now, we'll mark that we need to redraw everything when hiding
        # In a real implementation with terminal buffer access, we'd save the actual characters
        self._saved_screen = True
            
    def _restore_screen_area(self) -> None:
        """Restore saved screen content."""
        if hasattr(self, '_saved_overlay_dims'):
            overlay_x, overlay_y, overlay_width, overlay_height = self._saved_overlay_dims
            
            # Clear the overlay area - this will force the game to redraw
            for y in range(overlay_y, min(overlay_y + overlay_height, self.terminal.height)):
                for x in range(overlay_x, min(overlay_x + overlay_width, self.terminal.width)):
                    self.terminal.write_char(Position(x, y), TerminalChar(' '))
                
    def _draw_overlay_box(self, x: int, y: int, width: int, height: int) -> None:
        """Draw overlay box with border."""
        # Draw background (dark gray)
        bg_color = Color(40, 40, 40)
        border_color = self._indicator.color if self._indicator else Color.WHITE
        
        for dy in range(height):
            for dx in range(width):
                pos = Position(x + dx, y + dy)
                if pos.in_bounds(self.terminal.width, self.terminal.height):
                    # Draw border or background
                    if dy == 0 or dy == height - 1 or dx == 0 or dx == width - 1:
                        # Border
                        if (dy == 0 or dy == height - 1) and (dx == 0 or dx == width - 1):
                            # Corners
                            char = '+'
                        elif dy == 0 or dy == height - 1:
                            # Horizontal borders
                            char = '-'
                        else:
                            # Vertical borders
                            char = '|'
                        self.terminal.write_char(pos, TerminalChar(char, border_color, bg_color))
                    else:
                        # Background
                        self.terminal.write_char(pos, TerminalChar(' ', Color.WHITE, bg_color))
                        
    def _draw_spinner(self, x: int, y: int, width: int, only_animation: bool = False) -> None:
        """Draw spinner-style loading indicator."""
        if not self._indicator:
            return
            
        # Draw spinner frame
        spinner_char = self.SPINNER_FRAMES[self._frame_index]
        message = f"{spinner_char} {self._indicator.message}"
        
        # Center the message
        message_x = x + (width - len(message)) // 2
        message_y = y + 3
        
        if only_animation and self._last_animation_pos:
            # Only redraw the spinner character
            pos = Position(message_x, message_y)
            if pos.in_bounds(self.terminal.width, self.terminal.height):
                self.terminal.write_char(pos, TerminalChar(spinner_char, self._indicator.color, Color(40, 40, 40)))
        else:
            # Draw full message
            for i, char in enumerate(message):
                pos = Position(message_x + i, message_y)
                if pos.in_bounds(self.terminal.width, self.terminal.height):
                    fg_color = self._indicator.color if i == 0 else Color.WHITE
                    self.terminal.write_char(pos, TerminalChar(char, fg_color, Color(40, 40, 40)))
            
        self._last_animation_pos = (message_x, message_y)
                
    def _draw_dots(self, x: int, y: int, width: int, only_animation: bool = False) -> None:
        """Draw dots-style loading indicator."""
        if not self._indicator:
            return
            
        # Draw message with animated dots
        dots = self.DOTS_FRAMES[self._frame_index]
        base_message = self._indicator.message
        
        # Center the message
        message_x = x + (width - len(base_message) - 4) // 2  # Reserve space for max dots
        message_y = y + 3
        
        if only_animation and self._last_animation_pos:
            # Clear old dots and draw new ones
            dots_x = message_x + len(base_message)
            # Clear the dots area (max 4 characters)
            for i in range(4):
                pos = Position(dots_x + i, message_y)
                if pos.in_bounds(self.terminal.width, self.terminal.height):
                    self.terminal.write_char(pos, TerminalChar(' ', Color.WHITE, Color(40, 40, 40)))
            # Draw new dots
            for i, char in enumerate(dots):
                pos = Position(dots_x + i, message_y)
                if pos.in_bounds(self.terminal.width, self.terminal.height):
                    self.terminal.write_char(pos, TerminalChar(char, Color.WHITE, Color(40, 40, 40)))
        else:
            # Draw full message
            # First draw base message
            for i, char in enumerate(base_message):
                pos = Position(message_x + i, message_y)
                if pos.in_bounds(self.terminal.width, self.terminal.height):
                    self.terminal.write_char(pos, TerminalChar(char, Color.WHITE, Color(40, 40, 40)))
            # Then draw dots
            dots_x = message_x + len(base_message)
            for i in range(4):  # Clear space for dots
                pos = Position(dots_x + i, message_y)
                if pos.in_bounds(self.terminal.width, self.terminal.height):
                    if i < len(dots):
                        self.terminal.write_char(pos, TerminalChar(dots[i], Color.WHITE, Color(40, 40, 40)))
                    else:
                        self.terminal.write_char(pos, TerminalChar(' ', Color.WHITE, Color(40, 40, 40)))
                        
        self._last_animation_pos = (message_x, message_y)
                
    def _draw_progress_bar(self, x: int, y: int, width: int) -> None:
        """Draw progress bar style loading indicator."""
        if not self._indicator:
            return
            
        progress = self._indicator.progress or 0.0
        
        # Only draw message on first render
        if self._last_progress is None:
            # Draw message
            message_x = x + (width - len(self._indicator.message)) // 2
            message_y = y + 2
            
            for i, char in enumerate(self._indicator.message):
                pos = Position(message_x + i, message_y)
                if pos.in_bounds(self.terminal.width, self.terminal.height):
                    self.terminal.write_char(pos, TerminalChar(char, Color.WHITE, Color(40, 40, 40)))
                    
            # Draw bar brackets
            bar_width = width - 4
            bar_x = x + 2
            bar_y = y + 4
            self.terminal.write_char(Position(bar_x - 1, bar_y), TerminalChar('[', Color.WHITE, Color(40, 40, 40)))
            self.terminal.write_char(Position(bar_x + bar_width, bar_y), TerminalChar(']', Color.WHITE, Color(40, 40, 40)))
        
        # Always update progress bar and percentage
        bar_width = width - 4
        bar_x = x + 2
        bar_y = y + 4
        
        # Calculate filled portion
        filled_width = int(bar_width * progress)
        
        # Only redraw bar if progress changed
        if progress != self._last_progress:
            # Draw bar fill
            for i in range(bar_width):
                pos = Position(bar_x + i, bar_y)
                if pos.in_bounds(self.terminal.width, self.terminal.height):
                    if i < filled_width:
                        # Filled portion
                        self.terminal.write_char(pos, TerminalChar('=', self._indicator.color, Color(40, 40, 40)))
                    else:
                        # Empty portion
                        self.terminal.write_char(pos, TerminalChar('-', Color(80, 80, 80), Color(40, 40, 40)))
                        
            # Clear old percentage (max 4 chars "100%")
            percent_y = bar_y + 1
            if self._last_progress is not None:
                old_percentage = f"{int(self._last_progress * 100)}%"
                old_percent_x = x + (width - len(old_percentage)) // 2
                for i in range(4):  # Clear max 4 chars
                    pos = Position(old_percent_x + i, percent_y)
                    if pos.in_bounds(self.terminal.width, self.terminal.height):
                        self.terminal.write_char(pos, TerminalChar(' ', Color.WHITE, Color(40, 40, 40)))
                        
            # Draw new percentage
            percentage = f"{int(progress * 100)}%"
            percent_x = x + (width - len(percentage)) // 2
            
            for i, char in enumerate(percentage):
                pos = Position(percent_x + i, percent_y)
                if pos.in_bounds(self.terminal.width, self.terminal.height):
                    self.terminal.write_char(pos, TerminalChar(char, self._indicator.color, Color(40, 40, 40)))
                    
        self._last_progress = progress
                
    def _get_frame_count(self) -> int:
        """Get number of animation frames for current style."""
        if not self._indicator:
            return 1
            
        if self._indicator.style == LoadingStyle.SPINNER:
            return len(self.SPINNER_FRAMES)
        elif self._indicator.style == LoadingStyle.DOTS:
            return len(self.DOTS_FRAMES)
        else:
            return 1  # Progress bar doesn't animate


class AsyncOperationManager:
    """Manages async operations with loading indicators and input locking."""
    
    def __init__(self, terminal: TerminalInterface):
        """Initialize async operation manager."""
        self.terminal = terminal
        self.loading_overlay = LoadingOverlay(terminal)
        self._input_locked = False
        self._operation_stack: List[LoadingIndicator] = []
        
    @property
    def input_locked(self) -> bool:
        """Check if input is currently locked."""
        return self._input_locked
        
    def start_operation(self, message: str, style: LoadingStyle = LoadingStyle.SPINNER) -> None:
        """Start an async operation with loading indicator."""
        indicator = LoadingIndicator(message=message, style=style)
        self._operation_stack.append(indicator)
        self._input_locked = True
        # Always show the most recent operation (top of stack)
        self.loading_overlay.show(self._operation_stack[-1])
        
    def update_progress(self, progress: float, message: Optional[str] = None) -> None:
        """Update progress for current operation."""
        if self._operation_stack:
            self.loading_overlay.update_progress(progress, message)
            
    def end_operation(self) -> None:
        """End the current async operation."""
        if self._operation_stack:
            self._operation_stack.pop()
            
        if not self._operation_stack:
            # No more operations, hide overlay and unlock input
            self.loading_overlay.hide()
            self._input_locked = False
        else:
            # Show previous operation
            self.loading_overlay.show(self._operation_stack[-1])
            
    def render(self) -> None:
        """Render the loading overlay if active."""
        self.loading_overlay.render()