from transformers import pipeline

qa_generator = pipeline("text2text-generation", model="google/flan-t5-small")

def generate_answer(question):
    prompt = f"Answer the question: {question}"
    response = qa_generator(prompt, max_length=100, do_sample=False)[0]['generated_text']
    return response
