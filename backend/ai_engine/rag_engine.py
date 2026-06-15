import os

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


class RAGEngine:
    def __init__(self, knowledge_file: str, model_dir: str):
        self.knowledge_file = knowledge_file
        self.vector_path = os.path.join(model_dir, "faiss_index")
        os.makedirs(model_dir, exist_ok=True)
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.retriever = self._build_retriever()
        self.prompt = PromptTemplate(
            input_variables=["context", "history", "question"],
            template=(
                "You are DIU WISE wellness assistant. Use only the provided context and history to answer.\n"
                "Give supportive, practical, non-clinical advice. If severe risk appears,"
                " recommend contacting counselor immediately.\n\n"
                "Context:\n{context}\n\n"
                "Chat History:\n{history}\n\n"
                "Question: {question}\nAnswer:"
            ),
        )
        self.tokenizer, self.model = self._load_generator()

    def _load_documents(self):
        with open(self.knowledge_file, "r", encoding="utf-8") as fp:
            chunks = [line.strip() for line in fp.readlines() if line.strip()]
        return [Document(page_content=chunk) for chunk in chunks]

    def _build_retriever(self):
        pkl_path = os.path.join(self.vector_path, "index.pkl")
        faiss_path = os.path.join(self.vector_path, "index.faiss")
        if os.path.exists(self.vector_path) and os.path.exists(pkl_path) and os.path.exists(faiss_path):
            store = FAISS.load_local(
                self.vector_path,
                self.embedding_model,
                allow_dangerous_deserialization=True,
            )
            return store.as_retriever(search_kwargs={"k": 4})
        docs = self._load_documents()
        store = FAISS.from_documents(docs, self.embedding_model)
        store.save_local(self.vector_path)
        return store.as_retriever(search_kwargs={"k": 4})

    def _load_generator(self):
        try:
            tok = AutoTokenizer.from_pretrained("google/flan-t5-small")
            mdl = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")
            return tok, mdl
        except Exception:
            return None, None

    def answer(self, message: str, anonymous: bool = False, history: list = None, intent: str = "general", urgency: str = "low", context_data: dict = None):
        if history is None:
            history = []
        if context_data is None:
            context_data = {}
        
        # Format history string
        history_str = "\n".join([f"User: {msg.get('user', '')}\nAI: {msg.get('ai', '')}" for msg in history[-5:]]) # Keep last 5 turns
        
        docs = self.retriever.invoke(message)
        context = "\n".join(d.page_content for d in docs[:4])
        
        # Try OpenAI First
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            try:
                import json
                from openai import OpenAI
                client = OpenAI(api_key=key)
                
                # Upgraded System Prompt for JSON Structure
                sys_prompt = (
                    "You are the DIU WISE AI, an expert academic and wellness assistant for university students. "
                    "Your goal is to provide highly specific, concrete, and actionable answers. "
                    "You MUST always respond with a valid JSON object matching this exact schema:\n"
                    "{\n"
                    '  "summary": "Short 1 sentence summary of your advice",\n'
                    '  "advice": ["Actionable step 1", "Actionable step 2", ...],\n'
                    '  "action_required": "Main takeaway or action",\n'
                    '  "risk_level": "low" | "medium" | "high",\n'
                    '  "follow_up_questions": ["Question 1?", "Question 2?"]\n'
                    "}\n"
                    f"Use this retrieved knowledge context if relevant: {context}\n"
                    f"Student Context Data: {json.dumps(context_data)}\n"
                    f"Intent: {intent}, Urgency: {urgency}"
                )
                
                response_obj = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={ "type": "json_object" },
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": f"History:\n{history_str}\n\nCurrent Question: {message}"}
                    ],
                    max_tokens=600,
                    temperature=0.4
                )
                response_text = response_obj.choices[0].message.content.strip()
                parsed_response = json.loads(response_text)
                
                return {
                    "anonymous": bool(anonymous),
                    "structured_response": parsed_response,
                    "sources": [d.page_content for d in docs[:3]],
                }
            except Exception as e:
                print(f"RAG OpenAI fallback error: {e}")
        
        # Fallback to local model (simulating structured output since local model can't easily do json)
        prompt_text = self.prompt.format(context=context, history=history_str, question=message)
        inputs = self.tokenizer(prompt_text, return_tensors="pt", truncation=True, max_length=1024)
        outputs = self.model.generate(**inputs, max_new_tokens=160)
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return {
            "anonymous": bool(anonymous),
            "structured_response": {
                "summary": response,
                "advice": ["Check wellness center"],
                "action_required": "Read summary",
                "risk_level": urgency,
                "follow_up_questions": []
            },
            "sources": [d.page_content for d in docs[:3]],
        }
