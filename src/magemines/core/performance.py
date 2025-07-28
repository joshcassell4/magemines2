"""Performance optimization utilities for terminal rendering."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from .terminal import TerminalInterface, Position, TerminalChar, Color
import time


@dataclass
class DirtyRegion:
    """Represents a rectangular region that needs to be redrawn."""
    x: int
    y: int
    width: int
    height: int
    
    def contains(self, x: int, y: int) -> bool:
        """Check if a position is within this region."""
        return (self.x <= x < self.x + self.width and 
                self.y <= y < self.y + self.height)
    
    def merge(self, other: 'DirtyRegion') -> 'DirtyRegion':
        """Merge two regions into a bounding box."""
        min_x = min(self.x, other.x)
        min_y = min(self.y, other.y)
        max_x = max(self.x + self.width, other.x + other.width)
        max_y = max(self.y + self.height, other.y + other.height)
        
        return DirtyRegion(min_x, min_y, max_x - min_x, max_y - min_y)


class DirtyRegionTracker:
    """Tracks which screen regions need to be redrawn."""
    
    def __init__(self, width: int, height: int):
        """Initialize the dirty region tracker.
        
        Args:
            width: Screen width
            height: Screen height
        """
        self.width = width
        self.height = height
        self.dirty_cells: Set[Tuple[int, int]] = set()
        self.dirty_regions: List[DirtyRegion] = []
        self._merge_threshold = 20  # Merge regions if they have fewer cells between them
        
    def mark_dirty(self, x: int, y: int) -> None:
        """Mark a single cell as dirty."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.dirty_cells.add((x, y))
            
    def mark_region_dirty(self, x: int, y: int, width: int, height: int) -> None:
        """Mark a rectangular region as dirty."""
        # Clip to screen bounds
        x = max(0, x)
        y = max(0, y)
        width = min(width, self.width - x)
        height = min(height, self.height - y)
        
        if width > 0 and height > 0:
            self.dirty_regions.append(DirtyRegion(x, y, width, height))
            
    def get_dirty_regions(self) -> List[DirtyRegion]:
        """Get optimized list of dirty regions."""
        # Convert individual cells to small regions
        cell_regions = [DirtyRegion(x, y, 1, 1) for x, y in self.dirty_cells]
        
        # Combine all regions
        all_regions = self.dirty_regions + cell_regions
        
        if not all_regions:
            return []
            
        # Optimize by merging nearby regions
        optimized = self._optimize_regions(all_regions)
        
        # Clear for next frame
        self.clear()
        
        return optimized
        
    def _optimize_regions(self, regions: List[DirtyRegion]) -> List[DirtyRegion]:
        """Merge nearby regions to reduce rendering calls."""
        if len(regions) <= 1:
            return regions
            
        # Simple optimization: merge overlapping or adjacent regions
        merged = []
        used = set()
        
        for i, region1 in enumerate(regions):
            if i in used:
                continue
                
            current = region1
            
            for j, region2 in enumerate(regions[i+1:], i+1):
                if j in used:
                    continue
                    
                # Check if regions are close enough to merge
                if self._should_merge(current, region2):
                    current = current.merge(region2)
                    used.add(j)
                    
            merged.append(current)
            
        return merged
        
    def _should_merge(self, r1: DirtyRegion, r2: DirtyRegion) -> bool:
        """Check if two regions should be merged."""
        # Check if regions overlap
        if (r1.x < r2.x + r2.width and r1.x + r1.width > r2.x and
            r1.y < r2.y + r2.height and r1.y + r1.height > r2.y):
            return True
            
        # Check if regions are close enough
        gap_x = max(0, max(r1.x, r2.x) - min(r1.x + r1.width, r2.x + r2.width))
        gap_y = max(0, max(r1.y, r2.y) - min(r1.y + r1.height, r2.y + r2.height))
        
        # Merge if the gap is small
        return gap_x <= 2 and gap_y <= 2
        
    def clear(self) -> None:
        """Clear all dirty regions."""
        self.dirty_cells.clear()
        self.dirty_regions.clear()


