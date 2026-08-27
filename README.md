# NOC Test Management Dashboard

Operations console for monitoring and triggering automated tests across four
applications plus a shared general-automation scope. Hebrew interface,
right-to-left throughout.

```
noc-test-dashboard/
├── frontend/          React + TypeScript + Vite + MUI + Jotai + Axios
├── backend/           Flask + psycopg2 + PostgreSQL
│   └── automations/   Playwright + pytest (Page Object Model)
├── docker-compose.yml PostgreSQL + MinIO for local development
└── README.md
```

Each half has independent package management: `frontend/package.json` and
`backend/requirements.txt` share nothing.

---

## Quick start

Prerequisites: Node 20+, Python 3.11+, Docker.

```bash
# 1. dependencies
docker compose up -d                      # PostgreSQL :5432, MinIO :9000

# 2. backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                      # set DATABASE_URL and JWT_SECRET
python -m database.seed --days 75         # applies schema, generates history
python server.py                          # → http://localhost:8000

# 3. frontend
cd ../frontend
npm install
cp .env.example .env
npm run dev                               # → http://localhost:5173
```

Sign in with `michal@noc.local` / `noc-dev-password` (operator). Other seeded
accounts, including admin and a privileged operator, are in
`backend/automations/data/users.json`.

---

## What the product does

**Tests** — one card per application. Each card leads with that application's
single main test, with secondary tests behind a disclosure. Selecting the
General scope replaces the grid with the five shared automations, which have no
hierarchy because there is no primary task among them.

**Dashboard** — four KPIs (total runs, pass rate, failures, average duration)
over a selectable window, plus run volume over time, failures by feature, and a
breakdown of error types.

**Timeline** — the full run history: searchable, sortable, filterable by status,
with a debrief panel per run and asynchronous CSV export.

**Calendar** — a month grid of run activity. Clicking a day opens that day's
runs on an hour rail; clicking a run pushes it onto the same panel.

### Scope model

The filter row reads `[All applications] │ four application pills │ [General]`,
with hairline dividers marking the bookends as modes rather than products.
Selecting "all applications" aggregates the four products and **excludes**
General, because general automation is not attributable to any one of them.

The bulk "run all main tests" action is **hidden** in the General scope. Those
automations mutate production permissions, and bulk-firing them is the accident
most worth designing out. The API refuses the request independently of the UI.

---

## Design decisions worth knowing

### `useStyles` via `tss-react`

MUI removed `makeStyles`; `@mui/styles` is legacy and misbehaves under React 18
StrictMode. `tss-react/mui` is the migration path MUI's own documentation points
to, and it gives the required pattern:

```ts
// ButtonStyles.ts — all appearance lives here
export const useStyles = makeStyles()(() => ({ root: { /* … */ } }));
```

```tsx
// Button.tsx — no styling logic, only class selection
const { classes, cx } = useStyles();
```

The destructured form is the library's API, and it also yields `cx` for
conditional classes. Every one of the 16 components and 6 pages follows the
`ComponentName/{ComponentName.tsx, ComponentNameStyles.ts}` pair.

### RTL without per-component work

Two emotion caches — one for MUI with `prepend: true`, one for tss — both
running `stylis-plugin-rtl`. Physical CSS properties are flipped at insertion
time, which is why components are authored as though LTR and still render
correctly in Hebrew. Both caches exist separately because on equal specificity
the later-inserted rules win, and component styles must be able to override MUI
defaults.

Charts are handled per chart type, not uniformly: the volume chart keeps time
flowing left-to-right (the convention in Hebrew dashboards) with only its value
axis moved right, while the categorical failures chart mirrors fully.

### Jotai for state, Context only where it earns it

Global state — the current user, derived permissions, scope selection, the panel
navigation stack, live run status, toasts — lives in Jotai atoms.

React Context is used exactly twice, where the value is genuinely tree-scoped:

- **`ThemeContext`** — the MUI theme and RTL caches. Never mutated by
  application logic and read through MUI's own `useTheme`.
- **`ConfirmContext`** — an imperative `await confirm({…})`. An atom would only
  expose state, forcing every caller to reimplement the wait-for-the-answer
  plumbing.

The current user deliberately does *not* live in Context — that would duplicate
what `userAtom` already does.

### The detail panel is a navigation stack

Opening a run from a day pushes onto a stack and slides sideways with a back
crumb; it never stacks a second overlay. Escape steps back one level rather than
dismissing everything. Below 720px the same panel becomes a bottom sheet. This
replaced a centred dialog that was being painted over by the sticky header.

### Idempotent run submission

Every trigger carries a client-generated key, so a double-click or a retried
request cannot enqueue the same run twice. Because `test_runs` is partitioned,
this required a separate unpartitioned claim table — the detail is explained in
`backend/README.md`, and it is the one piece of the schema worth reading before
changing anything.

---

## Testing

```bash
cd frontend && npm run typecheck && npm run build
cd backend && pytest
cd backend/automations && pytest -m smoke
```

The Playwright suite uses the Page Object Model with a hard rule: **no selector
appears anywhere in `tests/`.** Every selector lives in `locators/`, page objects
are the only consumers, and CI enforces it:

```bash
grep -rE "data-testid|querySelector|xpath=" backend/automations/tests/ && exit 1
```

Tests that trigger general automations are marked `privileged` and skipped
unless run with `--allow-privileged`.

---

## Environment

Both halves ship `.env.example`. The values that actually need attention:

| Variable | Where | Note |
|---|---|---|
| `DATABASE_URL` | backend | PostgreSQL DSN |
| `JWT_SECRET` | backend | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `CORS_ORIGINS` | backend | comma-separated; the Vite origin in dev |
| `VITE_API_BASE_URL` | frontend | `/api`, proxied by Vite in dev |

---

## Production notes

```bash
# backend
gunicorn --workers 4 --threads 2 --bind 0.0.0.0:8000 wsgi:application

# frontend
npm run build      # → dist/, serve behind any static host or CDN
```

Threads matter for the backend: the live-status endpoint holds an SSE connection
open for its lifetime, so a purely process-based worker model runs out of
capacity as soon as a handful of dashboards are open.

Do not use `database/seed.py` or `apply_schema()` in production — they exist for
local development and CI. Production should use versioned migrations applied by a
role with DDL rights, after which the application connects as a member of
`noc_app`:

```sql
GRANT noc_app TO your_login_role;
```

The application role deliberately cannot create tables or modify the audit log.
See `backend/README.md` for the full privilege model.
