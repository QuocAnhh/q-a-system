import streamlit as st
from retriever import load_data, ChatbotSession
from generator import generate_answer

st.set_page_config(page_title="QA Demo", page_icon="❓")
st.title("Chatbot hỏi đáp thông minh")

@st.cache_resource
def init_data(file_path):
    return load_data(file_path=file_path)

data_file = st.sidebar.text_input("Đường dẫn file dữ liệu:", "C:/Users/ADMIN/Project-NLP/data/faq.json")
data = init_data(data_file)

if "chatbot" not in st.session_state:
    st.session_state.chatbot = ChatbotSession(data)

query = st.text_input("Nhập câu hỏi:")

if st.button("Gửi") and query:
    turn = st.session_state.chatbot.ask(query, generator=generate_answer)
    st.session_state.last_turn = turn

# Hiển thị lịch sử hội thoại
st.subheader("Lịch sử hội thoại")
for turn in st.session_state.chatbot.get_history():
    st.markdown(f"**Bạn:** {turn['user']}")
    if turn["matched_question"]:
        st.markdown(f"**Bot:** {turn['answer']} _(matched: {turn['matched_question']})_")
    else:
        st.markdown(f"**Bot:** {turn['answer']} _(generated)_")
    st.markdown("---")
