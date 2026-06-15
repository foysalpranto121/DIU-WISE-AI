import os
import sys
# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

print("Testing imports...")
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(backend_dir, ".env"))

print("Importing libraries...")
import torch
print(f"Torch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from openai import OpenAI

print("Testing OpenAI key...")
key = os.getenv("OPENAI_API_KEY")
if key:
    print(f"OpenAI key: {key[:15]}...{key[-15:]}")
    try:
        client = OpenAI(api_key=key)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        print("OpenAI key is VALID!")
        print(f"Response: {res.choices[0].message.content}")
    except Exception as e:
        print(f"OpenAI key is INVALID! Error: {e}")
else:
    print("No OpenAI key found!")
