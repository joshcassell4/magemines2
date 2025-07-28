"""AI system for entity behaviors."""

import random
import logging
from typing import List, Optional, Tuple
from ..entities import Entity, EntityManager
from ..components import Position, AI, MagicUser, Health, Faction, Stats
from ..map import GameMap


class AISystem:
    """System for processing AI behaviors."""
    
    def __init__(self, entity_manager: EntityManager, game_map: GameMap):
        """Initialize the AI system.
        
        Args:
            entity_manager: The entity manager
            game_map: The game map
        """
        self.entity_manager = entity_manager
        self.game_map = game_map
        self.logger = logging.getLogger(__name__)
        
        # Behavior handlers
        self.behavior_handlers = {
            "idle": self._handle_idle,
            "patrol": self._handle_patrol,
            "study": self._handle_study,
            "erratic": self._handle_erratic,
            "boss": self._handle_boss,
            "flee": self._handle_flee,
            "attack": self._handle_attack,
            "cast": self._handle_cast,
        }
    
    def process_turn(self, player: Entity):
        """Process AI turns for all entities with AI components.
        
        Args:
            player: The player entity
        """
        # Get all entities with AI components
        ai_entities = self.entity_manager.get_entities_with_components(AI, Position)
        
        for entity in ai_entities:
            if entity.id == player.id or not entity.active:
                continue
                
            ai = entity.get_component(AI)
            if ai:
                # Process the entity's behavior
                handler = self.behavior_handlers.get(ai.behavior_type, self._handle_idle)
                handler(entity, player)
                
                # Update spell cooldowns if entity is a magic user
                magic = entity.get_component(MagicUser)
                if magic:
                    magic.update_cooldowns()
                    # Regenerate mana
                    stats = entity.get_component(Stats)
                    if stats:
                        magic.regenerate_mana(stats.mana_regen_rate)
    
    def _handle_idle(self, entity: Entity, player: Entity):
        """Handle idle behavior - do nothing or wander randomly."""
        # 20% chance to move randomly
        if random.random() < 0.2:
            self._move_randomly(entity)
    
    def _handle_patrol(self, entity: Entity, player: Entity):
        """Handle patrol behavior - move around territory, attack intruders."""
        ai = entity.get_component(AI)
        pos = entity.get_component(Position)
        
        if not ai or not pos:
            return
            
        # Check if player is nearby
        player_pos = player.get_component(Position)
        if player_pos:
            distance = self._get_distance(pos, player_pos)
            
            # If player is within 5 tiles, consider them an intruder
            if distance <= 5:
                # Check faction hostility
                faction = entity.get_component(Faction)
                if faction and faction.is_hostile_to(player.id):
                    # Switch to attack behavior
                    ai.set_behavior("attack", player.id)
                    self._handle_attack(entity, player)
                    return
        
        # Otherwise, patrol randomly
        if not ai.memory.get("patrol_direction"):
            ai.memory["patrol_direction"] = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
        
        dx, dy = ai.memory["patrol_direction"]
        if not self._try_move(entity, dx, dy):
            # Hit a wall, change direction
            ai.memory["patrol_direction"] = random.choice([(0, 1), (1, 0), (0, -1), (-1, 0)])
    
    def _handle_study(self, entity: Entity, player: Entity):
        """Handle study behavior - stay near magical objects, regenerate mana faster."""
        pos = entity.get_component(Position)
        if not pos:
            return
            
        # Check if near a magical tile (crystal, essence, altar)
        magical_tiles = ['*', '☼', '◊']  # Crystal/essence, light effect, altar
        tile = self.game_map.get_tile_at(pos.x, pos.y)
        
        if tile in magical_tiles:
            # Double mana regeneration when studying
            magic = entity.get_component(MagicUser)
            stats = entity.get_component(Stats)
            if magic and stats:
                magic.regenerate_mana(stats.mana_regen_rate)  # Extra regen
        else:
            # Move toward nearest magical object (simplified - just wander)
            if random.random() < 0.3:
                self._move_randomly(entity)
    
    def _handle_erratic(self, entity: Entity, player: Entity):
        """Handle erratic behavior - unpredictable actions."""
        ai = entity.get_component(AI)
        if not ai:
            return
            
        # Change mood randomly
        if random.random() < 0.2:
            ai.memory["mood"] = random.choice(["aggressive", "fearful", "curious", "helpful"])
        
        mood = ai.memory.get("mood", "curious")
        
        if mood == "aggressive":
            # Attack anything nearby
            ai.set_behavior("attack", player.id)
            self._handle_attack(entity, player)
        elif mood == "fearful":
            # Run away
            ai.set_behavior("flee", player.id)
            self._handle_flee(entity, player)
        elif mood == "curious":
            # Move toward player
            self._move_toward(entity, player)
        else:  # helpful
            # Just stand there
            pass
            
        # Reset to erratic after action
        ai.behavior_type = "erratic"
    
    def _handle_boss(self, entity: Entity, player: Entity):
        """Handle boss behavior - intelligent combat with phases."""
        ai = entity.get_component(AI)
        health = entity.get_component(Health)
        magic = entity.get_component(MagicUser)
        
        if not ai or not health or not magic:
            return
            
        # Determine combat phase based on health
        health_percent = health.percentage
        if health_percent > 0.75:
            phase = 1
        elif health_percent > 0.5:
            phase = 2
        elif health_percent > 0.25:
            phase = 3
        else:
            phase = 4
            
        ai.memory["phase"] = phase
        
        # Phase-based behavior
        if phase == 1:
            # Normal attacks
            ai.set_behavior("attack", player.id)
            self._handle_attack(entity, player)
        elif phase == 2:
            # Start using shields
            if magic.can_cast("arcane_shield", 5) and not ai.memory.get("shielded"):
                ai.set_behavior("cast", "arcane_shield")
                self._handle_cast(entity, player)
                ai.memory["shielded"] = True
            else:
                ai.set_behavior("attack", player.id)
                self._handle_attack(entity, player)
        elif phase == 3:
            # Teleport and attack
            teleport_cd = ai.memory.get("teleport_cooldown", 0)
            if teleport_cd <= 0 and magic.can_cast("teleport", 8):
                ai.set_behavior("cast", "teleport")
                self._handle_cast(entity, player)
                ai.memory["teleport_cooldown"] = 5
            else:
                ai.set_behavior("attack", player.id)
                self._handle_attack(entity, player)
                if teleport_cd > 0:
                    ai.memory["teleport_cooldown"] = teleport_cd - 1
        else:  # phase 4
            # Desperate attacks with powerful spells
            if magic.can_cast("lightning_strike", 7):
                ai.set_behavior("cast", "lightning_strike")
                self._handle_cast(entity, player)
            elif magic.can_cast("fireball", 6):
                ai.set_behavior("cast", "fireball")
                self._handle_cast(entity, player)
            else:
                ai.set_behavior("attack", player.id)
                self._handle_attack(entity, player)
    
    def _handle_flee(self, entity: Entity, player: Entity):
        """Handle flee behavior - run away from target."""
        entity_pos = entity.get_component(Position)
        player_pos = player.get_component(Position)
        
        if not entity_pos or not player_pos:
            return
            
        # Calculate direction away from player
        dx = 0 if entity_pos.x == player_pos.x else (1 if entity_pos.x > player_pos.x else -1)
        dy = 0 if entity_pos.y == player_pos.y else (1 if entity_pos.y > player_pos.y else -1)
        
        # Try to move away
        if not self._try_move(entity, dx, dy):
            # Can't move directly away, try perpendicular
            if dx == 0:
                self._try_move(entity, 1, 0) or self._try_move(entity, -1, 0)
            else:
                self._try_move(entity, 0, 1) or self._try_move(entity, 0, -1)
    
    def _handle_attack(self, entity: Entity, player: Entity):
        """Handle attack behavior - move toward target and cast spells."""
        entity_pos = entity.get_component(Position)
        player_pos = player.get_component(Position)
        magic = entity.get_component(MagicUser)
        
        if not entity_pos or not player_pos:
            return
            
        distance = self._get_distance(entity_pos, player_pos)
        
        # If has magic and in range, try to cast a spell
        if magic and magic.known_spells:
            # Find a suitable offensive spell
            from ..data.spells import get_spell
            
            for spell_id in magic.known_spells:
                spell_data = get_spell(spell_id)
                if spell_data and spell_data.effect_type in ["damage", "debuff"]:
                    # Check if in range and can cast
                    if distance <= spell_data.range and magic.can_cast(spell_id, spell_data.mana_cost):
                        ai = entity.get_component(AI)
                        if ai:
                            ai.set_behavior("cast", spell_id)
                            self._handle_cast(entity, player)
                        return
        
        # Otherwise, move closer
        if distance > 1:
            self._move_toward(entity, player)
    
    def _handle_cast(self, entity: Entity, player: Entity):
        """Handle spell casting."""
        ai = entity.get_component(AI)
        magic = entity.get_component(MagicUser)
        
        if not ai or not magic or not ai.target:
            return
            
        spell_id = ai.target
        from ..data.spells import get_spell
        spell_data = get_spell(spell_id)
        
        if not spell_data:
            return
            
        # Check if already casting
        if magic.casting_spell:
            # Continue casting
            magic.cast_progress += 1
            if magic.cast_progress >= spell_data.cast_time:
                # Spell is ready, execute it
                self._execute_spell(entity, spell_id, player)
                magic.finish_casting(spell_id, spell_data.cooldown)
                # Return to previous behavior
                ai.behavior_type = ai.memory.get("previous_behavior", "idle")
        else:
            # Start casting
            if magic.can_cast(spell_id, spell_data.mana_cost):
                magic.start_casting(spell_id)
                ai.memory["previous_behavior"] = ai.memory.get("current_behavior", "idle")
                
                # Spend mana for instant spells
                if spell_data.is_instant:
                    magic.spend_mana(spell_data.mana_cost)
                    self._execute_spell(entity, spell_id, player)
                    magic.finish_casting(spell_id, spell_data.cooldown)
                    ai.behavior_type = ai.memory.get("previous_behavior", "idle")
    
    def _execute_spell(self, caster: Entity, spell_id: str, target: Entity):
        """Execute a spell effect (placeholder for now)."""
        # This is where spell effects would be applied
        # For now, just log it
        from ..data.spells import get_spell
        spell_data = get_spell(spell_id)
        
        if spell_data:
            self.logger.info(f"{caster.id} casts {spell_data.name} at {target.id}")
            # TODO: Implement actual spell effects when we have the magic system
    
    def _move_randomly(self, entity: Entity):
        """Move entity in a random direction."""
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            if self._try_move(entity, dx, dy):
                break
    
    def _move_toward(self, entity: Entity, target: Entity):
        """Move entity toward target."""
        entity_pos = entity.get_component(Position)
        target_pos = target.get_component(Position)
        
        if not entity_pos or not target_pos:
            return
            
        # Calculate direction
        dx = 0 if entity_pos.x == target_pos.x else (1 if entity_pos.x < target_pos.x else -1)
        dy = 0 if entity_pos.y == target_pos.y else (1 if entity_pos.y < target_pos.y else -1)
        
        # Try to move in that direction
        if not self._try_move(entity, dx, dy):
            # Try moving in just one direction
            if dx != 0 and self._try_move(entity, dx, 0):
                return
            if dy != 0 and self._try_move(entity, 0, dy):
                return
    
    def _try_move(self, entity: Entity, dx: int, dy: int) -> bool:
        """Try to move an entity, returns True if successful."""
        pos = entity.get_component(Position)
        if not pos:
            return False
            
        new_x = pos.x + dx
        new_y = pos.y + dy
        
        # Check bounds
        if new_x < 0 or new_x >= self.game_map.width or new_y < 0 or new_y >= self.game_map.height:
            return False
            
        # Check if blocked (ignore the entity itself)
        if self.game_map.is_blocked(new_x, new_y, ignore_entity_id=entity.id):
            return False
        
        # Move the entity
        self.game_map.move_entity(entity, new_x, new_y)
        return True
    
    def _get_distance(self, pos1: Position, pos2: Position) -> int:
        """Get the Manhattan distance between two positions."""
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)