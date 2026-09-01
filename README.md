# DIU WISE AI: Student Wellness & Success Platform

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0-green)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/openai-GPT--4o-orange)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DIU WISE AI** is an AI-powered mental wellness platform built for Daffodil International University (DIU) students. It combines machine learning-based burnout prediction, emotion analysis, and a bilingual (Bangla + English) AI chatbot to support student wellbeing.

---

## Features

### Bilingual AI Wellness Chatbot

An intelligent assistant powered by OpenAI GPT-4o with Retrieval-Augmented Generation (RAG). Responds fluently in **both Bangla and English** in the same reply. Students can ask in either language and receive context-aware wellness support.

### Burnout Prediction

A trained Random Forest model analyzes academic patterns (attendance, assignments, grades) and predicts burnout risk with a detailed risk score and actionable recommendations.

### Emotion & Mood Tracking

Real-time emotion classification from journal entries and self-reports. Visual mood history with trend analysis over time using Chart.js.

### Student Success Hub

- Academic metrics: GPA, credit load, submission status
- Wellbeing trends: mood history, stress indicators, sleep analysis
- Personal goals and achievement badges
- Profile picture upload and management

### Crisis Safety Net

When high distress is detected in a conversation, the platform surfaces verified Bangladesh emergency helplines, National Emergency (**999**), **Kaan Pete Roi** and **Moner Bondhu**, with an interactive breathing exercise overlay.

### Admin Dashboard

Monitor student wellbeing trends, flag at-risk students, and generate population-level reports.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.10+, Flask 3.0, SQLAlchemy |
| **AI / NLP** | OpenAI GPT-4o, LangChain |
| **ML Models** | Scikit-learn (Random Forest, KMeans), Joblib |
| **Frontend** | HTML5, CSS3 (Glassmorphism), Vanilla JavaScript, Chart.js |
| **Database** | PostgreSQL on Neon (SQLite fallback for local demo) |
| **Retrieval and emotion** | Keyword matching, no embedding model. See the memory budget note under Deployment for why |

---

## Project Structure

```text
DIU-WISE-AI/
├── backend/
│   ├── ai_engine/
│   │   ├── burnout_model.py        # Random Forest burnout predictor
│   │   ├── emotion_classifier.py   # Keyword based emotion classifier
│   │   ├── agent_router.py         # Keyword based intent router
│   │   ├── rag_engine.py           # Keyword retrieval + GPT-4o chatbot
│   │   └── trained/
│   │       └── burnout_model.joblib  # Trained burnout model
│   ├── data/
│   │   └── wellness_knowledge.txt  # RAG knowledge base
│   ├── models/                     # SQLAlchemy database models
│   ├── routes/                     # Flask blueprints (API + page routes)
│   ├── services/                   # Business logic and triage engine
│   ├── static/                     # CSS, JS, images
│   ├── templates/                  # Jinja2 HTML templates
│   ├── app.py                      # Flask entry point
│   ├── factory.py                  # App factory
│   ├── start.py                    # Startup script with logging
│   ├── START_SERVER.bat            # Windows one-click launcher
│   └── .env                        # Environment variables (not committed)
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- An [OpenAI API key](https://platform.openai.com/)

### 1. Clone the Repository

```bash
git clone https://github.com/foysalpranto121/DIU-WISE-AI.git
cd DIU-WISE-AI
```

### 2. Set Up the Virtual Environment

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file inside the `backend/` directory:

```env
# Neon Postgres. Omit to fall back to the local SQLite file (demo only).
DATABASE_URL=postgresql://USER:PASSWORD@ep-xxxx-pooler.REGION.aws.neon.tech/DBNAME?sslmode=require
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
MODEL_DIR=ai_engine/trained
KNOWLEDGE_FILE=data/wellness_knowledge.txt
```

See `backend/.env.example` for the full list with comments.

### 5. Create the Database Schema

The schema is managed by Alembic (Flask-Migrate). Run this once against a new
database, and again after pulling any new migration:

```bash
cd backend
flask --app manage db upgrade
```

The app no longer creates tables on startup, so this step is required before the
first run. Demo data is seeded automatically once the tables exist.

### 6. Start the Server

**Option A, Windows (recommended):** Double-click `backend/START_SERVER.bat`

**Option B, Command line:**

```bash
cd backend
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

> **First-run note:** The first startup trains the burnout model if `ai_engine/trained/burnout_model.joblib` is missing, which takes a few seconds. There is no embedding model to download any more, so startup is quick. Wait for `Running on http://0.0.0.0:5000` before opening the browser.

---

## Windows Performance Note

