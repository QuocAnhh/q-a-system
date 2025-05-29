from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_cors import CORS
import os
from datetime import datetime
import json

from config import Config
from database import get_db
from ai_handlers import handle_ai_question, handle_ai_question_with_context
from utils import handle_deadline_commands, handle_calendar_commands, handle_document_search
from db_session_manager import export_to_html

# Session management functions
def get_user_id():
    """Get or create user ID from session"""
    if 'user_id' not in session:
        session['user_id'] = f"user_{datetime.now().timestamp()}"
    return session['user_id']

def get_conversation_history():
    """Get conversation history"""
    db = get_db()
    user_id = get_user_id()
    return db.get_conversations(user_id)

def create_new_conversation(title=None, ai_mode=None):
    """Create new conversation"""
    db = get_db()
    user_id = get_user_id()
    if not title:
        title = f"Hội thoại {datetime.now().strftime('%d/%m %H:%M')}"
    
    # Tạo conversation mới
    conversation = db.create_conversation(user_id, title, ai_mode)
    
    return conversation

def get_current_conversation():
    """Get current conversation"""
    db = get_db()
    user_id = get_user_id()
    return db.get_current_conversation(user_id)

def switch_conversation(conversation_id):
    """Switch to conversation"""
    db = get_db()
    user_id = get_user_id()
    return db.switch_conversation(conversation_id, user_id)

def delete_conversation(conversation_id):
    """Delete conversation"""
    db = get_db()
    user_id = get_user_id()
    return db.delete_conversation(conversation_id, user_id)

def add_message_to_conversation(question, answer, ai_mode=None, metadata=None):
    """Add message to current conversation"""
    db = get_db()
    user_id = get_user_id()
    # Lấy đúng hội thoại active
    current_conv = db.get_current_conversation(user_id)
    if not current_conv:
        title = question[:50] + "..." if len(question) > 50 else question
        current_conv = db.create_conversation(user_id, title, ai_mode)
        db.switch_conversation(current_conv['id'], user_id)
    return db.add_message(current_conv['id'], user_id, question, answer, ai_mode, metadata)

# Local export function was removed and replaced with imported function from db_session_manager

def get_user_data():
    """Get user's preferences, deadlines, schedule"""
    try:
        db = get_db()
        user_id = get_user_id()
        return db.get_user_data(user_id)
    except Exception as e:
        print(f"[ERROR] get_user_data failed: {e}")
        return {'preferences': {}, 'deadlines': {}, 'schedule': {}}

