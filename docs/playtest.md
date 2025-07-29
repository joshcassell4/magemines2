# Playtest Guide for MageMines

Last Updated: 2025-01-25

## Current Development Status

### What's Playable Now

The game currently offers a **foundational exploration experience** with the following features:

1. **Basic Movement**
   - Vim-style movement (hjkl)
   - Diagonal movement (yubn)
   - Wait action (.)
   - Collision detection with walls

2. **Message System**
   - Side-by-side layout (map left, messages right)
   - Scrollable message history (-/+ keys)
   - Turn tracking with [T#] prefixes
   - Descriptive feedback for blocked movement

3. **Map**
   - Procedural dungeon generation with rooms and corridors
   - Multiple generation algorithms (Dungeon, Cave, Town)
   - Player represented by '@'
   - Walls represented by '#'
   - Empty space represented by '.'
   - Stairs up/down represented by '<' and '>'
   - Doors represented by '+' (in town maps)
   - Altars represented by '▲' (in town centers)

### What's Missing (But Coming Soon)

- No NPCs or other entities
- No resource gathering or crafting
- No divine powers or spells
- No atmospheric effects or evolving symbols
- No save/load functionality
- No color (monochrome ASCII only)

## Playtest Scripts

### Script 1: Basic Navigation & Boundaries
**Goal**: Test movement system and collision feedback

```
1. Start the game
2. Note your starting position (should be at 10,10)
3. Move in each cardinal direction (h,j,k,l) and observe:
   - Does the @ symbol move smoothly?
   - Do you see turn numbers incrementing?
4. Try to walk into walls:
   - Move to a wall and try to pass through
   - Check message: Should say "A wall blocks your path!"
5. Try to leave the map:
   - Move to the edge and try to go beyond
   - Check message: Should say "You can't leave the map!"
6. Test diagonal movement (y,u,b,n)
7. Test waiting in place (.)
```

### Script 2: Message System Exploration
**Goal**: Test the message pane functionality

```
1. Start fresh, note the welcome messages
2. Make several moves, creating a message history
3. Test scrolling:
   - Press - to scroll up (view older messages)
   - Press + to scroll down (view newer messages)
   - Look for ^ and v indicators
4. Create many messages by repeatedly hitting walls
5. Check that messages have turn numbers [T#]
6. Verify system messages don't have turn prefixes
```

### Script 3: Input Responsiveness
**Goal**: Test input buffer management

```
1. Hold down a movement key (like 'l') for 2 seconds
2. Release and observe:
   - Does movement stop immediately?
   - Are there queued movements that execute?
3. Rapidly alternate between two keys (h and l)
4. Test the quit sequence:
   - Press q
   - Observe confirmation prompt
   - Press n to cancel
   - Press q again, then y to quit
```

### Script 4: Atmospheric Exploration
**Goal**: Begin imagining the world that will emerge

```
1. Start the game
2. As you move, imagine:
   - What kind of space is this?
   - What might be beyond the walls?
   - Where would ancient doors appear?
3. Find a corner and "wait" there several turns
   - Imagine this space becoming "more alive"
   - What would change if you spent time here?
4. Walk a specific pattern (like a circle)
   - Consider: what rituals might emerge?
5. Document your imaginative observations
```

### Script 5: Procedural Dungeon Exploration
**Goal**: Experience the new procedural generation

```
1. Start the game multiple times to see different layouts
2. Note your starting position (should be near stairs <)
3. Explore the dungeon:
   - Count how many rooms you find
   - Notice how corridors connect spaces
   - Find the down stairs (>)
4. Test movement in tight corridors
5. Try to find any isolated areas
6. Notice emergent "special" rooms (dead ends feel important!)
```

### Script 6: Map Generation Variety
**Goal**: Understand the different generation styles

```
1. Run the playtest_map_generation.py script
2. Open map_samples directory
3. Compare the different map types:
   - Dungeon: Room-based with corridors
   - Cave: Organic, flowing spaces
   - Town: Urban layout with buildings
4. Consider which style fits different game phases
5. Imagine how each would feel to explore
```

## Playtest Feedback Template

When playtesting, please note:

### Technical Observations
- [ ] Movement feels responsive
- [ ] Messages display correctly
- [ ] Turn numbers increment properly
- [ ] Scrolling works as expected
- [ ] No visual glitches or artifacts

### Atmospheric Impressions
- What mood does the current game evoke?
- What's missing that would enhance atmosphere?
- Any "happy accidents" or unexpected feelings?

### Feature Desires
- What do you most want to do that you can't?
- What would make exploration more interesting?
- Ideas for the first "living" element to add?

## Next Features to Playtest

Based on the evolving vision of "Whispers Beneath the Mountain", the next features to implement and playtest are:

1. **Time-Based Changes** (Priority 1)
   - Areas that track "presence" (time spent there)
   - Subtle symbol evolution (. → : → ∴ → ※)
   - First hints of spaces becoming "alive"

2. **Atmospheric Elements** (Priority 2)
   - Fog of war / visibility
   - Memory of places visited
   - Ambient "whispers" in messages

3. **First Interactive Element** (Priority 3)
   - An ancient door that "shimmers"
   - Knock/interact command
   - Echo or response system

## Development Notes

The game is transitioning from a traditional roguelike to something more mysterious and emergent. Each playtest should help us discover what this game wants to become, rather than forcing it into predetermined patterns.

### Current Technical Debt
- No tests for emergent features (intentional)
- Message system could support richer formatting
- No configuration or settings
- Level transitions not yet implemented (stairs are visual only)

### Philosophical Considerations
- How much should be predictable vs emergent?
- What makes an ASCII space feel "alive"?
- How can we embrace "sacred chaos" in the design?

---

*Remember: In Playtest Driven Development, surprising moments and unexpected behaviors are often more valuable than bug reports. Document the magic, not just the mistakes.*