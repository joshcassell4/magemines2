# MageMines Performance Optimization Guide

## Executive Summary

After analyzing the MageMines codebase, I've identified several critical performance issues related to UI rendering and screen redraws. The game currently performs many unnecessary full-screen redraws, inefficient character-by-character rendering, and lacks proper dirty region tracking. This document provides actionable recommendations to improve performance, particularly focusing on minimizing screen flicker and reducing terminal I/O operations.

## Critical Performance Issues

### 1. Excessive Full Screen Redraws

**Problem**: The game performs full screen redraws in multiple scenarios:
- Every time the async manager needs a redraw
- When toggling inventory
- After level changes
- When messages scroll
- During initial render and various UI state changes

**Impact**: Full screen redraws cause visible flicker and poor performance, especially on slower terminals or remote connections.

### 2. Character-by-Character Rendering

**Problem**: Multiple components render one character at a time:
- `ColorPalette.render_colored_char()` - moves cursor and prints for each character
- `GameMap.draw_static()` - renders entire map character by character
- `GameMap.draw_entities()` - renders each entity individually
- Message pane renders text character by character

**Impact**: Each character requires multiple terminal escape sequences (cursor move, color codes, character, reset), resulting in thousands of terminal operations per frame.

### 3. Inefficient Color Management

**Problem**: Color escape sequences are generated repeatedly:
- Colors are converted from RGB to escape sequences on every render
- No caching of frequently used color combinations
- Terminal normal reset after every character

**Impact**: Significant overhead from repeated string operations and terminal commands.

### 4. Lack of Dirty Region Tracking

**Problem**: The game doesn't track which screen regions have changed:
- Player movement redraws the entire player position instead of just the changed cells
- Message pane redraws all visible lines even if only one message was added
- Header bar has some optimization but still redraws entire stats

**Impact**: Unnecessary rendering of unchanged content.

## Recommended Optimizations

### 1. Implement Proper Dirty Region Tracking

**Priority: HIGH**

Create a dirty region system to track changed areas:

```python
class DirtyRegionTracker:
    def __init__(self, width, height):
        self.dirty_cells = set()  # Set of (x, y) tuples
        self.dirty_regions = []   # List of rectangular regions
        
    def mark_dirty(self, x, y):
        self.dirty_cells.add((x, y))
        
    def mark_region_dirty(self, x, y, width, height):
        self.dirty_regions.append((x, y, width, height))
        
    def get_dirty_cells(self):
        # Merge overlapping regions for efficiency
        return self.optimize_regions()
```

### 2. Batch Terminal Operations

**Priority: HIGH**

Instead of printing each character individually, batch operations:

```python
class BatchRenderer:
    def __init__(self, terminal):
        self.terminal = terminal
        self.buffer = []
        
    def add_char(self, x, y, char, fg_color, bg_color):
        self.buffer.append((x, y, char, fg_color, bg_color))
        
    def flush(self):
        # Sort by position to minimize cursor movement
        self.buffer.sort(key=lambda item: (item[1], item[0]))
        
        # Group consecutive characters with same color
        output = []
        for group in self.group_by_color(self.buffer):
            output.extend(self.render_group(group))
            
        # Write everything at once
        print(''.join(output), end='', flush=True)
        self.buffer.clear()
```

### 3. Cache Color Escape Sequences

**Priority: MEDIUM**

Create a color cache to avoid repeated conversions:

```python
class ColorCache:
    def __init__(self, terminal):
        self.terminal = terminal
        self.cache = {}
        
    def get_color_sequence(self, fg_rgb, bg_rgb=None):
        key = (fg_rgb, bg_rgb)
        if key not in self.cache:
            sequence = self.terminal.color_rgb(*fg_rgb)
            if bg_rgb:
                sequence += self.terminal.on_color_rgb(*bg_rgb)
            self.cache[key] = sequence
        return self.cache[key]
```

### 4. Optimize Map Rendering

**Priority: HIGH**

The map should only redraw changed tiles:

```python
class OptimizedGameMap:
    def __init__(self):
        self.last_rendered_tiles = {}  # (x, y) -> (char, color)
        
    def draw_optimized(self, term):
        batch = BatchRenderer(term)
        
        for y in range(self.height):
            for x in range(self.width):
                current = (self.tiles[y][x], self.get_tile_color(x, y))
                last = self.last_rendered_tiles.get((x, y))
                
                if current != last:
                    batch.add_char(x + self.x_offset, y + self.y_offset, 
                                 current[0], current[1])
                    self.last_rendered_tiles[(x, y)] = current
                    
        batch.flush()
```

### 5. Implement Double Buffering

**Priority: MEDIUM**

Use double buffering to eliminate flicker:

```python
class DoubleBufferedRenderer:
    def __init__(self, width, height):
        self.front_buffer = [[None for _ in range(width)] for _ in range(height)]
        self.back_buffer = [[None for _ in range(width)] for _ in range(height)]
        
    def draw_to_back_buffer(self, x, y, char, color):
        self.back_buffer[y][x] = (char, color)
        
    def swap_buffers(self, terminal):
        # Only update changed cells
        for y in range(len(self.front_buffer)):
            for x in range(len(self.front_buffer[0])):
                if self.back_buffer[y][x] != self.front_buffer[y][x]:
                    # Render the change
                    char, color = self.back_buffer[y][x]
                    # ... render to terminal ...
                    
        # Swap references
        self.front_buffer, self.back_buffer = self.back_buffer, self.front_buffer
```

