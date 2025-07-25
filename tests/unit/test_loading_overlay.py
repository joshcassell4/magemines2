"""Tests for loading overlay UI components."""

import pytest
import time
from unittest.mock import MagicMock, patch

from magemines.ui.loading_overlay import (
    LoadingOverlay,
    LoadingIndicator,
    LoadingStyle,
    AsyncOperationManager,
)
from magemines.core.terminal import MockTerminal, Position, TerminalChar, Color


class TestLoadingIndicator:
    """Test LoadingIndicator dataclass."""
    
    def test_default_values(self):
        """Test default values for loading indicator."""
        indicator = LoadingIndicator(message="Loading")
        
        assert indicator.message == "Loading"
        assert indicator.style == LoadingStyle.SPINNER
        assert indicator.progress is None
        assert indicator.color == Color.DIVINE_GOLD
        
    def test_custom_values(self):
        """Test custom values for loading indicator."""
        indicator = LoadingIndicator(
            message="Processing",
            style=LoadingStyle.PROGRESS_BAR,
            progress=0.5,
            color=Color.RED
        )
        
        assert indicator.message == "Processing"
        assert indicator.style == LoadingStyle.PROGRESS_BAR
        assert indicator.progress == 0.5
        assert indicator.color == Color.RED


class TestLoadingOverlay:
    """Test LoadingOverlay component."""
    
    @pytest.fixture
    def terminal(self):
        """Create mock terminal."""
        return MockTerminal(80, 24)
        
    @pytest.fixture
    def overlay(self, terminal):
        """Create loading overlay."""
        return LoadingOverlay(terminal)
        
    def test_initial_state(self, overlay):
        """Test initial overlay state."""
        assert not overlay.active
        assert overlay._indicator is None
        assert overlay._frame_index == 0
        
    def test_show_overlay(self, overlay, terminal):
        """Test showing overlay."""
        indicator = LoadingIndicator(message="Loading")
        
        overlay.show(indicator)
        
        assert overlay.active
        assert overlay._indicator == indicator
        assert overlay._start_time > 0
        
        # Check that overlay is drawn
        screen = terminal.get_screen_content()
        assert any("Loading" in line for line in screen)
        
    def test_hide_overlay(self, overlay):
        """Test hiding overlay."""
        indicator = LoadingIndicator(message="Loading")
        overlay.show(indicator)
        
        overlay.hide()
        
        assert not overlay.active
        assert overlay._indicator is None
        
    def test_spinner_animation(self, overlay, terminal):
        """Test spinner animation frames."""
        indicator = LoadingIndicator(message="Loading", style=LoadingStyle.SPINNER)
        overlay.show(indicator)
        
        # Check initial frame
        initial_frame = overlay._frame_index
        
        # Simulate time passing
        with patch('time.time', return_value=overlay._start_time + 0.2):
            overlay.render()
            
        # Frame should have advanced
        assert overlay._frame_index != initial_frame
        
    def test_dots_animation(self, overlay, terminal):
        """Test dots animation."""
        indicator = LoadingIndicator(message="Loading", style=LoadingStyle.DOTS)
        overlay.show(indicator)
        
        # Render multiple frames
        for i in range(len(overlay.DOTS_FRAMES)):
            overlay._frame_index = i
            overlay.render()
            
            screen = terminal.get_screen_content()
            # Check that dots appear
            dots = overlay.DOTS_FRAMES[i]
            assert any(f"Loading{dots}" in ''.join(line) for line in screen)
            
    def test_progress_bar(self, overlay, terminal):
        """Test progress bar rendering."""
        indicator = LoadingIndicator(
            message="Downloading",
            style=LoadingStyle.PROGRESS_BAR,
            progress=0.0
        )
        overlay.show(indicator)
        
        # Test different progress values
        for progress in [0.0, 0.25, 0.5, 0.75, 1.0]:
            overlay.update_progress(progress)
            overlay.render()
            
            screen = terminal.get_screen_content()
            # Check percentage is shown
            percentage = f"{int(progress * 100)}%"
            assert any(percentage in line for line in screen)
            
    def test_update_progress_with_message(self, overlay):
        """Test updating progress with new message."""
        indicator = LoadingIndicator(
            message="Starting",
            style=LoadingStyle.PROGRESS_BAR,
            progress=0.0
        )
        overlay.show(indicator)
        
        overlay.update_progress(0.5, "Halfway there")
        
        assert overlay._indicator.progress == 0.5
        assert overlay._indicator.message == "Halfway there"
        
    def test_progress_clamping(self, overlay):
        """Test progress value clamping."""
        indicator = LoadingIndicator(
            message="Loading",
            style=LoadingStyle.PROGRESS_BAR
        )
        overlay.show(indicator)
        
        # Test values outside 0-1 range
        overlay.update_progress(-0.5)
        assert overlay._indicator.progress == 0.0
        
        overlay.update_progress(1.5)
        assert overlay._indicator.progress == 1.0
        
    def test_overlay_centering(self, overlay, terminal):
        """Test overlay is centered on screen."""
        indicator = LoadingIndicator(message="Centered")
        overlay.show(indicator)
        
        # Calculate expected position
        overlay_width = 40  # Default minimum width
        overlay_x = (terminal.width - overlay_width) // 2
        
        # Check that content appears in expected horizontal range
        screen = terminal.get_screen_content()
        for y, line in enumerate(screen):
            if "Centered" in line:
                x = line.index("Centered")
                assert overlay_x <= x <= overlay_x + overlay_width
                
    def test_no_render_when_inactive(self, overlay, terminal):
        """Test overlay doesn't render when inactive."""
        terminal.clear()
        terminal.operations.clear()
        
        overlay.render()
        
        # Should not have written anything
        assert terminal.count_operations("write_char") == 0


