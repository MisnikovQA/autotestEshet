import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_logger(run_id: str, logs_dir: Path) -> logging.Logger:
    logger_name = f"ui-tests-{run_id}"
    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    _ensure_dir(logs_dir)
    logfile = logs_dir / f"{run_id}.jsonl"

    class JsonLineFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload: Dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "run_id": run_id,
            }
            extra_data: Optional[Dict[str, Any]] = getattr(record, "extra_data", None)
            if isinstance(extra_data, dict):
                payload.update(extra_data)
            return json.dumps(payload, ensure_ascii=True)

    file_handler = logging.FileHandler(logfile, encoding="utf-8")
    file_handler.setFormatter(JsonLineFormatter())

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger


def log_json(logger: logging.Logger, message: str, **extra_data: Any) -> None:
    logger.info(message, extra={"extra_data": extra_data} if extra_data else None)
