import re
import unicodedata
from transformers import pipeline

def preprocess_question(question):
    """Tiền xử lý input"""
    # chuẩn hóa unicode
    question = unicodedata.normalize("NFC", question)
    # drop khoảng trắng đầu/cuối và nhiều khoảng trắng liên tiếp
    question = re.sub(r"\s+", " ", question).strip()
    # drop những ký tự đặc biệt không cần thiết (giữ lại chữ, số, dấu câu cơ bản)
    question = re.sub(r"[^\w\s,.?!À-ỹà-ỹ]", "", question)
    return question

qa_generator = pipeline(
    "text-generation",
    model="bkai-foundation-models/vietnamese-llama2-7b-40GB",
    max_new_tokens=100
)

def generate_answer(question):
    question = preprocess_question(question)
    prompt = f"<s>### Câu hỏi:\n{question}\n### Trả lời:"
    response = qa_generator(prompt)
    if response and "generated_text" in response[0]:
        answer = response[0]["generated_text"]
        if "### Trả lời:" in answer:
            answer = answer.split("### Trả lời:")[-1].strip()
        return answer.strip()
    else:
        return "Xin lỗi, tôi chưa có câu trả lời cho câu hỏi này"
