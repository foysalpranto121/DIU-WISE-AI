import os
import json

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


class RAGEngine:
    def __init__(self, knowledge_file: str, model_dir: str):
        self.knowledge_file = knowledge_file
        self.vector_path = os.path.join(model_dir, "faiss_index")
        os.makedirs(model_dir, exist_ok=True)
        self.embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.retriever = self._build_retriever()

    def _load_documents(self):
        with open(self.knowledge_file, "r", encoding="utf-8") as fp:
            chunks = [line.strip() for line in fp.readlines() if line.strip()]
        return [Document(page_content=chunk) for chunk in chunks]

    def _build_retriever(self):
        pkl_path = os.path.join(self.vector_path, "index.pkl")
        faiss_path = os.path.join(self.vector_path, "index.faiss")
        if (
            os.path.exists(self.vector_path)
            and os.path.exists(pkl_path)
            and os.path.exists(faiss_path)
        ):
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

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #
    def answer(
        self,
        message: str,
        anonymous: bool = False,
        history: list = None,
        intent: str = "general",
        urgency: str = "low",
        context_data: dict = None,
    ):
        if history is None:
            history = []
        if context_data is None:
            context_data = {}

        # Retrieve relevant knowledge
        docs = self.retriever.invoke(message)
        context = "\n".join(d.page_content for d in docs[:4])

        # Format last 5 conversation turns
        history_str = "\n".join(
            [f"User: {m.get('user','')}\nAI: {m.get('ai','')}" for m in history[-5:]]
        )

        result = self._openai_answer(
            message, context, history_str, intent, urgency, context_data
        )

        return {
            "anonymous": bool(anonymous),
            "structured_response": result,
            "sources": [d.page_content for d in docs[:3]],
        }

    # ------------------------------------------------------------------ #
    #  OpenAI (primary)                                                    #
    # ------------------------------------------------------------------ #
    def _openai_answer(self, message, context, history_str, intent, urgency, context_data):
        key = os.getenv("OPENAI_API_KEY", "")
        if not key or key == "your_openai_api_key_here":
            return self._fallback_response(message, urgency)

        try:
            from openai import OpenAI
            base_url = os.getenv("OPENAI_BASE_URL")
            client_kwargs = {"api_key": key, "timeout": 30}
            if base_url:
                client_kwargs["base_url"] = base_url
            client = OpenAI(**client_kwargs)

            sys_prompt = f"""You are DIU WISE AI — a compassionate academic and mental-wellness assistant built for Daffodil International University students.

IMPORTANT LANGUAGE RULE:
- Always reply in BOTH Bangla AND English.
- Put the English version first, then the Bangla version below it.
- Label them clearly: "English:" and "বাংলা:" (or just write them in both languages naturally).

You MUST respond with a valid JSON object matching EXACTLY this schema:
{{
  "summary": "1-sentence English summary",
  "summary_bn": "একটি বাক্যে বাংলায় সারসংক্ষেপ",
  "advice": ["English step 1", "English step 2", "English step 3"],
  "advice_bn": ["বাংলা পদক্ষেপ ১", "বাংলা পদক্ষেপ ২", "বাংলা পদক্ষেপ ৩"],
  "action_required": "Main takeaway in English",
  "action_required_bn": "প্রধান পরামর্শ বাংলায়",
  "risk_level": "low" | "medium" | "high",
  "follow_up_questions": ["English follow-up question?"],
  "follow_up_questions_bn": ["বাংলায় ফলো-আপ প্রশ্ন?"]
}}

Guidelines:
- Be warm, supportive, and non-clinical.
- Give concrete, actionable advice specific to university life.
- If urgency is high, always recommend speaking with a counselor immediately.
- Use retrieved knowledge context when relevant.

Retrieved Knowledge Context:
{context}

Student Context: {json.dumps(context_data)}
Intent: {intent} | Urgency: {urgency}"""

            response_obj = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {
                        "role": "user",
                        "content": f"Conversation History:\n{history_str}\n\nStudent Message: {message}",
                    },
                ],
                max_tokens=800,
                temperature=0.5,
            )
            raw = response_obj.choices[0].message.content.strip()
            return json.loads(raw)

        except Exception as e:
            print(f"[RAGEngine] OpenAI error: {e}")
            return self._fallback_response(message, urgency)

    # ------------------------------------------------------------------ #
    #  Fallback (no API key / network error)                              #
    # ------------------------------------------------------------------ #
    def _fallback_response(self, message: str, urgency: str):
        """Rule-based bilingual fallback when OpenAI is unavailable."""
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["stress", "stressed", "tension"]):
            summary    = "It sounds like you're under stress — that's very normal for students."
            summary_bn = "মনে হচ্ছে তুমি চাপে আছো — শিক্ষার্থীদের জন্য এটা খুবই স্বাভাবিক।"
            advice     = ["Take short breaks every 25–30 minutes.", "Try deep breathing for 2 minutes.", "Talk to a friend or counselor."]
            advice_bn  = ["প্রতি ২৫–৩০ মিনিটে ছোট বিরতি নাও।", "২ মিনিট গভীর শ্বাস নেওয়ার চেষ্টা করো।", "বন্ধু বা কাউন্সেলরের সাথে কথা বলো।"]
        elif any(w in msg_lower for w in ["sleep", "tired", "exhausted", "ঘুম"]):
            summary    = "Sleep is crucial for both your academic and mental health."
            summary_bn = "ঘুম তোমার পড়াশোনা ও মানসিক স্বাস্থ্য উভয়ের জন্যই অত্যন্ত গুরুত্বপূর্ণ।"
            advice     = ["Aim for 7–8 hours of sleep each night.", "Avoid screens 30 minutes before bed.", "Keep a consistent sleep schedule."]
            advice_bn  = ["প্রতি রাতে ৭–৮ ঘণ্টা ঘুমানোর চেষ্টা করো।", "ঘুমানোর ৩০ মিনিট আগে স্ক্রিন এড়িয়ে চলো।", "নিয়মিত ঘুমানোর সময়সূচি মেনে চলো।"]
        elif any(w in msg_lower for w in ["exam", "study", "grade", "পরীক্ষা", "পড়া"]):
            summary    = "Academic pressure is real — let's make a plan to tackle it."
            summary_bn = "পড়াশোনার চাপ বাস্তব — চলো একসাথে একটা পরিকল্পনা করি।"
            advice     = ["Break study sessions into 25-minute focused blocks.", "Prioritize topics by exam weight.", "Review notes within 24 hours of class."]
            advice_bn  = ["পড়াশোনাকে ২৫ মিনিটের ব্লকে ভাগ করো।", "পরীক্ষার গুরুত্ব অনুযায়ী বিষয় সাজাও।", "ক্লাসের ২৪ ঘণ্টার মধ্যে নোট রিভিউ করো।"]
        elif any(w in msg_lower for w in ["anxious", "anxiety", "worried", "উদ্বিগ্ন"]):
            summary    = "Feeling anxious is common — there are practical ways to ease it."
            summary_bn = "উদ্বেগ অনুভব করা সাধারণ ব্যাপার — এটা কমানোর কার্যকর উপায় আছে।"
            advice     = ["Practice 4-7-8 breathing: inhale 4s, hold 7s, exhale 8s.", "Write down your worries to get them out of your head.", "Speak to the DIU counseling center."]
            advice_bn  = ["৪-৭-৮ শ্বাস-প্রশ্বাস অনুশীলন করো: ৪ সেকেন্ড শ্বাস নাও, ৭ সেকেন্ড ধরে রাখো, ৮ সেকেন্ড ছাড়ো।", "তোমার চিন্তাগুলো লিখে ফেলো।", "DIU কাউন্সেলিং সেন্টারে কথা বলো।"]
        else:
            summary    = "I'm here to support your wellness journey at DIU."
            summary_bn = "আমি DIU-তে তোমার সুস্থতার যাত্রায় সাহায্য করতে এখানে আছি।"
            advice     = ["Check the resource library for wellness tips.", "Talk to a counselor if you need personal support.", "Remember: taking care of yourself is not optional."]
            advice_bn  = ["ওয়েলনেস টিপসের জন্য রিসোর্স লাইব্রেরি দেখো।", "ব্যক্তিগত সহায়তার প্রয়োজন হলে কাউন্সেলরের সাথে কথা বলো।", "মনে রেখো: নিজের যত্ন নেওয়া ঐচ্ছিক নয়।"]

        return {
            "summary": summary,
            "summary_bn": summary_bn,
            "advice": advice,
            "advice_bn": advice_bn,
            "action_required": advice[0],
            "action_required_bn": advice_bn[0],
            "risk_level": urgency if urgency in ("low", "medium", "high") else "low",
            "follow_up_questions": ["How are you feeling right now?", "Would you like to book a counselor session?"],
            "follow_up_questions_bn": ["এই মুহূর্তে তুমি কেমন অনুভব করছো?", "তুমি কি কাউন্সেলর সেশন বুক করতে চাও?"],
        }
