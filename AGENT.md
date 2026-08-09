# AGENT.md — DIU WISE AI: Database, Backend Fixes & Deployment

## Role

You are working as a **backend/infrastructure contributor** on an existing project, not the lead
developer. Another teammate owns the Flask backend logic and the entire frontend. Your access is a
**collaborator invite on their GitHub repo**. Your mandate from the team is narrow and explicit —
do not exceed it.

## Scope — read this before touching anything

**You ARE allowed to:**
- Migrate the database from SQLite to PostgreSQL (hosted on Neon)
- Set up a proper migration system (Alembic / Flask-Migrate) going forward
- Fix backend-only bugs: Python files in `backend/`, config, environment variables, security
  settings, database models, and data files (e.g. `data/wellness_knowledge.txt`)
- Deploy the app live on Render
- Add deployment config files (`Procfile`, `render.yaml`, `wsgi.py`, etc.)
- Update `requirements.txt`, `.env.example`, and `README.md` where accuracy requires it
- Tighten `SESSION_COOKIE_SAMESITE` (e.g. to `"Strict"` where it won't break normal navigation) as
  a backend-only, partial CSRF mitigation — see "CSRF protection" note below for why this is a
  partial fix, not full protection

**You are NOT allowed to:**
- Edit anything in `backend/templates/` (Jinja/HTML)
- Edit anything in `backend/static/` (CSS, JS, images) — this includes `app.js`, `admin.js`,
  `chat.js`, `crisis.js`, and all stylesheets
- Change any UI copy, layout, colors, or visual behavior
- Add new user-facing features
- Rename, remove, or restructure routes in a way that changes frontend contracts (i.e. URLs,
  JSON response shapes, and form field names consumed by existing JS/templates must stay identical
  unless a fix strictly requires it — see "Frontend contract safety" below)

If a bug genuinely cannot be fixed without touching a template or JS file, **stop and flag it** in
your output instead of fixing it. Do not make an exception.

### Frontend contract safety
Some backend responses are read by frontend JS (e.g. `burnout_summary` keys, `#emotion-result`
element IDs referenced from server-rendered templates). Before changing any route's response shape,
grep the `templates/` and `static/` directories for every place that consumes it. If a fix would
require changing the frontend to keep working, do not make that fix — log it as an "out of scope,
needs frontend owner" item instead.

### CSRF protection — decided out of scope for real implementation
Real CSRF protection requires the browser to send a token back on every POST — that token has to
come from either a hidden form field or a JS-attached header, both of which mean editing templates
or static JS. There is no way to add functioning CSRF protection without a frontend change; turning
it on with zero frontend changes would just reject every existing form submission with a 400 error,
which is a worse outcome than leaving it alone. Do not attempt full CSRF protection. The only
backend-only mitigation in scope is verifying/tightening `SESSION_COOKIE_SAMESITE`. Log full CSRF
as a "needs frontend owner" item — it's a small ask (one hidden input, one JS header line) for
whoever owns the frontend.

### Deployment topology — single deployment, decided
This is a Flask monolith: Jinja templates are rendered server-side by the same app that serves the
API routes. There is no separate frontend build to deploy elsewhere. Splitting backend (Render) and
frontend (Vercel) was considered and rejected — it would require rewriting every template into a
JSON API and building a real separate frontend app, which is an architecture change and out of
scope. Vercel is also not suited to a long-running Python process with heavy ML dependencies
(transformers, faiss-cpu). Deploy the whole app as one unit on Render. Do not propose or set up a
split deployment.

---

## Project context

DIU WISE AI is a Flask-based student mental wellness platform (repo:
`github.com/foysalpranto121/DIU-WISE-AI`). It has grown since initial development to include voice
journaling, appointments, subscriptions, academic events, and faculty advisor alerts, alongside its
original burnout-prediction and AI chat features.

Current state (confirmed by static review):
- `config.py` already reads `DATABASE_URL` from env with a SQLite fallback — Postgres support is
  partially wired in already.
- `requirements.txt` already includes `psycopg[binary]`.
- `migrate_db.py` and `migrate_subscription.py` are raw `sqlite3` scripts hardcoded to a local
  `.db` file path — **these will fail entirely against Postgres** and are not real migrations.
- There is no `Procfile`, no `wsgi.py`, and no `gunicorn` in requirements — **the app cannot be
  deployed to Render as-is**; it currently only runs via `start.py` with Flask's dev server.
- `factory.py` runs `db.create_all()` and seeds a default admin (`admin@diu-wise.ai` /
  `Admin@12345`) on every boot — this credential is also printed in `login.html` (frontend, do not
  touch) but the seeding logic itself is backend and in scope.
- `models/student_metrics.py` (`StudentMetric`) only has 5 fields (attendance_rate,
  submission_delay, grades, activity_score, engagement_decline). The burnout model
  (`ai_engine/burnout_model.py`) was expanded to expect 11 features including sleep_quality,
  screen_time, social_interaction, break_frequency, mood_score, and stress_level — these 6 fields
  don't exist on the model, so predictions default to constants and every student is scored
  "Balanced." This is a schema gap, which makes it a database task.
- `services/triage_service.py` and `data/wellness_knowledge.txt` reference US crisis numbers
  (988, 911, 741741) instead of the correct Bangladesh numbers (999, Kaan Pete Roi, Moner Bondhu)
  already used correctly elsewhere in the app (`routes/chat_routes.py`). This is a safety-critical,
  backend-only, plain-text fix — explicitly in scope per team decision.
- `config.py` SECRET_KEY defaults to the literal string `"change-this-in-production"` if the env
  var is unset.
- The app runs with Flask debug mode enabled in places and binds to `0.0.0.0` — needs to be
  disabled for the live deployment.

## Tech decisions (already made — do not re-litigate)

| Decision | Choice |
|---|---|
| Database | PostgreSQL, hosted on **Neon** |
| Migration tool | **Flask-Migrate (Alembic)** — versioned, repeatable migrations from now on |
| Hosting | **Render** |
| Seed data | Live Neon database starts **seeded with demo/test data** (same shape as current SQLite demo seed), understood to be wiped/reset later once real users onboard |
| Backend bug fixes | **All backend-only bugs** found in QA review are in scope, not just the crisis-number one |
| Frontend | **Untouched.** Zero changes to templates/static, no exceptions |

## Definition of Done (applies to every phase)

- [ ] App boots locally against a Postgres connection string with zero code errors
- [ ] `python -m py_compile` passes on every changed file
- [ ] Every existing route still returns the same JSON shape / same template it did before (grep
      verified against templates/static consumers)
- [ ] No `.venv`, `.env`, secrets, or `instance/` database files are ever committed
- [ ] Every phase ends with a short written summary: what changed, what was explicitly left alone
      and why, and any item that needed a frontend change and was therefore skipped
- [ ] Real secrets (Neon connection string, SECRET_KEY, OPENAI_API_KEY) live only in Render's
      environment variable settings and in a local untracked `.env` — never in code, never in git
      history
- [ ] Nothing has been pushed to `origin` or any remote — all work stays local on a feature branch
      until the user reviews and pushes it themselves

## Style / conventions to follow

- Match the existing code style already in the repo (Flask blueprint + `ServiceRegistry` DI pattern
  in `factory.py` — don't introduce a different architecture)
- Keep migrations small and reversible; one logical schema change per migration file
- Comment any bug fix with a one-line `# FIX:` explaining what was wrong, so the other teammate can
  review it fast in a PR
- No em dashes or horizontal divider lines (`---` as visual dividers) in code comments, commit
  messages, or generated docs — plain punctuation only

## Working agreement

- This is a **collaborator** relationship on someone else's repo — every phase's work should be
  small enough to review in one sitting.
- Work locally on a feature branch (create one per phase, e.g. `feature/postgres-migration`). Local
  commits on that branch are fine and encouraged, as checkpoints.
- **Never run `git push`, under any circumstances, even if asked to "finish up" or "wrap this
  phase."** Do not push to `origin`, do not open a pull request, do not push any branch — local or
  otherwise. Pushing and PR creation are done manually by the user only, after they've tested and
  reviewed the changes themselves.
- End every phase by telling the user exactly what branch the work is on and what changed, so they
  can review and push it themselves.
- See `ROADMAP.md` for the 3-phase breakdown and what to build in each session with Claude Code.
