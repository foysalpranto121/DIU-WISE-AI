# Run DIU WISE AI Locally

## Prerequisites
- Python 3.11+ installed
- pip package manager

## Setup & Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Environment Variables
Create `.env` file in project root:
```
FLASK_ENV=development
FLASK_DEBUG=true
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the Application

**Option A: Run with wsgi.py (Recommended)**
```bash
python wsgi.py
```

**Option B: Run Flask directly**
```bash
cd backend
flask run
```

### 4. Access in Browser
```
http://localhost:5000
```

## Features Available Locally
- ✅ Full voice assistant interface
- ✅ Microphone recording
- ✅ Real-time text input
- ✅ Bilingual support (Bengali & English)
- ✅ AI-powered responses
- ✅ Conversation history

## Troubleshooting

**Module not found error?**
```bash
pip install -r requirements.txt
```

**Port already in use?**
```bash
python wsgi.py --port 8000
```
Then visit: http://localhost:8000

**Microphone not working?**
- Check browser permissions
- Use HTTPS for production (localhost works)
- Ensure microphone is connected

## Stop the Server
Press `Ctrl + C` in terminal
