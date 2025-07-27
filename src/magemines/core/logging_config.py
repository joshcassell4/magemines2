"""Logging configuration for MageMines."""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class LoggingConfig:
    """Centralized logging configuration for the application."""
    
    # Default log directory
    LOG_DIR = Path("logs")
    
    # Log format
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    
    # Log file settings
    MAX_BYTES = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    
    _initialized = False
    
    @classmethod
    def setup_logging(
        cls,
        log_level: str = "INFO",
        log_to_console: bool = True,
        log_to_file: bool = True,
        log_dir: Optional[Path] = None,
        detailed_format: bool = False
    ) -> None:
        """Set up the logging configuration for the entire application.
        
        Args:
            log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_to_console: Whether to log to console
            log_to_file: Whether to log to file
            log_dir: Custom log directory (uses default if None)
            detailed_format: Whether to use detailed format (includes file/line info)
        """
        if cls._initialized:
            return
            
        # Create log directory if needed
        if log_dir is None:
            log_dir = cls.LOG_DIR
        log_dir.mkdir(exist_ok=True)
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Choose format
        formatter = logging.Formatter(
            cls.DETAILED_FORMAT if detailed_format else cls.LOG_FORMAT
        )
        
        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, log_level.upper()))
            root_logger.addHandler(console_handler)
        
        # File handler with rotation
        if log_to_file:
            # Create timestamped log file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"magemines_{timestamp}.log"
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=cls.MAX_BYTES,
                backupCount=cls.BACKUP_COUNT
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
            root_logger.addHandler(file_handler)
            
            # Also create a latest.log symlink/copy for easy access
            latest_log = log_dir / "latest.log"
            try:
                if latest_log.exists():
                    latest_log.unlink()
                # On Windows, we'll copy instead of symlink
                if os.name == 'nt':
                    import shutil
                    shutil.copy2(log_file, latest_log)
                else:
                    latest_log.symlink_to(log_file.name)
            except Exception:
                pass  # Ignore symlink errors
        
        cls._initialized = True
        
        # Log startup message
        logger = logging.getLogger(__name__)
        logger.info("=" * 60)
        logger.info("MageMines logging initialized")
        logger.info(f"Log level: {log_level}")
        logger.info(f"Log directory: {log_dir.absolute()}")
        logger.info(f"Console logging: {log_to_console}")
        logger.info(f"File logging: {log_to_file}")
        logger.info("=" * 60)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger instance for a specific module.
        
        Args:
            name: The name of the logger (usually __name__)
            
        Returns:
            A configured logger instance
        """
        # Ensure logging is set up with defaults if not already done
        if not cls._initialized:
            cls.setup_logging()
        
        return logging.getLogger(name)


# Convenience function for getting loggers
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.
    
    Args:
        name: The name of the logger (usually __name__)
        
    Returns:
        A configured logger instance
    """
    return LoggingConfig.get_logger(name)