@dataclass
class BufferedChar:
    """A character with its styling information."""
    char: str
    fg_color: Optional[Color] = None
    bg_color: Optional[Color] = None
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, BufferedChar):
            return False
        return (self.char == other.char and 
                self.fg_color == other.fg_color and 
                self.bg_color == other.bg_color)


class DoubleBuffer:
    """Double buffering system for flicker-free rendering."""
    
    def __init__(self, width: int, height: int):
        """Initialize the double buffer.
        
        Args:
            width: Buffer width
            height: Buffer height
        """
        self.width = width
        self.height = height
        
        # Initialize buffers with empty cells
        empty_cell = BufferedChar(' ')
        self.front_buffer = [[empty_cell for _ in range(width)] for _ in range(height)]
        self.back_buffer = [[empty_cell for _ in range(width)] for _ in range(height)]
        
        self.dirty_tracker = DirtyRegionTracker(width, height)
        
    def write(self, x: int, y: int, char: str, fg_color: Optional[Color] = None, 
              bg_color: Optional[Color] = None) -> None:
        """Write a character to the back buffer."""
        if 0 <= x < self.width and 0 <= y < self.height:
            new_char = BufferedChar(char, fg_color, bg_color)
            if self.back_buffer[y][x] != new_char:
                self.back_buffer[y][x] = new_char
                self.dirty_tracker.mark_dirty(x, y)
                
    def write_region(self, x: int, y: int, width: int, height: int,
                     fill_char: str = ' ', fg_color: Optional[Color] = None,
                     bg_color: Optional[Color] = None) -> None:
        """Fill a rectangular region in the back buffer."""
        for dy in range(height):
            for dx in range(width):
                self.write(x + dx, y + dy, fill_char, fg_color, bg_color)
                
    def get_dirty_regions(self) -> List[DirtyRegion]:
        """Get list of regions that differ between front and back buffers."""
        # Add regions where content changed
        for y in range(self.height):
            for x in range(self.width):
                if self.front_buffer[y][x] != self.back_buffer[y][x]:
                    self.dirty_tracker.mark_dirty(x, y)
                    
        return self.dirty_tracker.get_dirty_regions()
        
    def swap(self) -> None:
        """Swap front and back buffers."""
        self.front_buffer, self.back_buffer = self.back_buffer, self.front_buffer
        
    def clear_back_buffer(self) -> None:
        """Clear the back buffer to empty spaces."""
        empty_cell = BufferedChar(' ')
        for y in range(self.height):
            for x in range(self.width):
                self.back_buffer[y][x] = empty_cell


class ColorCache:
    """Cache for color escape sequences to avoid repeated conversions."""
    
    def __init__(self, terminal: TerminalInterface):
        """Initialize the color cache.
        
        Args:
            terminal: Terminal interface for generating escape sequences
        """
        self.terminal = terminal
        self.cache: Dict[Tuple[Optional[Tuple[int, int, int]], Optional[Tuple[int, int, int]]], str] = {}
        self.max_cache_size = 1000  # Prevent unbounded growth
        
    def get_color_sequence(self, fg_rgb: Optional[Tuple[int, int, int]] = None,
                          bg_rgb: Optional[Tuple[int, int, int]] = None) -> str:
        """Get cached color escape sequence."""
        key = (fg_rgb, bg_rgb)
        
        if key not in self.cache:
            # Generate the sequence
            if hasattr(self.terminal._term, 'color_rgb'):
                sequence = ""
                if fg_rgb:
                    sequence += self.terminal._term.color_rgb(*fg_rgb)
                if bg_rgb:
                    sequence += self.terminal._term.on_color_rgb(*bg_rgb)
                self.cache[key] = sequence
            else:
                # Fallback for terminals without RGB support
                self.cache[key] = ""
                
            # Prevent cache from growing too large
            if len(self.cache) > self.max_cache_size:
                # Remove oldest entries (simple FIFO)
                keys_to_remove = list(self.cache.keys())[:100]
                for k in keys_to_remove:
                    del self.cache[k]
                    
        return self.cache[key]
        
    def clear(self) -> None:
        """Clear the color cache."""
        self.cache.clear()


@dataclass
class RenderOperation:
    """A single rendering operation."""
    x: int
    y: int
    char: str
    fg_color: Optional[Color] = None
    bg_color: Optional[Color] = None


