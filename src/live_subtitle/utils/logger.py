import logging
import os
import sys
from pathlib import Path

def setup_logger(name: str = "LiveSubtitle", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a centralized application logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(funcName)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional local file handler
    try:
        app_data = os.getenv("LOCALAPPDATA", str(Path.home()))
        log_dir = Path(app_data) / "LiveSubtitle" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not initialize log file: {e}")

    return logger

logger = setup_logger()
