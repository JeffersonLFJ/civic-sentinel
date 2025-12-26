import logging
import sys
from pathlib import Path

def setup_logging():
    """
    Configures logging to file and console.
    """
    log_dir = Path("data")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    # Format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info("Logging initialized. Writing to data/app.log")
