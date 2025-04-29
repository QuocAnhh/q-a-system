import streamlit as st
from retriever import load_data, find_similar_question
from generator import generate_answer

st.set_page_config(page_title="QA Demo", page_icon="❓")
st.title("Hệ thống hỏi đáp thông minh")

@st.cache_resource
def init_data():
    return load_data()

data = init_data()

query = st.text_input("Nhập câu hỏi của bạn:")
if query:
    matched_question, answer, score = find_similar_question(query, data)
    
    if score > 0.7:
        st.success(f"Câu hỏi gần nhất: {matched_question}\n Trả lời: {answer}")
    else:
        st.warning("Không tìm thấy câu hỏi tương tự. Đang tạo câu trả lời bằng AI...")
        generated = generate_answer(query)
        st.info(f"Câu trả lời AI: {generated}")
