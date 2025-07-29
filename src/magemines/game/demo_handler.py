"""Demo Handler for loading indicator demonstrations."""

import time
from typing import Optional
from ..ui.loading_overlay import AsyncOperationManager, LoadingStyle
from ..ui.message_pane import MessagePane, MessageCategory


class DemoHandler:
    """Handles loading indicator demonstrations."""
    
    def __init__(self, async_manager: AsyncOperationManager, message_pane: MessagePane):
        """Initialize demo handler.
        
        Args:
            async_manager: Async operation manager for loading overlays
            message_pane: Message pane for displaying demo messages
        """
        self.async_manager = async_manager
        self.message_pane = message_pane
        self.demo_start_time: Optional[float] = None
        self.demo_progress: float = 0.0
        
    def handle_key(self, key: str) -> bool:
        """Handle demo-related key presses.
        
        Args:
            key: The key pressed
            
        Returns:
            True if key was handled, False otherwise
        """
        if self.async_manager.loading_overlay.active:
            if str(key) == 'C':
                # Cancel/complete loading demo
                self.message_pane.add_message("Operation cancelled!", MessageCategory.GENERAL)
                self.async_manager.end_operation()
                self.reset_demo()
                return True
        else:
            # Start new demos
            if str(key) == 'L':
                # Demo loading spinner
                self.start_spinner_demo()
                return True
            elif str(key) == 'P':
                # Demo progress bar
                self.start_progress_demo()
                return True
            elif str(key) == 'D':
                # Demo dots animation
                self.start_dots_demo()
                return True
                
        return False
    
    def start_spinner_demo(self) -> None:
        """Start spinner loading demonstration."""
        self.async_manager.start_operation("Loading magical energies", LoadingStyle.SPINNER)
        self.message_pane.add_message("Channeling divine power...", MessageCategory.DIVINE)
        self.message_pane.render()  # Force message to show immediately
        self.async_manager.render()  # Force overlay to render immediately
        self.demo_start_time = time.time()
        self.demo_progress = 0.0
        
    def start_progress_demo(self) -> None:
        """Start progress bar demonstration."""
        self.async_manager.start_operation("Downloading ancient knowledge", LoadingStyle.PROGRESS_BAR)
        self.message_pane.add_message("Connecting to the astral plane...", MessageCategory.SPELL)
        self.message_pane.render()
        self.async_manager.render()
        self.demo_start_time = time.time()
        self.demo_progress = 0.0
        
    def start_dots_demo(self) -> None:
        """Start dots animation demonstration."""
        self.async_manager.start_operation("Thinking", LoadingStyle.DOTS)
        self.message_pane.add_message("The spirits are contemplating...", MessageCategory.DIALOGUE)
        self.message_pane.render()
        self.async_manager.render()
        self.demo_start_time = time.time()
        self.demo_progress = 0.0
        
    def update(self) -> None:
        """Update demo progress and auto-complete demos after timeout."""
        if not self.async_manager.loading_overlay.active or not self.demo_start_time:
            return
            
        elapsed = time.time() - self.demo_start_time
        
        if self.async_manager.loading_overlay._indicator:
            style = self.async_manager.loading_overlay._indicator.style
            
            if style == LoadingStyle.SPINNER:
                # Spinner demo lasts 3 seconds
                if elapsed > 3.0:
                    self.message_pane.add_message("Divine energy channeled!", MessageCategory.DIVINE)
                    self.async_manager.end_operation()
                    self.reset_demo()
            elif style == LoadingStyle.DOTS:
                # Dots demo lasts 2 seconds
                if elapsed > 2.0:
                    self.message_pane.add_message("The spirits have spoken!", MessageCategory.DIALOGUE)
                    self.async_manager.end_operation()
                    self.reset_demo()
            elif style == LoadingStyle.PROGRESS_BAR:
                # Progress bar advances over 4 seconds
                self.demo_progress = min(1.0, elapsed / 4.0)
                self.async_manager.update_progress(self.demo_progress)
                if self.demo_progress >= 1.0:
                    self.message_pane.add_message("Ancient knowledge downloaded!", MessageCategory.SPELL)
                    self.async_manager.end_operation()
                    self.reset_demo()
                    
    def reset_demo(self) -> None:
        """Reset demo state."""
        self.demo_start_time = None
        self.demo_progress = 0.0
        
    def add_help_messages(self) -> None:
        """Add demo help messages to message pane."""
        self.message_pane.add_message("Demo: L (spinner), P (progress), D (dots), C (cancel)", MessageCategory.SYSTEM, turn=0)