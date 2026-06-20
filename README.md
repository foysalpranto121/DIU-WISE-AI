# DIU WISE AI — Student Wellness & Success Platform

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.0-green)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/openai-GPT--4o-orange)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**DIU WISE AI** is an AI-powered mental wellness platform built for Daffodil International University (DIU) students. It combines machine learning-based burnout prediction, emotion analysis, and a bilingual (Bangla + English) AI chatbot to support student wellbeing.

---

## Features

### Bilingual AI Wellness Chatbot

An intelligent assistant powered by OpenAI GPT-4o with Retrieval-Augmented Generation (RAG). Responds fluently in **both Bangla and English** in the same reply — students can ask in either language and receive context-aware wellness support.

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

When high distress is detected in a conversation, the platform surfaces verified Bangladesh emergency helplines — National Emergency (**999**), **Kaan Pete Roi**, **Moner Bondhu** — with an interactive breathing exercise overlay.

### Admin Dashboard

Monitor student wellbeing trends, flag at-risk students, and generate population-level reports.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.10+, Flask 3.0, SQLAlchemy |
| **AI / NLP** | OpenAI GPT-4o, LangChain, FAISS, Sentence-Transformers |
| **ML Models** | Scikit-learn (Random Forest), Joblib |
| **Frontend** | HTML5, CSS3 (Glassmorphism), Vanilla JavaScript, Chart.js |
| **Database** | SQLite (development), PostgreSQL (production ready) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |

---

## Project Structure

```text
DIU-WISE-AI/
├── backend/
│   ├── ai_engine/
│   │   ├── burnout_model.py        # Random Forest burnout predictor
│   │   ├── emotion_model.py        # Emotion classifier
│   │   ├── rag_engine.py           # LangChain + FAISS RAG + GPT-4o chatbot
│   │   └── trained/
│   │       ├── faiss_index/        # Vector store for wellness knowledge
│   │       └── *.pkl               # Trained model files
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
DATABASE_URL=sqlite:///diu_wise.db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
MODEL_DIR=ai_engine/trained
KNOWLEDGE_FILE=data/wellness_knowledge.txt
HF_HUB_OFFLINE=0
TRANSFORMERS_OFFLINE=0
```

### 5. Start the Server

**Option A — Windows (recommended):** Double-click `backend/START_SERVER.bat`

**Option B — Command line:**

```bash
cd backend
python app.py
```

Open your browser at: **http://127.0.0.1:5000**

> **First-run note:** On the very first startup, AI models (sentence-transformers, FAISS index, sklearn) need to load. This can take **2–10 minutes** depending on your machine. Do not close the terminal — wait for `Running on http://0.0.0.0:5000` to appear before opening the browser.

---

## Windows Performance Note

If the project is stored on a virtual or network-mapped drive (e.g., `M:\`), Windows Defender may scan Python DLL files on first load, causing a **2–5 minute startup delay**.

**To fix this permanently:**

1. Open **Windows Security** → **Virus & threat protection**
2. Go to **Manage settings** → **Exclusions** → **Add an exclusion**
3. Add your Python installation folder and the project directory (e.g., `M:\DIU-WISE-AI` and `M:\Miniconda`)

After adding exclusions, subsequent startups take under 30 seconds.

---

## Default Credentials

After the database is seeded on first run:

| Role | Email | Password |
| :--- | :--- | :--- |
| Admin | `admin@diu.edu.bd` | `admin123` |
| Student | Register via `/register` | — |

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/chat` | Send message to AI wellness chatbot |
| `POST` | `/api/predict-burnout` | Get burnout risk prediction |
| `GET` | `/api/mood-history` | Retrieve mood trend data |
| `POST` | `/api/log-mood` | Log a new mood entry |
| `GET` | `/api/dashboard` | Get student dashboard data |

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

Developed for the DIU Student Community — Daffodil International University, Dhaka, Bangladesh
