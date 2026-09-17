# JobTrack — Job Application Automation Dashboard

A full-stack dashboard for running a job search like a pipeline: track opportunities
through six statuses, store multiple resumes, get follow-up reminders, see conversion
analytics, and let a Playwright worker fill repetitive application forms for you —
stopping before Submit.

**Stack:** React 19 · Vite · React Router · Axios · Tailwind CSS 4 · Recharts ·
Django 6 · Django REST Framework · JWT · PostgreSQL · Playwright

---

## The automation policy

This is the part worth reading before anything else.

The form filler **types, uploads, screenshots, and then stops.** It hands you the
open browser window to review and press Submit yourself. Three independent
switches must *all* be on before any run submits on your behalf:

1. The site is on the allowlist **and** publishes an official application API
   (`SupportedSite.supports_official_api`).
2. The deployment allows it (`AUTOMATION_ALLOW_AUTO_SUBMIT` in `.env`).
3. The user allows it (Settings → Allow automated submission).

Miss any one and the run ends at `awaiting_review` with a plain-language reason.
Sites that are not on the allowlist are refused outright rather than fumbled at.

The filler also refuses to touch a fixed list of fields regardless of settings —
date of birth, gender, race, disability, veteran status, government IDs, bank
details, CAPTCHAs, and consent/terms checkboxes. Those are yours to answer.
See `Backend/apps/automation/field_map.py`.

---

## Quick start

Two terminals for the app, a third if you want to run automation.

### 1. Backend

```bash
cd Backend
python -m venv venv
venv\Scripts\activate           # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

copy .env.example .env          # macOS/Linux: cp .env.example .env
python manage.py migrate
python manage.py seed_sites     # the automation allowlist
python manage.py seed_demo      # optional: demo account with sample data
python manage.py runserver
```

API on <http://127.0.0.1:8000>. Demo login: `demo@example.com` / `DemoPass123!`

### 2. Frontend

```bash
cd Frontend
npm install
npm run dev
```

App on <http://localhost:5173>. Vite proxies `/api` and `/media` to Django, so no
CORS configuration is needed in development.

### 3. Automation worker (only when you use assisted filling)

```bash
cd Backend
python -m playwright install chromium    # once
python manage.py run_automation_worker
```

The worker owns the browser. A run can sit open for minutes while you review a
filled form, which is not something a web request should be holding — so the API
only queues runs and the dashboard polls for progress.

---

## Switching to PostgreSQL

The project ships with `USE_SQLITE=True` so it boots before you configure anything.
For Postgres, create the database and flip the flag:

```bash
createdb job_dashboard
```

```ini
# Backend/.env
USE_SQLITE=False
DB_NAME=job_dashboard
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

Then `python manage.py migrate` again.

---

## Tests

```bash
cd Backend
python manage.py test --settings=config.test_settings
```

95 tests covering auth and per-user isolation, the job lifecycle and status
history, match scoring, resume default-promotion, application recording,
reminder scheduling, the analytics aggregations, and the automation safety gates.

The suite includes a real-browser integration test that drives the Playwright
filler against `Backend/tests/fixtures/sample_application_form.html` — a form
built to exercise every label-detection strategy and every sensitive field the
filler must refuse. It skips itself if Chromium is not installed.

Frontend lint:

```bash
cd Frontend && npm run lint
```

---

## Project layout

```
Backend/
  config/                   settings, root URLs, WSGI/ASGI
  apps/
    accounts/               custom email user, job-search profile, JWT, settings
    jobs/                   Job model, status history, filters, match scoring
    resumes/                uploads, one-default-per-user invariant
    applications/           application attempts, quick-apply
    reminders/              follow-ups and the auto-scheduling service
    automation/             allowlist, runs, field map, Playwright runner, worker
    analytics/              dashboard aggregations
    core.py                 per-user queryset scoping shared by every viewset
  tests/fixtures/           the HTML application form used by the integration test

Frontend/src/
  api/                      axios client with JWT refresh, endpoint wrappers
  context/                  auth and toast providers
  components/
    ui/                     buttons, cards, fields, modal, empty states
    charts/                 Recharts wrappers with a shared frame and tooltip
    jobs/ resumes/ …        feature components
  pages/                    the twelve routed pages
  lib/                      constants (incl. validated chart palettes), formatters
```

---

## Notes on a few design decisions

**Job vs Application.** A `Job` carries the lifecycle status; an `Application`
records each individual attempt — which resume went out, how it was filled, what
was answered. One job can have several attempts. This is what lets the tracker
stay honest about an automation-assisted form that was *prepared* but never sent.

**Statuses are ordinal, not categorical.** Saved → Applied → Shortlisted →
Interview → Selected is a sequence, so charts colour it with a single-hue
light-to-dark ramp rather than six unrelated hues, and the rows stay in lifecycle
order. Rejected leaves that sequence, so it takes the reserved critical red.
Every palette in `Frontend/src/lib/constants.js` was checked for lightness
monotonicity, step separation, colour-vision separation and contrast.

**Rates are measured against applications sent, not jobs tracked.** A hundred
saved jobs you never applied to should not dilute your interview rate.

**Match scores explain themselves.** Every point the scorer awards comes back as
a sentence, because a number with no reason is not advice. See
`Backend/apps/jobs/matching.py`.
