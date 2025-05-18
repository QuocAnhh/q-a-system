import json
import os
from sentence_transformers import SentenceTransformer, util

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

def get_model(model_name=DEFAULT_MODEL_NAME):
    return SentenceTransformer(model_name)

def load_data(file_path="C:/Users/ADMIN/Project-NLP/data/faq.json", model=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không thấy file dữ liệu: {file_path}")
    if model is None:
        model = get_model()
    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)
    questions = [item["question"] for item in content]
    answers = [item["answer"] for item in content]
    embeddings = model.encode(questions, convert_to_tensor=True)
    return {"questions": questions, "answers": answers, "embeddings": embeddings, "model": model}

def find_similar_question(query, data):
    model = data.get("model")
    if model is None:
        model = get_model()
    query_embedding = model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, data['embeddings'])[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()
    return {
        "matched_question": data['questions'][best_idx],
        "answer": data['answers'][best_idx],
        "score": best_score
    }

class ChatbotSession:
    def __init__(self, data):
        self.data = data
        self.history = []

    def ask(self, query, generator=None, threshold=0.7):
        result = find_similar_question(query, self.data)
        if result["score"] > threshold:
            answer = result["answer"]
            matched_question = result["matched_question"]
            generated = False
        else:
            # luôn gọi generator nếu không tìm thấy câu hỏi tương tự
            if generator is not None:
                answer = generator(query)
            else:
                answer = "Xin lỗi, tôi chưa có câu trả lời cho câu hỏi này."
            matched_question = None
            generated = True
        turn = {
            "user": query,
            "matched_question": matched_question,
            "answer": answer,
            "score": result["score"],
            "generated": generated
        }
        self.history.append(turn)
        return turn

    def get_history(self):
        return self.history
