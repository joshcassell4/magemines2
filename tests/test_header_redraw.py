"""Test header bar redrawing when changing levels."""

import sys
sys.path.insert(0, 'src')

from magemines.ui.header_bar import HeaderBar
from magemines.core.terminal import Position, Color

class MockTerminal:
    """Mock terminal for testing."""
    def __init__(self):
        self.buffer = {}  # Position -> char
        self.write_count = 0
        
    def write_char(self, position, char):
        """Track writes to the terminal."""
        self.buffer[(position.x, position.y)] = char
        self.write_count += 1
        
    def clear_buffer(self):
        """Clear the buffer (simulating terminal clear)."""
        self.buffer.clear()
        self.write_count = 0
        
    def get_line(self, y):
        """Get the text on a specific line."""
        chars = []
        for x in range(80):  # Assume 80 char width
            if (x, y) in self.buffer:
                chars.append(self.buffer[(x, y)].char)
            else:
                chars.append(' ')
        return ''.join(chars).rstrip()


def test_header_redraw():
    """Test that header bar redraws properly after terminal clear."""
    print("Testing Header Bar Redraw")
    print("=" * 80)
    
    # Create mock terminal and header bar
    terminal = MockTerminal()
    header = HeaderBar(terminal, Position(0, 0), 80)
    
    # Set initial stats
    header.set_stat("turn", "Turn", 1, Color(255, 255, 100))
    header.set_stat("depth", "Depth", 1, Color(100, 200, 255))
    
    # Initial render
    header.render()
    initial_line = terminal.get_line(0)
    print(f"Initial header: '{initial_line}'")
    assert "Turn: 1" in initial_line
    assert "Depth: 1" in initial_line
    
    # Simulate level change - update depth
    header.set_stat("depth", "Depth", 2, Color(100, 200, 255))
    
    # Clear terminal (simulating what happens on level change)
    terminal.clear_buffer()
    print("Terminal cleared")
    
    # Try to render without force flag (old behavior)
    write_count_before = terminal.write_count
    header.render()  # Should not redraw because _needs_full_redraw is False
    write_count_after = terminal.write_count
    
    line_without_force = terminal.get_line(0)
    print(f"After render() without force: '{line_without_force}'")
    print(f"Writes without force: {write_count_after - write_count_before}")
    
    # Clear again and render with force flag (new behavior)
    terminal.clear_buffer()
    write_count_before = terminal.write_count
    header.render(force=True)  # Should redraw everything
    write_count_after = terminal.write_count
    
    line_with_force = terminal.get_line(0)
    print(f"After render(force=True): '{line_with_force}'")
    print(f"Writes with force: {write_count_after - write_count_before}")
    
    # Verify the header was properly redrawn
    assert "Turn: 1" in line_with_force
    assert "Depth: 2" in line_with_force
    assert write_count_after - write_count_before > 0  # Should have written something
    
    print("\nTest passed! Header bar properly redraws with force=True")


def test_partial_update():
    """Test that partial updates still work efficiently."""
    print("\n\nTesting Partial Updates")
    print("=" * 80)
    
    # Create mock terminal and header bar
    terminal = MockTerminal()
    header = HeaderBar(terminal, Position(0, 0), 80)
    
    # Set initial stats
    header.set_stat("turn", "Turn", 1, Color(255, 255, 100))
    header.set_stat("depth", "Depth", 1, Color(100, 200, 255))
    
    # Initial render
    header.render()
    initial_writes = terminal.write_count
    print(f"Initial render: {initial_writes} writes")
    
    # Update only the turn value
    write_count_before = terminal.write_count
    header.set_stat("turn", "Turn", 2, Color(255, 255, 100))
    header.render()  # Should only update the turn value
    write_count_after = terminal.write_count
    
    partial_writes = write_count_after - write_count_before
    print(f"Partial update: {partial_writes} writes")
    
    # Verify partial update is more efficient than full redraw
    assert partial_writes < initial_writes / 2  # Should be much fewer writes
    
    # Verify the update worked
    line = terminal.get_line(0)
    assert "Turn: 2" in line
    assert "Depth: 1" in line
    
    print("Test passed! Partial updates are still efficient")


if __name__ == "__main__":
    test_header_redraw()
    test_partial_update()