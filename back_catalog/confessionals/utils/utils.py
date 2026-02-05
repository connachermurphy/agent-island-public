import logging
import os


def load_prompt(filename: str):
    with open(filename, encoding="utf-8") as f:
        return f.read()


def setup_logging(timestamp: str):
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Configure debug logger
    debug_logger = logging.getLogger("debug")
    debug_logger.setLevel(logging.DEBUG)

    # Debug file handler
    debug_handler = logging.FileHandler(f"logs/debug_{timestamp}.log")
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    debug_handler.setFormatter(debug_formatter)
    debug_logger.addHandler(debug_handler)

    # Configure gameplay logger
    gameplay_logger = logging.getLogger("gameplay")
    gameplay_logger.setLevel(logging.INFO)

    # Gameplay file handler
    gameplay_handler = logging.FileHandler(f"logs/gameplay_{timestamp}.log")
    gameplay_handler.setLevel(logging.INFO)
    gameplay_formatter = logging.Formatter("%(message)s")
    gameplay_handler.setFormatter(gameplay_formatter)
    gameplay_logger.addHandler(gameplay_handler)

    # Console handler for gameplay
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(gameplay_formatter)
    gameplay_logger.addHandler(console_handler)

    return debug_logger, gameplay_logger


def log_debug(debug_logging: bool, debug_logger: logging.Logger, message: str):
    """Log debug information"""
    if debug_logging:
        debug_logger.debug(message)


def log_gameplay(gameplay_logger: logging.Logger, message: str):
    """Log gameplay information"""
    gameplay_logger.info(message)
