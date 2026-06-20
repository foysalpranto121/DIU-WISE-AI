import sys, os, traceback
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Step 1: Testing RAGEngine instantiation...")
try:
    from ai_engine.rag_engine import RAGEngine
    rag = RAGEngine(knowledge_file="data/wellness_knowledge.txt", model_dir="ai_engine/trained")
    print("  RAGEngine OK")
except Exception as e:
    print(f"  RAGEngine FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Step 2: Testing factory import...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    from factory import create_app
    print("  factory import OK")
except Exception as e:
    print(f"  factory import FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Step 3: Creating app...")
try:
    app = create_app()
    print("  create_app() OK")
except Exception as e:
    print(f"  create_app() FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

print("All OK! Server should start fine.")
