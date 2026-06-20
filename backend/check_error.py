import sys, os, traceback
os.chdir(os.path.dirname(os.path.abspath(__file__)))

log = open("startup_error.log", "w", buffering=1)

def p(msg):
    print(msg, flush=True)
    log.write(msg + "\n")
    log.flush()

p("=== Startup Check ===")

try:
    p("Loading dotenv...")
    from dotenv import load_dotenv
    load_dotenv()
    p("OK")

    p("Loading BurnoutModel...")
    from ai_engine.burnout_model import BurnoutModel
    bm = BurnoutModel(model_dir="ai_engine/trained")
    bm.load_or_train()
    p("BurnoutModel OK")

    p("Loading DistressDetector...")
    from ai_engine.distress_detector import DistressDetector
    DistressDetector()
    p("DistressDetector OK")

    p("Loading EmotionClassifier...")
    from ai_engine.emotion_classifier import EmotionClassifier
    EmotionClassifier()
    p("EmotionClassifier OK")

    p("Loading RAGEngine...")
    from ai_engine.rag_engine import RAGEngine
    RAGEngine(knowledge_file="data/wellness_knowledge.txt", model_dir="ai_engine/trained")
    p("RAGEngine OK")

    p("=== ALL OK ===")

except Exception as e:
    p(f"FAILED: {e}")
    traceback.print_exc(file=log)
    traceback.print_exc()
    log.close()
    sys.exit(1)

log.close()
