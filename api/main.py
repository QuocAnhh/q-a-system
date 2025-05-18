from fastapi import FastAPI, Request
from pydantic import BaseModel
from app.retriever import load_data, find_similar_question
from app.generator import generate_answer

app = FastAPI()
data = load_data()

class QueryRequest(BaseModel):
    question: str

@app.post("/ask")
def ask_question(req: QueryRequest):
    matched_question, answer, score = find_similar_question(req.question, data)
    if score > 0.7:
        return {
            "matched_question": matched_question,
            "answer": answer,
            "score": score,
            "generated": False
        }
    else:
        generated = generate_answer(req.question)
        return {
            "matched_question": None,
            "answer": generated,
            "score": score,
            "generated": True
        }
