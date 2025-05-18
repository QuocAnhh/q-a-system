from transformers import pipeline

qa_generator = pipeline("text2text-generation", model="google/flan-t5-small")

def generate_answer(question):
    prompt = f"Answer the question: {question}"
    response = qa_generator(prompt, max_length=100, do_sample=False)
    # Đảm bảo lấy đúng key, fallback nếu không có 'generated_text'
    if response and 'generated_text' in response[0]:
        return response[0]['generated_text']
    elif response and 'text' in response[0]:
        return response[0]['text']
    else:
        return "Xin lỗi, tôi chưa có câu trả lời cho câu hỏi này."