### 6. Optimize Entity Rendering

**Priority: HIGH**

Track entity positions and only redraw when they move:

```python
class EntityRenderer:
    def __init__(self):
        self.last_positions = {}  # entity_id -> (x, y)
        
    def render_entities(self, entities, game_map, term):
        batch = BatchRenderer(term)
        
        for entity in entities:
            entity_id = entity.id
            current_pos = entity.get_component(Position)
            last_pos = self.last_positions.get(entity_id)
            
            # Clear old position if entity moved
            if last_pos and last_pos != current_pos:
                tile = game_map.tiles[last_pos.y][last_pos.x]
                batch.add_char(last_pos.x, last_pos.y, tile, 
                             game_map.get_tile_color(last_pos.x, last_pos.y))
            
            # Draw at new position
            if current_pos:
                batch.add_char(current_pos.x, current_pos.y, 
                             entity.renderable.char, entity.renderable.color)
                self.last_positions[entity_id] = current_pos
                
        batch.flush()
```

### 7. Optimize Message Pane

**Priority: MEDIUM**

Only redraw new messages and scroll changes:

```python
class OptimizedMessagePane:
    def render_incremental(self):
        if not self._needs_redraw:
            return
            
        # Only redraw changed lines
        new_lines = self._get_visible_lines()
        
        for i, (new_line, old_line) in enumerate(zip(new_lines, self._last_lines)):
            if new_line != old_line:
                self._render_line(i, new_line)
                
        self._last_lines = new_lines
        self._needs_redraw = False
```

### 8. Reduce Terminal Flushes

**Priority: MEDIUM**

Batch all rendering operations and flush once per frame:

```python
class FrameRenderer:
    def __init__(self):
        self.operations = []
        
    def add_operation(self, op):
        self.operations.append(op)
        
    def render_frame(self):
        # Sort operations by screen position
        self.operations.sort(key=lambda op: (op.y, op.x))
        
        # Batch all terminal output
        output = []
        for op in self.operations:
            output.append(op.render())
            
        # Single flush for entire frame
        print(''.join(output), end='', flush=True)
        self.operations.clear()
```

### 9. Implement Viewport Culling

**Priority: LOW**

Only render entities and tiles within the visible viewport:

```python
def is_in_viewport(x, y, viewport):
    return (viewport.x <= x < viewport.x + viewport.width and
            viewport.y <= y < viewport.y + viewport.height)
```

### 10. Profile and Monitor Performance

**Priority: MEDIUM**

Add performance monitoring to identify bottlenecks:

```python
class PerformanceMonitor:
    def __init__(self):
        self.frame_times = []
        self.render_times = {}
        
    def measure_frame(self):
        start = time.perf_counter()
        yield
        frame_time = time.perf_counter() - start
        self.frame_times.append(frame_time)
        
        if len(self.frame_times) > 60:  # Keep last 60 frames
            self.frame_times.pop(0)
            
    def get_fps(self):
        if not self.frame_times:
            return 0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0
```

## Implementation Priority

1. **Immediate (High Impact, Low Effort)**:
   - Implement batch rendering for map tiles
   - Cache color escape sequences
   - Reduce full screen redraws

2. **Short Term (High Impact, Medium Effort)**:
   - Add dirty region tracking
   - Optimize entity rendering
   - Batch terminal operations per frame

3. **Medium Term (Medium Impact, High Effort)**:
   - Implement double buffering
   - Optimize message pane rendering
   - Add performance monitoring

4. **Long Term (Nice to Have)**:
   - Viewport culling
   - Advanced caching strategies
   - Terminal capability detection and optimization

## Expected Results

Implementing these optimizations should result in:
- 80-90% reduction in terminal I/O operations
- Elimination of visible screen flicker
- Smooth gameplay even on slow terminals or SSH connections
- Reduced CPU usage from string operations
- Better scalability for larger maps and more entities

## Testing Recommendations

1. Create performance benchmarks before implementing changes
2. Test on various terminal emulators (Windows Terminal, ConEmu, PuTTY)
3. Test over SSH connections to simulate latency
4. Monitor frame rates and render times
5. Use profiling tools to verify improvements

## Code Examples

For immediate implementation, here's a simple batch renderer that can replace the current character-by-character rendering:

```python
def render_map_batch(game_map, term):
    """Optimized map rendering using batching."""
    # Build output buffer
    output = []
    current_color = None
    
    for y in range(game_map.height):
        # Move to start of line
        output.append(term.move(y + game_map.y_offset, game_map.x_offset))
        
        for x in range(game_map.width):
            tile = game_map.tiles[y][x]
            color = game_map.get_tile_color(tile)
            
            # Only change color if different
            if color != current_color:
                if current_color is not None:
                    output.append(term.normal)
                output.append(term.color_rgb(*color))
                current_color = color
                
            output.append(tile)
    
    # Reset color at end
    output.append(term.normal)
    
    # Single print for entire map
    print(''.join(output), end='', flush=True)
```

This simple change alone should significantly improve performance by reducing terminal operations from O(width × height × 4) to O(width × height).