import json
import os
from sentence_transformers import SentenceTransformer, util

#loadd model
model = SentenceTransformer("all-MiniLM-L6-v2")

def load_data(file_path="C:/Users/ADMIN/Project-NLP/data/faq.json"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    questions = [item["question"] for item in content]
    answers = [item["answer"] for item in content]
    embeddings = model.encode(questions, convert_to_tensor=True)

    return {"questions": questions, "answers": answers, "embeddings": embeddings}

#Hàm tìm câu hỏi tương tự
def find_similar_question(query, data):
    query_embedding = model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, data['embeddings'])[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()
    return data['questions'][best_idx], data['answers'][best_idx], best_score