class TestAsyncOperationManager:
    """Test AsyncOperationManager component."""
    
    @pytest.fixture
    def terminal(self):
        """Create mock terminal."""
        return MockTerminal(80, 24)
        
    @pytest.fixture
    def manager(self, terminal):
        """Create async operation manager."""
        return AsyncOperationManager(terminal)
        
    def test_initial_state(self, manager):
        """Test initial manager state."""
        assert not manager.input_locked
        assert len(manager._operation_stack) == 0
        assert not manager.loading_overlay.active
        
    def test_start_operation(self, manager):
        """Test starting an async operation."""
        manager.start_operation("Loading data")
        
        assert manager.input_locked
        assert len(manager._operation_stack) == 1
        assert manager.loading_overlay.active
        
        # Check operation details
        operation = manager._operation_stack[0]
        assert operation.message == "Loading data"
        assert operation.style == LoadingStyle.SPINNER
        
    def test_end_operation(self, manager):
        """Test ending an async operation."""
        manager.start_operation("Loading")
        manager.end_operation()
        
        assert not manager.input_locked
        assert len(manager._operation_stack) == 0
        assert not manager.loading_overlay.active
        
    def test_nested_operations(self, manager):
        """Test nested async operations."""
        # Start first operation
        manager.start_operation("Operation 1")
        assert manager.input_locked
        
        # Start second operation
        manager.start_operation("Operation 2")
        assert manager.input_locked
        assert len(manager._operation_stack) == 2
        
        # Current overlay should show second operation
        assert manager.loading_overlay._indicator.message == "Operation 2"
        
        # End second operation
        manager.end_operation()
        assert manager.input_locked  # Still locked
        assert len(manager._operation_stack) == 1
        
        # Should now show first operation
        assert manager.loading_overlay._indicator.message == "Operation 1"
        
        # End first operation
        manager.end_operation()
        assert not manager.input_locked
        assert len(manager._operation_stack) == 0
        
    def test_update_progress(self, manager):
        """Test updating progress for current operation."""
        manager.start_operation("Processing", LoadingStyle.PROGRESS_BAR)
        
        manager.update_progress(0.5, "Halfway")
        
        assert manager.loading_overlay._indicator.progress == 0.5
        assert manager.loading_overlay._indicator.message == "Halfway"
        
    def test_render_delegation(self, manager):
        """Test render delegates to overlay."""
        manager.loading_overlay.render = MagicMock()
        
        manager.render()
        
        manager.loading_overlay.render.assert_called_once()
        
    def test_custom_style(self, manager):
        """Test starting operation with custom style."""
        manager.start_operation("Thinking", LoadingStyle.DOTS)
        
        operation = manager._operation_stack[0]
        assert operation.style == LoadingStyle.DOTS