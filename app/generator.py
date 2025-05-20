from transformers import pipeline

qa_generator = pipeline(
    "text-generation",
    model="bkai-foundation-models/vietnamese-llama2-7b-40GB",
    max_new_tokens=100
)

def generate_answer(question):
    # Prompt
    prompt = f"<s>### Câu hỏi:\n{question}\n### Trả lời:"
    response = qa_generator(prompt)
    if response and "generated_text" in response[0]:
        answer = response[0]["generated_text"]
        if "### Trả lời:" in answer:
            answer = answer.split("### Trả lời:")[-1].strip()
        return answer.strip()
    else:
        return "Xin lỗi, tôi chưa có câu trả lời cho câu hỏi này"
