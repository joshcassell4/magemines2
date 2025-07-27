"""Factory function for creating map generators."""

from .base import MapGenerator, MapGeneratorConfig, GenerationMethod
from .dungeon import DungeonGenerator
from .cave import CaveGenerator
from .town import TownGenerator


def create_generator(config: MapGeneratorConfig, message_pane=None) -> MapGenerator:
    """Factory function to create the appropriate generator.
    
    Args:
        config: Configuration specifying which generator to create
        message_pane: Optional message pane for debug output
        
    Returns:
        An instance of the appropriate MapGenerator subclass
        
    Raises:
        ValueError: If the generation method is unknown
    """
    if config.method == GenerationMethod.ROOMS_AND_CORRIDORS:
        return DungeonGenerator(config, message_pane)
    elif config.method == GenerationMethod.CELLULAR_AUTOMATA:
        return CaveGenerator(config, message_pane)
    elif config.method == GenerationMethod.TOWN:
        return TownGenerator(config, message_pane)
    else:
        raise ValueError(f"Unknown generation method: {config.method}")