"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import Mock

import pytest
from blessed import Terminal

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_terminal() -> Mock:
    """Create a mock blessed Terminal for testing."""
    terminal = Mock(spec=Terminal)
    terminal.width = 80
    terminal.height = 24
    terminal.move = Mock(return_value="")
    terminal.clear = Mock(return_value="")
    terminal.normal = Mock(return_value="")
    
    # Color methods
    terminal.color_rgb = Mock(side_effect=lambda r, g, b: f"[RGB:{r},{g},{b}]")
    terminal.on_color_rgb = Mock(side_effect=lambda r, g, b: f"[BG_RGB:{r},{g},{b}]")
    
    # Terminal capabilities
    terminal.number_of_colors = 1 << 24  # 24-bit color support
    
    # Context managers
    terminal.fullscreen = Mock(return_value=terminal)
    terminal.cbreak = Mock(return_value=terminal)
    terminal.hidden_cursor = Mock(return_value=terminal)
    
    # Make context managers work
    terminal.__enter__ = Mock(return_value=terminal)
    terminal.__exit__ = Mock(return_value=None)
    
    return terminal


@pytest.fixture
def game_config() -> dict:
    """Standard game configuration for tests."""
    return {
        "map_width": 80,
        "map_height": 24,
        "seed": 42,  # Deterministic for tests
        "max_entities": 10,
        "turn_time_limit": 0.1,  # 100ms
    }


@pytest.fixture
def test_env(monkeypatch) -> None:
    """Set up test environment variables."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("DEBUG_MODE", "true")
    monkeypatch.setenv("GAME_SEED", "42")
    monkeypatch.setenv("AUTO_ADVANCE_TURNS", "false")


@pytest.fixture
def temp_game_dir(tmp_path) -> Path:
    """Create a temporary directory for game files."""
    game_dir = tmp_path / "test_game"
    game_dir.mkdir()
    (game_dir / "saves").mkdir()
    (game_dir / "logs").mkdir()
    return game_dir


@pytest.fixture(autouse=True)
def reset_singletons() -> Generator[None, None, None]:
    """Reset any singleton instances between tests."""
    # This will be useful when we implement singletons
    yield
    # Clean up after test


class MockTerminalRecorder:
    """Records all terminal operations for verification."""
    
    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.buffer: dict[tuple[int, int], dict] = {}
        self.operations: list[dict] = []
        self.cursor_pos = (0, 0)
        
    def move(self, y: int, x: int) -> str:
        """Record cursor movement."""
        self.cursor_pos = (x, y)
        self.operations.append({"type": "move", "x": x, "y": y})
        return ""
        
    def write(self, text: str, fg=None, bg=None) -> None:
        """Write text at current position."""
        x, y = self.cursor_pos
        for char in text:
            self.buffer[(x, y)] = {"char": char, "fg": fg, "bg": bg}
            self.operations.append({
                "type": "write",
                "x": x,
                "y": y,
                "char": char,
                "fg": fg,
                "bg": bg
            })
            x += 1
            if x >= self.width:
                x = 0
                y += 1
        self.cursor_pos = (x, y)
        
    def clear(self) -> str:
        """Clear the screen."""
        self.buffer.clear()
        self.operations.append({"type": "clear"})
        return ""
        
    def get_screen_content(self) -> list[str]:
        """Get current screen as list of strings."""
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                if (x, y) in self.buffer:
                    line += self.buffer[(x, y)]["char"]
                else:
                    line += " "
            lines.append(line.rstrip())
        return lines
        
    def get_char_at(self, x: int, y: int) -> str | None:
        """Get character at specific position."""
        return self.buffer.get((x, y), {}).get("char")
        
    def count_operations(self, op_type: str) -> int:
        """Count operations of specific type."""
        return sum(1 for op in self.operations if op["type"] == op_type)


@pytest.fixture
def terminal_recorder() -> MockTerminalRecorder:
    """Create a terminal recorder for detailed testing."""
    return MockTerminalRecorder()


# Async fixtures for OpenAI testing
@pytest.fixture
async def mock_openai_client(mocker):
    """Mock OpenAI client for testing."""
    client = mocker.AsyncMock()
    
    # Mock chat completion
    completion_mock = mocker.Mock()
    completion_mock.choices = [
        mocker.Mock(message=mocker.Mock(content="Test AI response"))
    ]
    
    client.chat.completions.create = mocker.AsyncMock(return_value=completion_mock)
    
    return client


# Performance testing helpers
@pytest.fixture
def large_world_config() -> dict:
    """Configuration for performance testing with many entities."""
    return {
        "map_width": 200,
        "map_height": 200,
        "seed": 42,
        "max_entities": 200,
        "turn_time_limit": 0.1,
    }


# Markers for test organization
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that test single components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests that test multiple components"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests that should be run separately"
    )
    config.addinivalue_line(
        "markers", "benchmark: Performance benchmark tests"
    )
    config.addinivalue_line(
        "markers", "requires_terminal: Tests that need actual terminal features"
    )