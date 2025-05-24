from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
import os
from datetime import datetime

from config import Config
from session_manager import (
    get_user_data, save_user_data, create_new_conversation, 
    get_current_conversation, switch_conversation, add_message_to_conversation,
    get_conversation_history, delete_conversation
)
from ai_handlers import handle_ai_question
from utils import handle_deadline_commands, handle_calendar_commands, handle_document_search

app = Flask(__name__)
CORS(app)
app.secret_key = Config.SECRET_KEY


@app.route("/")
def index():
    """Serve trang chủ"""
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'index.html')
        return send_file(frontend_path)
    except Exception as e:
        return f"Lỗi: {e}", 500


@app.route("/<path:filename>")
def serve_frontend_files(filename):
    """Serve các file frontend"""
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        return send_from_directory(frontend_path, filename)
    except Exception as e:
        return f"File không tìm thấy: {e}", 404


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve các file static"""
    try:
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        return send_from_directory(frontend_path, filename)
    except Exception as e:
        return f"File không tìm thấy: {e}", 404


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


@app.route("/chat", methods=["POST"])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Không có dữ liệu được gửi"}), 400
            
        question = data.get("question", "").strip()
        
        if not question:
            return jsonify({"error": "Bạn chưa nhập câu hỏi!"}), 400
        
        # Xử lý câu hỏi và trả về phản hồi
        response = process_question(question)
        
        # Lưu vào cuộc hội thoại hiện tại
        message = add_message_to_conversation(question, response["answer"], response.get("ai_mode"))
        
        return jsonify({
            "answer": response["answer"],
            "suggestions": response.get("suggestions", []),
            "calendar_events": response.get("calendar_events", []),
            "ai_mode": response.get("ai_mode", None),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Có lỗi xảy ra khi xử lý yêu cầu"}), 500


@app.route("/conversations", methods=["GET"])
def get_conversations():
    """Lấy danh sách tất cả cuộc hội thoại"""
    try:
        conversations = get_conversation_history()
        return jsonify({
            "conversations": conversations,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error getting conversations: {e}")
        return jsonify({"error": "Không thể lấy danh sách cuộc hội thoại"}), 500


@app.route("/conversations/new", methods=["POST"])
def new_conversation():
    """Tạo cuộc hội thoại mới"""
    try:
        conversation = create_new_conversation()
        return jsonify({
            "conversation": conversation,
            "message": "Đã tạo cuộc hội thoại mới",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error creating new conversation: {e}")
        return jsonify({"error": "Không thể tạo cuộc hội thoại mới"}), 500


@app.route("/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    """Lấy chi tiết một cuộc hội thoại"""
    try:
        conversation = switch_conversation(conversation_id)
        if conversation:
            return jsonify({
                "conversation": conversation,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Không tìm thấy cuộc hội thoại"}), 404
    except Exception as e:
        print(f"Error getting conversation: {e}")
        return jsonify({"error": "Không thể lấy cuộc hội thoại"}), 500


@app.route("/conversations/<conversation_id>", methods=["DELETE"])
def remove_conversation(conversation_id):
    """Xóa một cuộc hội thoại"""
    try:
        success = delete_conversation(conversation_id)
        if success:
            return jsonify({
                "message": "Đã xóa cuộc hội thoại",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Không tìm thấy cuộc hội thoại"}), 404
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return jsonify({"error": "Không thể xóa cuộc hội thoại"}), 500


@app.route("/conversations/<conversation_id>/switch", methods=["POST"])
def switch_to_conversation(conversation_id):
    """Chuyển sang cuộc hội thoại khác"""
    try:
        conversation = switch_conversation(conversation_id)
        if conversation:
            return jsonify({
                "conversation": conversation,
                "message": "Đã chuyển sang cuộc hội thoại khác",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Không tìm thấy cuộc hội thoại"}), 404
    except Exception as e:
        print(f"Error switching conversation: {e}")
        return jsonify({"error": "Không thể chuyển cuộc hội thoại"}), 500


# phần xử lý logic chính
def process_question(question):
    """Xử lý câu hỏi từ người dùng"""
    q = question.lower().strip()
    user_data = get_user_data()
    
    # xử lý deadline commands
    if 'deadline' in q:
        return handle_deadline_commands(question, user_data)
    
    # xử lý calendar commands
    if any(keyword in q for keyword in ['lịch', 'calendar', 'thêm lịch']):
        return handle_calendar_commands(question, user_data)
    
    # xử lý tìm kiếm tài liệu
    if any(keyword in q for keyword in ['tài liệu', 'học', 'tìm', 'search']):
        return handle_document_search(question, user_data)
    
    # xử lý general commands
    return handle_general_commands(question, user_data)


def handle_general_commands(question, user_data):
    """Xử lý các lệnh chung và câu hỏi AI"""
    q = question.lower()
    
    if any(keyword in q for keyword in ['xin chào', 'hello', 'hi', 'chào']):
        return {
            "answer": "👋 Xin chào! Tôi là trợ lý học tập thông minh. Tôi có thể giúp bạn:<br>• 📅 Quản lý lịch học và deadline<br>• 📚 Tìm tài liệu và giải thích kiến thức<br>• 🤖 Trả lời các câu hỏi học tập<br>• 💡 Đưa ra lời khuyên và gợi ý học tập",
            "suggestions": ["Giải thích về Python", "Công thức Toán", "Lịch sử Việt Nam", "Mẹo học tập"]
        }
    
    if any(keyword in q for keyword in ['giúp', 'help', 'hướng dẫn']):
        return {
            "answer": """
                📖 <strong>Hướng dẫn sử dụng:</strong><br><br>
                <strong>🤖 Hỏi đáp AI học tập:</strong><br>
                • Hỏi bất kỳ câu hỏi nào về học tập<br>
                • Giải thích khái niệm, công thức các môn học<br>
                • Hướng dẫn cách làm bài tập<br>
                • Mẹo và phương pháp học tập hiệu quả<br><br>
                
                <strong>🗓️ Quản lý deadline:</strong><br>
                • "deadline" - Xem tất cả deadline<br>
                • "thêm deadline Toán 2024-12-25" - Thêm deadline mới<br>
                • "xóa deadline Toán" - Xóa deadline<br><br>
                
                <strong>📅 Quản lý lịch học:</strong><br>
                • "lịch hôm nay" - Xem lịch hôm nay<br>
                • "lịch tuần này" - Xem lịch tuần<br><br>
                
                <strong>📚 Tìm tài liệu:</strong><br>
                • "tìm tài liệu Python" - Tìm tài liệu học tập<br>
            """,
            "suggestions": ["Hỏi về Toán", "Giải thích Vật lý", "Lập trình Python", "Mẹo ôn thi"]
        }
    
    return handle_ai_question(question)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
