import logging
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime

# Load .env
load_dotenv()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger = logging.getLogger("rename_genie")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Generate timestamp for filenames
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Default log file (general logs) → with timestamp
general_log_file = log_dir / f"{timestamp}-app-general.log"
general_handler = logging.FileHandler(general_log_file)
general_handler.setFormatter(log_formatter)
logger.addHandler(general_handler)

# Global variables for run-specific logging
CURRENT_RUN_ID = None
CURRENT_RUN_HANDLER = None


def set_run_logger(run_id: str):
    """Switch logging to per-run log file (with timestamp)."""
    global CURRENT_RUN_ID, CURRENT_RUN_HANDLER
    CURRENT_RUN_ID = run_id

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_log_file = log_dir / f"{run_timestamp}-{run_id}-app.log"

    run_handler = logging.FileHandler(run_log_file)
    run_handler.setFormatter(log_formatter)
    logger.addHandler(run_handler)
    CURRENT_RUN_HANDLER = run_handler

    # Detach general handler
    logger.removeHandler(general_handler)
    logger.info(f"[{run_id}] Run logger initialized")


def reset_run_logger():
    """Reset logging to general log."""
    global CURRENT_RUN_ID, CURRENT_RUN_HANDLER
    if CURRENT_RUN_HANDLER:
        logger.removeHandler(CURRENT_RUN_HANDLER)
    CURRENT_RUN_ID = None
    CURRENT_RUN_HANDLER = None
    logger.addHandler(general_handler)
    logger.info("Run logger reset; logging back to general log")
