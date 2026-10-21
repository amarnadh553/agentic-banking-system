
import logging
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class Logger:
    
    def __init__(self, file_name = None, log_dir = None) -> None:

        self.log_dir = Path(log_dir) if log_dir else LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if not file_name:
            file_name = f"log_{datetime.now():%Y%m%d_%H%M%S}.log"
        self.file_path = self.log_dir / file_name
        self._configure_logger()

    def _configure_logger(self):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", filename=str(self.file_path), encoding="utf-8")

    def get_logger(self, name: str = __name__):
        return logging.getLogger(name)
