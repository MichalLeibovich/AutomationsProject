# Automations

Playwright automations, one folder per application, plus the runner that
executes them when someone presses **הרץ** on the dashboard.

## Layout

```
automations/
├── conftest.py                    fixtures + reporting to the NOC API
├── pytest.ini                     markers, test paths
├── requirements.txt
├── core/                          shared framework
│   ├── locators/                  every selector in the suite
│   ├── pages/                     BasePage, GoogleHomePage
│   └── utils/                     config, reporter, artifacts
├── magen_elyon_automations/
│   ├── tests/                     ← the automations
│   ├── pages/                     app-specific pages (empty for now)
│   └── locators/                  app-specific selectors (empty for now)
├── harmony_automations/
├── gaussian_automations/
├── butterfly_effect_automations/
├── general_automations/
└── runner/
    └── worker.py                  polls the queue, runs pytest
```

**Selectors live only in `core/locators/`.** Page objects import them; tests never
do. A test says `google_page.open()`, not "click the thing matching this CSS".

## Setup

```bash
cd backend/automations
pip install -r requirements.txt
playwright install chromium
```

## Running by hand

```bash
pytest                                            # all 19
pytest -m smoke                                   # main automations only
pytest harmony_automations/                       # one application
pytest harmony_automations/tests/test_smoke.py::test_site_is_reachable
AUTOMATION_HEADLESS=false pytest -m smoke         # watch the browser
```

Run by hand, **nothing is reported to the dashboard**. Reporting switches on only
when `NOC_RUN_ID` is set, which the runner does — so experimenting locally cannot
pollute the run history.

## Running the runner

This is what makes the **הרץ** button do something:

```bash
cd backend/automations
python -m runner.worker
```

It polls `GET /api/runs?status=queued` every two seconds, and for each queued run
executes its `runner_target` with pytest. Leave it running in its own terminal
alongside the backend and frontend.

```bash
python -m runner.worker --once              # drain the queue and exit
python -m runner.worker --run-id <UUID>     # execute one specific run
```

## How a click becomes a result

1. You press **הרץ** → `POST /api/runs` → a row with `status = 'queued'`
2. The worker polls, sees it, reads its `runner_target`
3. The worker runs `pytest <runner_target>` with `NOC_RUN_ID` in the environment
4. `conftest.py` claims the run → the dashboard shows **בריצה**
5. Each `with step(...)` block is timed and recorded
6. On finish the suite posts its steps, and the outcome
7. On failure it also captures a screenshot and attaches it

The `runner_target` is a pytest node id such as
`harmony_automations/tests/test_smoke.py::test_site_is_reachable`. That string is
the entire link between a database row and a real test on disk — which is why the
seed and these files have to agree.

## Adding an automation

1. Write the test in the right application's `tests/` folder
2. Register it, so the dashboard knows it exists:

```bash
curl -X POST localhost:8000/api/test-definitions \
  -H 'Content-Type: application/json' \
  -d '{"applicationId":"<APP_ID>","scope":"application","kind":"secondary",
       "name":"בדיקה חדשה",
       "runnerTarget":"harmony_automations/tests/test_new.py::test_thing"}'
```

Or add it to `SECONDARY_TESTS` in `backend/database/seed.py` and re-seed. The seed
upserts on `runnerTarget`, so re-running never duplicates.

Get application ids from `curl localhost:8000/api/applications`.

## Writing a test

Use the `step` fixture. It times each block and, when one raises, records *which*
step failed — so the debrief says "אימות טעינת הדף: timeout" instead of dumping a
traceback at an operator.

```python
def test_something(google_page, step):
    with step("פתיחת אתר היעד"):
        google_page.open()

    with step("אימות טעינת הדף"):
        assert google_page.is_loaded(), "תיבת החיפוש לא נטענה"
```

The step names appear on the dashboard, so write them as actions an operator
would recognise.

## Configuration

| Variable | Default                    | Purpose |
|---|----------------------------|---|
| `AUTOMATION_TARGET_URL` | `https://www.google.com`   | the site under test |
| `AUTOMATION_HEADLESS` | `true`                     | `false` to watch |
| `AUTOMATION_TIMEOUT_MS` | `15000`                    | element wait |
| `AUTOMATION_NAV_TIMEOUT_MS` | `30000`                    | page navigation |
| `AUTOMATION_ARTIFACTS_DIR` | `./artifacts`              | screenshots |
| `NOC_API_URL` | `http://localhost:8000/api` | where to report |
| `NOC_RUN_ID` | unset                      | set by the runner; enables reporting |

To point every automation at a different site, set `AUTOMATION_TARGET_URL`. The
page objects take the URL from configuration rather than hardcoding it.
