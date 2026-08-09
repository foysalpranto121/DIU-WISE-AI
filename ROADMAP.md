# ROADMAP.md: DIU WISE AI Database, Backend Fixes & Deployment

Read `AGENT.md` first, it defines what is and is not in scope. This file is the phase-by-phase
build plan. Run each phase as a separate Claude Code session/prompt, in order. Do not start a phase
until the previous one is reviewed.

## Phase 1: Database, Move to PostgreSQL on Neon

**Goal:** the app runs on a real Neon Postgres database, with proper versioned migrations from now
on, and the schema gap that breaks burnout prediction is closed.

### Tasks
1. Create a Neon project and database (guide the user through this if credentials aren't provided;
   otherwise use the connection string given).
2. Add `flask-migrate` to `requirements.txt` and wire it into `factory.py` / a new `manage.py` (or
   equivalent) alongside the existing `ServiceRegistry` pattern, don't replace the existing
   bootstrapping, extend it.
3. Initialize Alembic migrations (`flask db init`) and generate an initial migration that reflects
   the *current* schema (`User`, `StudentMetric`, `Appointment`, `VoiceJournal`, `AcademicEvent`,
   `Subscription`) exactly as it exists today, this becomes migration 0001, the baseline.
4. Add a second migration that extends `StudentMetric` with the 6 missing wellness fields the
   burnout model expects: `sleep_quality`, `screen_time`, `social_interaction`, `break_frequency`,
   `mood_score`, `stress_level`. Match types/nullability to how `ai_engine/burnout_model.py`
   consumes them, check the model code, don't guess.
