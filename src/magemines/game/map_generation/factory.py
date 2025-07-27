"""Factory function for creating map generators."""

from .base import MapGenerator, MapGeneratorConfig, GenerationMethod
from .dungeon import DungeonGenerator
from .cave import CaveGenerator
from .town import TownGenerator


def create_generator(config: MapGeneratorConfig) -> MapGenerator:
    """Factory function to create the appropriate generator.
    
    Args:
        config: Configuration specifying which generator to create
        
    Returns:
        An instance of the appropriate MapGenerator subclass
        
    Raises:
        ValueError: If the generation method is unknown
    """
    if config.method == GenerationMethod.ROOMS_AND_CORRIDORS:
        return DungeonGenerator(config)
    elif config.method == GenerationMethod.CELLULAR_AUTOMATA:
        return CaveGenerator(config)
    elif config.method == GenerationMethod.TOWN:
        return TownGenerator(config)
    else:
        raise ValueError(f"Unknown generation method: {config.method}")