class BatchRenderer:
    """Batches rendering operations to minimize terminal I/O."""
    
    def __init__(self, terminal: TerminalInterface):
        """Initialize the batch renderer.
        
        Args:
            terminal: Terminal interface for rendering
        """
        self.terminal = terminal
        self.operations: List[RenderOperation] = []
        self.color_cache = ColorCache(terminal)
        
    def add_char(self, x: int, y: int, char: str, 
                 fg_color: Optional[Color] = None,
                 bg_color: Optional[Color] = None) -> None:
        """Add a character to the batch."""
        self.operations.append(RenderOperation(x, y, char, fg_color, bg_color))
        
    def add_string(self, x: int, y: int, text: str,
                   fg_color: Optional[Color] = None,
                   bg_color: Optional[Color] = None) -> None:
        """Add a string to the batch."""
        for i, char in enumerate(text):
            self.add_char(x + i, y, char, fg_color, bg_color)
            
    def flush(self) -> None:
        """Execute all batched operations efficiently."""
        if not self.operations:
            return
            
        # Sort by position to minimize cursor movement
        self.operations.sort(key=lambda op: (op.y, op.x))
        
        # Group consecutive operations with same styling
        output = []
        term = self.terminal._term
        
        i = 0
        while i < len(self.operations):
            op = self.operations[i]
            
            # Move cursor
            output.append(term.move(op.y, op.x))
            
            # Find consecutive operations with same styling
            j = i
            same_style_ops = []
            
            while j < len(self.operations):
                next_op = self.operations[j]
                
                # Check if this operation is consecutive and has same styling
                if (j == i or 
                    (next_op.y == op.y and 
                     next_op.x == self.operations[j-1].x + 1 and
                     next_op.fg_color == op.fg_color and
                     next_op.bg_color == op.bg_color)):
                    same_style_ops.append(next_op)
                    j += 1
                else:
                    break
                    
            # Apply color if needed
            fg_rgb = op.fg_color.to_rgb() if op.fg_color else None
            bg_rgb = op.bg_color.to_rgb() if op.bg_color else None
            color_seq = self.color_cache.get_color_sequence(fg_rgb, bg_rgb)
            
            if color_seq:
                output.append(color_seq)
                
            # Add all characters
            for style_op in same_style_ops:
                output.append(style_op.char)
                
            # Reset color if it was set
            if color_seq:
                output.append(term.normal)
                
            i = j
            
        # Single write to terminal
        print(''.join(output), end='', flush=True)
        
        # Clear operations
        self.operations.clear()


class PerformanceMonitor:
    """Monitor rendering performance metrics."""
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.frame_times: List[float] = []
        self.render_times: Dict[str, List[float]] = {}
        self.max_samples = 60  # Keep last 60 frames
        
    def measure_frame(self):
        """Context manager to measure frame time."""
        start = time.perf_counter()
        yield
        frame_time = time.perf_counter() - start
        
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_samples:
            self.frame_times.pop(0)
            
    def measure_component(self, component_name: str):
        """Context manager to measure component render time."""
        start = time.perf_counter()
        yield
        render_time = time.perf_counter() - start
        
        if component_name not in self.render_times:
            self.render_times[component_name] = []
            
        self.render_times[component_name].append(render_time)
        if len(self.render_times[component_name]) > self.max_samples:
            self.render_times[component_name].pop(0)
            
    def get_fps(self) -> float:
        """Get average FPS over recent frames."""
        if not self.frame_times:
            return 0.0
            
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
        
    def get_component_time(self, component_name: str) -> float:
        """Get average render time for a component."""
        if component_name not in self.render_times or not self.render_times[component_name]:
            return 0.0
            
        times = self.render_times[component_name]
        return sum(times) / len(times)
        
    def get_report(self) -> str:
        """Get a performance report string."""
        fps = self.get_fps()
        report = f"FPS: {fps:.1f}\n"
        
        for component, times in self.render_times.items():
            if times:
                avg_time = sum(times) / len(times)
                report += f"{component}: {avg_time*1000:.1f}ms\n"
                
        return report