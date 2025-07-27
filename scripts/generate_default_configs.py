#!/usr/bin/env python3
"""Generate default configuration files for MageMines."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from magemines.core.config import ConfigurationManager


def main():
    """Generate all default configuration files."""
    print("Generating default configuration files...")
    
    # Create configuration manager
    config_manager = ConfigurationManager()
    
    # Create all default configs
    config_manager.create_default_configs()
    
    print(f"Configuration files created in: {config_manager.config_dir}")
    print("\nCreated files:")
    for config_file in sorted(config_manager.config_dir.glob("*.json")):
        print(f"  - {config_file.name}")
        

if __name__ == "__main__":
    main()