5. Retire `migrate_db.py` and `migrate_subscription.py` (the raw sqlite3 scripts), replace what
   they did with proper Alembic migrations, then delete or clearly mark the old scripts as
   deprecated (don't leave dead, misleading scripts in the repo).
6. Update `config.py` if needed so `DATABASE_URL` cleanly supports Neon's connection string format
   (Neon requires `sslmode=require`, verify this is handled).
7. Update `.env.example` to include `DATABASE_URL` (Neon), `SECRET_KEY`, and `OPENAI_API_KEY` with
   clear placeholder comments, currently `.env.example` is missing `SECRET_KEY` and
   `DATABASE_URL` entirely.
8. Port the existing demo/seed data (`data_service.seed_if_empty()`) so it runs cleanly against
   Postgres and populates the new wellness fields with realistic demo values (not just defaults),
   the live Neon DB should start seeded, per the team's decision in AGENT.md.
9. Verify locally: point `DATABASE_URL` at the real Neon instance, run migrations, boot the app,
   confirm no errors, confirm seed data lands correctly with all 11 burnout-model fields populated.

### Explicitly not in this phase
- Don't fix the crisis-number bug or any other non-DB backend bug yet, that's Phase 2.
- Don't touch deployment config, that's Phase 3.

### Done when
- App boots against Neon with `flask db upgrade` as the only migration step needed
- `StudentMetric` has all 11 fields the burnout model reads
- Old raw sqlite migration scripts are gone or clearly deprecated
- `.env.example` is accurate and complete

## Phase 2: Backend bug fixes (safety, security, data integrity)

**Goal:** fix every backend-only bug identified in the QA review, without touching a single
template or static file.

### Tasks, in priority order
1. **Crisis numbers (safety-critical).** In `services/triage_service.py` and
   `data/wellness_knowledge.txt`, replace all US crisis numbers/references (988, 911, 741741) with
   the correct Bangladesh ones already used correctly in `routes/chat_routes.py` (999, Kaan Pete
   Roi, Moner Bondhu). Check both files fully, grep for "988", "911", "741741" repo-wide (excluding
   `.venv`) to make sure nothing is missed.
2. **Burnout model now has real data (depends on Phase 1).** Confirm `ai_engine/burnout_model.py`
   correctly reads the 6 new `StudentMetric` fields instead of falling back to hardcoded defaults.
   If the model's default-substitution logic is still silently active, fix it so it uses real
   column data.
3. **Default admin credentials.** In `factory.py`, stop seeding the fixed
   `admin@diu-wise.ai` / `Admin@12345` account in a way that's usable in production. Either:
   generate a random password on first boot and log it once (never store in plaintext, never
   print on the login page, that part is frontend and out of scope, but the backend seeding
   logic itself is fair game), or gate the seed behind an explicit `SEED_ADMIN=true` env var so it
   never silently runs in production. Pick whichever fits the existing pattern with the least
   risk, and explain the choice in your summary.
4. **SECRET_KEY.** Remove the `"change-this-in-production"` default in `config.py`. Make the app
   fail loudly at startup if `SECRET_KEY` isn't set via environment variable, rather than silently
   using a guessable default.
5. **Debug mode / host binding.** Ensure debug mode is `False` and the interactive Werkzeug
   debugger is disabled for anything other than local development (gate by `FLASK_ENV` or
   equivalent env var, not hardcoded).
6. **Admin-only routes.** Check `dashboard_routes.py` (`/dashboard-data`) and any other route that
   exposes the at-risk student watchlist, confirm it's guarded by an admin/counselor role check,
   not just `@login_required`. Add the role check if missing.
7. **Rate limiting.** Add basic rate limiting (e.g. `Flask-Limiter`) to `/chat` and `/login` to
   prevent brute-force login attempts and unrestrained OpenAI API cost abuse. This is a new
   dependency but it's backend-only, so it's in scope.
8. **CORS.** Review `extensions.py`, if CORS is wide open with no origin restriction, lock it down
   to the actual deployed frontend origin (set via env var so it can differ between local/prod).
9. **CSRF, partial mitigation only.** Full CSRF protection is decided out of scope (see AGENT.md)
   because a real token requires either a hidden form field or a JS header, both of which mean
   editing templates or static JS. Instead: verify `SESSION_COOKIE_SAMESITE` is set, and tighten it
   from `"Lax"` to `"Strict"` on any cookie where that won't break normal top-level navigation
   (test that login redirects still work after the change). Log full CSRF token protection as a
   "needs frontend owner" item in the phase summary, don't attempt it.
10. **Unhandled type casts.** In `routes/user_routes.py`, wrap the `float()`/`int()` casts on
    `current_gpa`, `credit_load`, `goal_*` in proper error handling so a bad POST returns a clean
    400 instead of a 500.
11. **Deprecated SQLAlchemy API.** Replace `User.query.get(...)` (legacy SQLAlchemy 2.x pattern) in
    `factory.py` with `db.session.get(User, ...)`.
12. **requirements.txt version pins.** Pin versions for the LangChain stack in particular
    (`langchain`, `langchain-community`, `sentence-transformers`, `faiss-cpu`) since these have had
    breaking API changes (e.g. `HuggingFaceEmbeddings` import path, `FAISS.load_local` signature).
    Test that the app still boots after pinning.
13. **FAISS index.** Either make sure both `index.faiss` and `index.pkl` are committed/generated so
    the retriever loads instead of rebuilding from scratch every boot, or remove the partial
    `index.faiss` file entirely if it's not going to be completed this phase, don't leave a
    partial, unused file in the repo silently.

### Explicitly not in this phase
- Anything requiring a template or JS change (e.g. the `#emotion-result` / `#emotion-result-container`
  ID mismatch, `app.js` binding to nonexistent elements, `admin.js` reading `High/Medium/Low` instead
  of `Doing Well/Balanced/Needs Support`), **flag these clearly in your summary as "needs frontend
  owner," do not fix them.**

### Done when
- Every item above is either fixed and verified, or explicitly logged as skipped with a one-line
  reason
- `python -m py_compile` still passes on everything
- The app still boots locally against Neon with no new errors

## Phase 3: Prepare for deployment, Render preferred

**Goal:** the repo is fully ready to deploy, ideally on Render, connected to the Neon database,
with secrets documented. This is a single-deployment app: Flask serves both the templates and the
API from one process. Do not split this into separate backend and frontend hosts, see AGENT.md's
"Deployment topology" note for why.

**Important boundary:** whichever host is used, deploying live requires a push to GitHub and
connecting that host's dashboard to the repo, both of which are manual steps the user does
themselves (see AGENT.md's working agreement, Claude Code never pushes). This phase's job is to
make the repo deployment-ready locally, not to make it live. Steps 6 and 7 below happen after the
user has pushed and connected the host, so verify what you can locally and clearly hand off the
rest.

**Hard budget constraint: free tier only.** The team cannot pay for Render's Standard tier. The app
must fit inside the free instance type's 512 MB memory limit. If it genuinely cannot, after trying
the size-reduction steps in task 4a below, stop and report that clearly rather than defaulting to a
paid plan in `render.yaml`.

### Tasks
1. Add `gunicorn` to `requirements.txt` (Flask's dev server should never run in production).
2. Add a `Procfile` (or `render.yaml`, whichever fits Render's current recommended setup, check
   current Render docs since this may have changed) with the correct start command pointing at
   `factory.create_app()`. Set the plan to the free instance type, not Standard.
3. Add a minimal `wsgi.py` entry point if Render's Python setup expects one.
4. Confirm build steps: Render needs to install `requirements.txt` cleanly, including the heavier
   ML dependencies (`sentence-transformers`, `faiss-cpu`, `transformers`, `torch` if pulled in
   transitively). Measure the actual installed footprint of these dependencies.
4a. Already measured: the app's real resident memory is 542.7 MB against Render free's 512 MB
    cap, over by roughly 31 MB. CPU-only torch was already in effect locally (torch 2.13.0+cpu)
    and does not change RAM usage, only download size, so it does not close the gap on its own.
    The OpenAI embeddings fallback is ruled out: the API key belongs to the team's teammate, who
    has very limited credit remaining, so no feature change may add API calls to that key. Do not
    attempt this option, do not ask for a re-check on it.
4b. Decided path: replace `EmotionClassifier`'s ML stack (`torch`, `transformers`,
    `sentence-transformers`, the loaded MiniLM model) with a keyword or lexicon-based
    implementation for emotion classification. This removes roughly 312 MB (the largest chunk of
    the app's footprint) and brings the app to an estimated 240 to 260 MB, comfortably inside the
    512 MB cap. This mirrors a tradeoff already present in this codebase: `RAGEngine` already
    skips its embedding model for the same memory reason and falls back to keyword-based
    retrieval, so this is consistent with an existing pattern, not a new one. Accuracy on
    `/emotion` and voice journal analysis will be lower than the sentence-embedding version, this
    is a known and accepted tradeoff, not a bug to fix later. Implement it, re-measure RSS to
    confirm it fits, and report the real numbers in the phase summary, the same way the first
    measurement was reported. Remove `torch`, `transformers`, and `sentence-transformers` from
    `requirements.txt` once nothing else in the app depends on them, verify nothing else does
    before removing (check the RAG engine and burnout model don't import them).
4c. Do not implement Cloud Run, or any other alternate host, this phase. Render free tier now fits
    once 4b is done. Keep the researched host comparison in the phase summary for reference, but
    it is not being acted on.
5. Write a clear list (in the phase summary and in `README.md`) of every environment variable
   Render needs set in its dashboard: `DATABASE_URL` (Neon connection string), `SECRET_KEY`,
   `OPENAI_API_KEY`, `FLASK_ENV=production`, and any others introduced in Phase 2 (e.g.
   `SEED_ADMIN`). Never commit these anywhere.
6. Document the migration step for the live database: running the Phase 1 Alembic migrations
   against the live Neon database, either as a Render "release phase" command or a documented
   manual one-time step, pick whichever Render supports cleanly, and write down exactly what the
   user needs to run or configure. This is documentation for the user to execute after they push,
   not something Claude Code runs against the live service.
7. Once the user confirms they've pushed and connected Render (a separate follow-up message from
   them, not part of this phase), you may help verify the deployed app boots, `/health` returns
   200, login works, and the AI engine initializes without crashing, but only after they confirm
   the push happened.
8. Update `README.md`'s deployment section (if it has one) to reflect reality, Render + Neon, not
   the old local-only instructions, since inaccurate deployment docs are themselves a form of the
   "broken promise" problem flagged in the QA report.

### Done when
- `Procfile`, `wsgi.py`, and `gunicorn` are in place and correct, targeting Render
- `EmotionClassifier` runs on keyword/lexicon logic, not the `torch`/`transformers`/
  `sentence-transformers` stack, and `requirements.txt` no longer lists those three
- Measured RSS after the change is written down in the phase summary and confirmed under 512 MB
- Config targets a free instance type, `plan: free`, not paid
- The env var list needed for Render is written down clearly in the summary and in `README.md`
- The migration step for the live database is documented, not run
- Everything above is committed locally on a feature branch, nothing pushed
- The phase summary states: "ready for you to push and connect Render, here's exactly what to do
  next"

## Phase 4: Frontend bug fixes (logic only, no visual changes)

**Scope change from the team, read carefully.** The frontend owner has now authorized fixing the
specific bugs listed below, and only these. This does not reopen frontend work generally. Do not
touch CSS, layout, colors, copy, or add anything new. Every change in this phase should be the
smallest possible edit that makes broken wiring work, not a rewrite or an improvement.

**Goal:** fix the exact bugs logged as "needs frontend owner" during Phases 1 to 3, without
changing how anything looks.

### Tasks
1. **`admin.js` label mismatch.** Lines 41, 114, and 208 read `burnout_summary['High']`,
   `['Medium']`, `['Low']`. The backend sends `'Doing Well'`, `'Balanced'`, `'Needs Support'`.
   Update the three label strings in `admin.js` to match what the backend actually sends. Do not
   change the backend response shape, and do not touch how the chart or counts are styled, only the
   key names being read.
2. **Unbound element IDs.** `chat.js` references `attendance`, `delay`, `grades`, none of which
   exist in any template. `app.js` references `new-password`, `old-password`, `password-message`,
   `password-save`, meaning the password-change UI does nothing right now. `dashboard.js`
   references `wellbeing-plan-container`, also missing. For each: check whether the matching HTML
   element already exists under a different ID (fix the ID mismatch if so) or is genuinely missing
   (add the minimal element needed for the JS to bind to it, matching the existing visual style
   exactly, do not redesign it). If it's unclear whether a feature was intentionally removed versus
   left half-built, flag it in the summary instead of guessing.
3. **Profile update errors render as raw JSON.** `profile.html` doesn't render flashed messages,
   so a failed profile update (e.g. bad GPA) shows raw JSON text instead of a message. Add the
   minimal flashed-message rendering block needed, styled to match the page's existing error/alert
   patterns already used elsewhere in the app, don't invent a new visual style for it.
4. **Do not touch, still frontend owner's call:** full CSRF token protection (needs a hidden field
   or JS header, a bigger decision than a bug fix) and the fake README API reference table (already
   flagged separately, not a frontend code bug).

### Done when
- All three bugs above are fixed and manually verified to work (admin dashboard chart shows real
  counts, password change UI actually submits, profile errors render as a message not raw JSON)
- No CSS file changed, no layout/color/copy changed anywhere
- `python -m py_compile` still passes, and nothing else in the app broke
- Local commits only on a new branch (e.g. `feature/frontend-bug-fixes`), nothing pushed
- Phase summary lists exactly what was changed per bug, one paragraph each

## After Phase 4

Claude Code never pushes anything (see AGENT.md's working agreement), all branches and commits
stay local. Once you've manually tested and reviewed the work yourself, push the branch(es) and
open the PR(s) against `github.com/foysalpranto121/DIU-WISE-AI` yourself, summarizing what changed,
what was intentionally left alone (with reasons), and the full list of frontend-dependent bugs that
still need the other teammate's attention.