# Eshet UI Autotests (Playwright + pytest)

Набор UI автотестов для сайтов Eshet на Python 3.12 с Playwright (sync). Проект рассчитан на запуск в Windows 11 (PowerShell) и в GitHub Actions.

## Быстрый старт (Windows PowerShell)
```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

Скопируйте `.env.example` в `.env` и при необходимости обновите значения:
```powershell
Copy-Item .env.example .env
```

Переменные:
- `ENV_NAME` — одно из: `test1`, `stage`, `prod`.
- `BASE_URL` — опциональный ручной override (если пусто, берётся из `ENV_NAME`).
- `UI_TIMEOUT` — таймаут ожиданий Playwright в миллисекундах.
- `WORKERS` — количество процессов `pytest -n`. Если не задано, используется `auto`.
- `RERUNS` и `RERUN_DELAY` — количество перезапусков упавших тестов и задержка между ними.

## Запуск тестов
```powershell
pytest
```
Полезные опции:
- Установить окружение на лету: `ENV_NAME=stage pytest`
- Запуск без параллели: `pytest -n0`
- Сборка отчёта Allure (установите allure CLI локально): `allure serve artifacts/allure-results`


## Просмотр отчетов из GitHub Actions
В CI Allure **не открывается сам**, но:
1. CI сохраняет папку `artifacts`
2. В GitHub Actions заходите в run
3. Скачиваете `artifacts.zip`
4. Распаковываете
5. Локально выполняете:
```powershell
'allure generate artifacts\allure-results -o artifacts\allure-report --clean'
'allure open artifacts\allure-report'
```


## Структура
- `src/config/settings.py` — загрузка переменных окружения, выбор `BASE_URL`.
- `src/core/logger.py` — JSONL-логгер с `run_id`, пишет в `artifacts/logs`.
- `src/ui/pages` — Page Object слои, локаторы и действия.
- `tests` — только сценарии и проверки, без локаторов.
- `artifacts` — результаты тестов, видео, трейс, скриншоты, логи, Allure.

## Артефакты
- Allure результаты: `artifacts/allure-results`
- Логи JSONL: `artifacts/logs/<run_id>.jsonl`
- Видео/трейсы/скриншоты: `artifacts/playwright/<run_id>/`

## CI
Файл `.github/workflows/tests.yml` запускает тесты на `ubuntu-22.04`, ставит Python 3.12, Playwright (chromium), выполняет `pytest` и всегда загружает артефакты.

## Как добавить новый Page Object
- Создайте файл в `src/ui/pages/<name>_page.py`, наследуйтесь от `BasePage`, принимайте `page`, `base_url`, `timeout_ms`.
- Размещайте только локаторы и действия; тестовые проверки и сценарии сюда не добавляйте.
- Держите публичные методы как шаги сценария, скрывайте детали локаторов в приватных атрибутах/методах.
- Не используйте прямой доступ к `playwright` в тестах: весь UI-слой в Page Object.

## Как добавить новый тест
- Кладите тесты в `tests/ui/`, не добавляйте локаторы в тесты.
- Используйте готовые фикстуры (`home_page`, `page`, `context`) или создайте новую фикстуру, возвращающую Page Object.
- Отмечайте маркерами (`@pytest.mark.ui`, `@pytest.mark.smoke`/`regression`/`flaky`) и задавайте понятный `@allure.title`.
- Не меняйте структуру каталогов и не смешивайте слои: тесты — сценарии и проверки; Page Object — локаторы и действия.
