"""Entity system for the game."""

from typing import Dict, Type, Optional, TypeVar, List
from .components import Component, Position, Renderable

T = TypeVar('T', bound=Component)


class Entity:
    """Base entity class using component system."""
    
    def __init__(self, entity_id: int):
        self.id = entity_id
        self.components: Dict[Type[Component], Component] = {}
        self.active = True
    
    def add_component(self, component: Component):
        """Add a component to the entity."""
        self.components[type(component)] = component
    
    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """Get a component of a specific type."""
        return self.components.get(component_type)
    
    def has_component(self, component_type: Type[Component]) -> bool:
        """Check if the entity has a component of a specific type."""
        return component_type in self.components
    
    def remove_component(self, component_type: Type[Component]):
        """Remove a component from the entity."""
        if component_type in self.components:
            del self.components[component_type]
    
    # Convenience properties for common components
    @property
    def position(self) -> Optional[Position]:
        """Get the position component."""
        return self.get_component(Position)
    
    @property
    def renderable(self) -> Optional[Renderable]:
        """Get the renderable component."""
        return self.get_component(Renderable)
    
    def move(self, dx: int, dy: int):
        """Move the entity if it has a position component."""
        pos = self.position
        if pos:
            pos.move(dx, dy)


class EntityManager:
    """Manages all entities in the game."""
    
    def __init__(self):
        self.entities: Dict[int, Entity] = {}
        self.next_id = 1
        # Component indexes for efficient queries
        self.component_index: Dict[Type[Component], List[int]] = {}
    
    def create_entity(self) -> Entity:
        """Create a new entity."""
        entity = Entity(self.next_id)
        self.entities[self.next_id] = entity
        self.next_id += 1
        return entity
    
    def add_entity(self, entity: Entity):
        """Add an existing entity to the manager."""
        self.entities[entity.id] = entity
        # Update component indexes
        for component_type in entity.components:
            if component_type not in self.component_index:
                self.component_index[component_type] = []
            self.component_index[component_type].append(entity.id)
    
    def remove_entity(self, entity_id: int):
        """Remove an entity from the manager."""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            # Remove from component indexes
            for component_type in entity.components:
                if component_type in self.component_index:
                    self.component_index[component_type].remove(entity_id)
            del self.entities[entity_id]
    
    def get_entity(self, entity_id: int) -> Optional[Entity]:
        """Get an entity by ID."""
        return self.entities.get(entity_id)
    
    def get_entities_with_component(self, component_type: Type[Component]) -> List[Entity]:
        """Get all entities that have a specific component type."""
        if component_type not in self.component_index:
            return []
        
        entities = []
        for entity_id in self.component_index[component_type]:
            if entity_id in self.entities:
                entities.append(self.entities[entity_id])
        return entities
    
    def get_entities_with_components(self, *component_types: Type[Component]) -> List[Entity]:
        """Get all entities that have all specified component types."""
        if not component_types:
            return list(self.entities.values())
        
        # Start with entities that have the first component
        result_ids = set(self.component_index.get(component_types[0], []))
        
        # Intersect with entities that have each subsequent component
        for component_type in component_types[1:]:
            result_ids &= set(self.component_index.get(component_type, []))
        
        # Return the actual entities
        return [self.entities[entity_id] for entity_id in result_ids if entity_id in self.entities]
    
    def update_component_index(self, entity: Entity, component_type: Type[Component], added: bool):
        """Update the component index when a component is added or removed."""
        if component_type not in self.component_index:
            self.component_index[component_type] = []
        
        if added and entity.id not in self.component_index[component_type]:
            self.component_index[component_type].append(entity.id)
        elif not added and entity.id in self.component_index[component_type]:
            self.component_index[component_type].remove(entity.id)