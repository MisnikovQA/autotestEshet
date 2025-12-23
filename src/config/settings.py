import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ENV_URLS = {
    "test1": "https://eshettestui-test1.azurewebsites.net/",
    "stage": "https://stage.eshet.com/",
    "prod": "https://www.eshet.com/",
}


@dataclass(frozen=True)
class Settings:
    env_name: str
    base_url: str
    ui_timeout: int
    workers: str
    reruns: int
    rerun_delay: int
    artifacts_dir: Path
    allure_results_dir: Path
    logs_dir: Path
    playwright_dir: Path


@lru_cache
def get_settings() -> Settings:
    load_dotenv()

    env_name = os.getenv("ENV_NAME", "test1").strip().lower()
    base_url_override = os.getenv("BASE_URL", "").strip()
    base_url = base_url_override or ENV_URLS.get(env_name)
    if not base_url:
        supported = ", ".join(ENV_URLS.keys())
        raise ValueError(f"Unsupported ENV_NAME '{env_name}'. Supported: {supported}. Or set BASE_URL override.")

    ui_timeout = int(os.getenv("UI_TIMEOUT", "10000"))
    workers = os.getenv("WORKERS", "").strip().lower() or "auto"
    reruns = int(os.getenv("RERUNS", "1"))
    rerun_delay = int(os.getenv("RERUN_DELAY", "2"))

    project_root = Path(__file__).resolve().parents[2]
    artifacts_dir = project_root / "artifacts"

    return Settings(
        env_name=env_name,
        base_url=base_url,
        ui_timeout=ui_timeout,
        workers=workers,
        reruns=reruns,
        rerun_delay=rerun_delay,
        artifacts_dir=artifacts_dir,
        allure_results_dir=artifacts_dir / "allure-results",
        logs_dir=artifacts_dir / "logs",
        playwright_dir=artifacts_dir / "playwright",
    )