If the project is stored on a virtual or network-mapped drive (e.g., `M:\`), Windows Defender may scan Python DLL files on first load, causing a **2 to 5 minute startup delay**.

**To fix this permanently:**

1. Open **Windows Security** → **Virus & threat protection**
2. Go to **Manage settings** → **Exclusions** → **Add an exclusion**
3. Add your Python installation folder and the project directory (e.g., `M:\DIU-WISE-AI` and `M:\Miniconda`)

After adding exclusions, subsequent startups take under 30 seconds.

---

## Admin Account

There is no built in admin password. The app used to create
`admin@diu-wise.ai` with a fixed password on every boot, which meant every
deployment shipped with publicly known admin credentials.

To create the admin account, set `SEED_ADMIN=true` for exactly one start, then
set it back to `false`:

* If `SEED_ADMIN_PASSWORD` is set, that password is used.
* If it is empty, a random password is generated and written to the application
  log once. Copy it from the log, sign in, and change it.

Students register themselves at `/register`.

---

## Deployment (Render + Neon)

The app deploys as a **single** Render web service. Flask serves the Jinja
templates and the API routes from one process, so there is no separate frontend
to host anywhere else. The database is Neon Postgres, which lives outside
Render and is reached over the `DATABASE_URL` connection string.

`render.yaml` at the repo root is a Render Blueprint and holds the whole
service definition. Render does not read a Procfile, which is why this repo
does not have one.

### 1. Create the service

1. Push this branch to GitHub.
2. In the Render dashboard choose **New > Blueprint** and point it at this repo.
3. Render reads `render.yaml` and prompts for the secret values (see below).

### 2. Environment variables

Set these in Render's dashboard. Never commit them.

| Variable | Required | Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | Yes | Neon connection string. Both `postgres://` and `postgresql://` forms work; the app rewrites the scheme and adds `sslmode=require`. |
| `SECRET_KEY` | Yes | Long random string. The app refuses to start without it outside development. Generate with `python -c "import secrets; print(secrets.token_hex(32))"`. |
| `OPENAI_API_KEY` | Yes | Used by the chat and triage services. |
| `FLASK_ENV` | Yes | `production`. Anything other than `development` disables debug and turns on secure cookies. |
| `PYTHON_VERSION` | Yes | `3.10.11`. Render's current default is 3.14, which the pinned torch and faiss-cpu versions do not support. |
| `SEED_ADMIN` | No | `false`. Set to `true` for one deploy to create the admin account, then set it back. See "Admin Account" above. |
| `SEED_ADMIN_PASSWORD` | No | Password for that one time seed. Leave empty to have one generated and logged. |
| `CORS_ORIGINS` | No | Empty. Only set this if something genuinely needs cross-origin access. |
| `RATELIMIT_LOGIN` | No | Defaults to `10 per minute`. |
| `RATELIMIT_CHAT` | No | Defaults to `20 per minute`. |
| `RATELIMIT_PASSWORD_RESET` | No | Defaults to `5 per hour`. Each request can send a real email, so keep this tight. |
| `BREVO_API_KEY` | For reset email | API key from the Brevo dashboard (Settings, SMTP & API, API Keys). This is the API key, not the SMTP key. With it unset, reset emails are suppressed and a warning is logged; the endpoint still responds normally. |
| `BREVO_API_TIMEOUT` | No | Defaults to `10` seconds. Bounds every call to Brevo so a network fault fails fast. |
| `MAIL_DEFAULT_SENDER` | For reset email | Sender address, must be verified in Brevo. |
| `GOOGLE_CLIENT_ID` | For Google sign-in | OAuth client ID from Google Cloud Console. With it unset the Google button reports sign-in as not configured instead of erroring. |
| `GOOGLE_CLIENT_SECRET` | For Google sign-in | OAuth client secret. |

### Why email goes over HTTP, not SMTP

Reset email is sent through Brevo's HTTP API (`api.brevo.com`, port 443), not
their SMTP relay. Render's free instances block outbound traffic to SMTP ports
25, 465 and 587. A blocked port is blackholed rather than refused, so an SMTP
connect never returns and the request hangs until gunicorn kills the worker
after its timeout. Do not switch this back to SMTP on a free instance.

### Google OAuth redirect URIs

Register the app in Google Cloud Console (APIs & Services, Credentials, OAuth
client ID, type Web application) and add both callback URLs as authorized
redirect URIs:

* Local development: `http://127.0.0.1:5000/auth/google/callback`
* Render: `https://YOUR-APP.onrender.com/auth/google/callback`

Accounts created through Google sign-in have no local password
(`auth_provider` is `google`). They sign in only via Google unless they set a
password through the reset flow.
| `WEB_CONCURRENCY` | No | Defaults to `1`. See `backend/gunicorn.conf.py` for why more than one worker does not fit. |

`render.yaml` already declares the non secret values and marks the secrets
`sync: false`, so Render asks for them once at Blueprint creation.

### 3. Database migrations

Schema changes are Alembic migrations, and the app no longer creates tables on
startup. The migrations have to run against Neon before a new version serves
traffic.

Render's pre-deploy command would do this automatically, but it is a **paid
instance feature**, so `render.yaml` does not use one. Run the migration
yourself instead, once per schema change, from the `backend/` directory with
`DATABASE_URL` pointing at Neon:

```bash
flask --app manage db upgrade
```

Neon is reachable from anywhere, so running this locally has the same effect as
running it on the host.

### 4. Memory budget

`render.yaml` targets the **free** instance type, which has 512 MB of RAM. The
app fits, with room to spare. Measured on Python 3.10 with the pinned
dependency set, each layer in its own process:

| Stage | Resident memory |
| :--- | ---: |
| Interpreter only | 15 MB |
| plus Flask, SQLAlchemy, psycopg | 65 MB |
| plus numpy, scipy, scikit-learn | 154 MB |
| plus langchain, openai | 183 MB |
| App booted through `create_app()` | 214 MB |
| **Peak after serving chat, dashboard and emotion requests** | **234 MB** |

That leaves about 278 MB of headroom under the 512 MB cap.

Getting there required removing the local embedding stack. `torch`,
`transformers` and `sentence-transformers` were pulled in by
`EmotionClassifier` alone and cost 312 MB of resident memory, which put the app
at 543 MB, over the cap. `EmotionClassifier` now classifies by keyword instead.
That is less accurate than sentence embeddings on paraphrased text, and it is a
deliberate, accepted tradeoff. `RAGEngine` already made the same one.

Do not reintroduce those three packages without re-measuring, and do not switch
`render.yaml` to a paid plan.

One consequence remains: free instances spin down after 15 minutes of
inactivity, so the next request pays a cold start. There is no model download
in that path any more, so it is much shorter than it used to be.

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
These are the JSON endpoints. Page routes that render a template (`/`,
`/profile`, `/resources`, `/counselors`, `/mood-history`, `/voice-journal`,
`/stress-calendar`, `/pricing`, `/landing`, `/admin`) are not listed.

### Wellbeing

| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/chat` | None | Send a message to the AI wellness chatbot. Rate limited. |
| `POST` | `/predict` | Login | Burnout prediction, forecast, distress and triage for a metrics payload |
| `POST` | `/emotion` | Login | Classify the emotion of a piece of text |
| `POST` | `/generate-plan` | Login | Generate a personalised wellbeing plan |
| `GET` | `/crisis-resources` | None | Verified Bangladesh crisis helplines |
| `GET` | `/dashboard-data` | Admin | Population level wellbeing data and the at-risk watchlist |
| `GET` | `/health` | None | Liveness check |

### Accounts

| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/login` | None | Sign in. Rate limited. |
| `POST` | `/register` | None | Create a student account |
| `POST` | `/logout` | Login | Sign out |
| `GET` | `/me` | None | Current session user, or `authenticated: false` |
| `POST` | `/account/password` | Login | Change password |
| `POST` | `/profile/update` | Login | Update profile and academic fields |
| `POST` | `/profile/upload-avatar` | Login | Upload a profile picture |
| `GET` `POST` | `/admin/users` | Admin | List or create users |
| `PATCH` | `/admin/users/<id>` | Admin | Update a user's name, role or active flag |

### Voice journal

| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/voice-journal/transcribe` | Login | Transcribe recorded audio |
| `POST` | `/voice-journal/save` | Login | Save an entry with its detected emotion |
| `GET` | `/voice-journal/entries` | Login | List entries |
| `DELETE` | `/voice-journal/entries/<id>` | Login | Delete an entry |
| `POST` | `/voice-assistant/chat` | Login | Voice assistant conversation turn |
| `POST` | `/voice-assistant/speak` | Login | Text to speech for a reply |

### Calendar and subscription

| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` `POST` | `/api/events` | Login | List or add an academic event |
| `DELETE` | `/api/events/<id>` | Login | Delete an academic event |
| `GET` | `/api/stress-forecast` | Login | Stress forecast derived from upcoming events |
| `GET` | `/api/subscription/status` | Login | Current plan and status |
| `POST` | `/api/subscription/upgrade` | Login | Change plan |
| `POST` | `/appointments/create` | Login | Book a counsellor appointment |

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License, see the [LICENSE](LICENSE) file for details.

---

Developed for the DIU Student Community, Daffodil International University, Dhaka, Bangladesh