def save_user_data(data):
    """Save user's preferences, deadlines, schedule"""
    db = get_db()
    user_id = get_user_id()
    return db.update_user_data(user_id, data)

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
    """Main chat endpoint với improved error handling và context preservation"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Không có dữ liệu được gửi"}), 400
            
        question = data.get("question", "").strip()
        
        if not question:
            return jsonify({"error": "Bạn chưa nhập câu hỏi!"}), 400
        
        print(f"[DEBUG] Processing question: {question[:100]}...")
        
        # LẤY CONTEXT từ cuộc hội thoại hiện tại
        current_conversation = get_current_conversation()
        context_messages = []
        
        if current_conversation and current_conversation.get('messages'):
            # Lấy 5 tin nhắn gần nhất để làm context
            recent_messages = current_conversation['messages'][-5:]
            for msg in recent_messages:
                context_messages.extend([
                    {"role": "user", "content": msg.get('question', '')},
                    {"role": "assistant", "content": msg.get('answer', '')}
                ])
        
        # Xử lý câu hỏi với context
        response = process_question_with_context(question, context_messages)
        
        if not response or not isinstance(response, dict):
            return jsonify({"error": "Có lỗi xử lý câu hỏi"}), 500
        
        # Lưu vào cuộc hội thoại hiện tại với error handling
        try:
            message = add_message_to_conversation(
                question, 
                response.get("answer", "Không có phản hồi"), 
                response.get("ai_mode")
            )
            if message:
                print(f"[DEBUG] Message saved successfully: {message['id']}")
            else:
                print("[WARNING] Failed to save message")
        except Exception as save_error:
            print(f"[ERROR] Failed to save message: {save_error}")
            # Vẫn trả về response mà không fail
        
        return jsonify({
            "answer": response.get("answer", "Có lỗi xảy ra"),
            "suggestions": response.get("suggestions", []),
            "calendar_events": response.get("calendar_events", []),
            "ai_mode": response.get("ai_mode", None),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Có lỗi xảy ra khi xử lý yêu cầu. Vui lòng thử lại."}), 500


@app.route('/conversations', methods=['GET'])
def get_conversations():
    """Lấy danh sách tất cả cuộc hội thoại"""
    try:
        db = get_db()
        user_id = get_user_id()
        conversations = db.get_conversations(user_id)
        return jsonify({
            'conversations': conversations,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/conversations/new', methods=['POST'])
def create_conversation():
    """Tạo cuộc hội thoại mới và chuyển active"""
    try:
        db = get_db()
        user_id = get_user_id()
        # Tạo tiêu đề mặc định dựa trên thời gian
        title = f"Hội thoại {datetime.now().strftime('%d/%m %H:%M')}"
        # Tạo hội thoại mới và chuyển active
        conversation = db.create_conversation(user_id, title)
        db.switch_conversation(conversation['id'], user_id)
        conversations = db.get_conversations(user_id)
        return jsonify({
            'conversation': conversation,
            'conversations': conversations,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        import traceback
        traceback.print_exc()  # In ra lỗi chi tiết
        return jsonify({'error': str(e)}), 500

@app.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Lấy cuộc hội thoại cụ thể với tin nhắn"""
    try:
        db = get_db()
        user_id = get_user_id()
        conversation = db.get_conversation(conversation_id, user_id)
        if conversation:
            return jsonify({
                'conversation': conversation,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Không tìm thấy cuộc hội thoại'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/conversations/<conversation_id>/switch', methods=['POST'])
def switch_to_conversation(conversation_id):
    """Chuyển sang cuộc hội thoại khác"""
    try:
        db = get_db()
        user_id = get_user_id()
        conversation = db.switch_conversation(conversation_id, user_id)
        conversations = db.get_conversations(user_id)
        if conversation:
            return jsonify({
                'conversation': conversation,
                'conversations': conversations,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Không tìm thấy cuộc hội thoại'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Xóa một cuộc hội thoại"""
    try:
        db = get_db()
        user_id = get_user_id()
        db.delete_conversation(conversation_id, user_id)
        conversations = db.get_conversations(user_id)
        return jsonify({
            'success': True,
            'conversations': conversations,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:        return jsonify({'error': str(e)}), 500


@app.route("/export-chat", methods=["GET"])
def export_chat_history():
    """Export toàn bộ lịch sử chat dưới dạng HTML"""
    try:
        from flask import Response
        
        html_content = export_to_html()
        
        # Tạo response với HTML content
        response = Response(
            html_content,
            mimetype='text/html',
            headers={
                "Content-Disposition": f"attachment; filename=chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            }
        )
        
        return response
        
    except Exception as e:
        print(f"Error exporting chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Không thể export chat: {str(e)}",
            "debug_info": {
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
        }), 500


# phần xử lý logic chính với context
def process_question_with_context(question, context_messages=None):
    """Xử lý câu hỏi từ người dùng với context từ lịch sử cuộc trò chuyện"""
    q = question.lower().strip()
    user_data = get_user_data()
    
    print(f"[DEBUG] process_question_with_context called with: {question}")
    print(f"[DEBUG] Context messages count: {len(context_messages) if context_messages else 0}")
    
    # 1. Ưu tiên các lệnh chào hỏi TRƯỚC TIÊN
    greeting_patterns = [
        q == 'xin chào', q == 'chào', q == 'hello', q == 'hi',
        q.startswith('xin chào'), q.startswith('chào bạn'), 
        q.startswith('hello '), q.startswith('hi '),
        q in ['xin chào!', 'chào!', 'hello!', 'hi!']
    ]
    
    if any(greeting_patterns):
        print(f"[DEBUG] Detected greeting")
        return {
            "answer": "👋 Xin chào! Tôi là trợ lý học tập thông minh. Tôi có thể giúp bạn:<br>• 📅 Quản lý lịch học và deadline<br>• 📚 Tìm tài liệu và giải thích kiến thức<br>• 🤖 Trả lời các câu hỏi học tập<br>• 💡 Đưa ra lời khuyên và gợi ý học tập",
            "suggestions": ["Giải thích về Python", "Công thức Toán", "Lịch sử Việt Nam", "Mẹo học tập"]
        }
    
    # 2. Các lệnh deadline
    if q.startswith('deadline') or 'thêm deadline' in q or 'xóa deadline' in q:
        print(f"[DEBUG] Detected deadline command")
        return handle_deadline_commands(question, user_data)
    
    # 3. Lệnh quản lý lịch
    if any(phrase in q for phrase in ['lịch hôm nay', 'lịch tuần', 'thêm lịch', 'calendar', 'lịch học']):
        print(f"[DEBUG] Detected calendar command")
        return handle_calendar_commands(question, user_data)
    
    # 4. Tìm kiếm tài liệu
    if q.startswith('tìm tài liệu') or q.startswith('search'):
        print(f"[DEBUG] Detected document search")
        return handle_document_search(question, user_data)
    
    # 5. Còn lại tất cả đều là câu hỏi học tập - chuyển cho AI handler với context
    print(f"[DEBUG] Routing to AI handler with context")
    return handle_ai_question_with_context(question, context_messages)


def process_question(question):
    """Xử lý câu hỏi từ người dùng (compatibility function)"""
    return process_question_with_context(question, None)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
