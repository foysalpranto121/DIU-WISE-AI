import sys, os, time

LOG = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.log"), "w", buffering=1)

def p(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.write(line + "\n")
    LOG.flush()

p("Python OK")
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv()

# Pre-load numpy/sklearn BEFORE Flask to avoid Windows DLL scan deadlock
p("Pre-loading numpy + sklearn (may take 1-2 min on first run)...")
import numpy, joblib
from sklearn.ensemble import RandomForestClassifier
p("numpy/sklearn ready")

p("Importing factory (loads Flask + all AI models)...")
from factory import create_app

p("Creating app...")
app = create_app()

p(">>> Server ready! Open http://127.0.0.1:5000 <<<")
LOG.close()

app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
