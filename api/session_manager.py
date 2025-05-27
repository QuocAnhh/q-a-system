"""
Session management utilities
"""
from flask import session
from datetime import datetime
import uuid


def get_user_data():
    """Lấy dữ liệu người dùng từ session"""
    try:
        if 'user_data' not in session:
            session['user_data'] = {
                'deadlines': {},
                'schedule': {},
                'preferences': {},
                'current_ai_mode': None,
                'conversations': {},  # {conversation_id: {...}}
                'current_conversation_id': None
            }
        
        # Đảm bảo tất cả keys đều tồn tại
        user_data = session['user_data']
        if 'conversations' not in user_data:
            user_data['conversations'] = {}
        if 'current_conversation_id' not in user_data:
            user_data['current_conversation_id'] = None
        if 'deadlines' not in user_data:
            user_data['deadlines'] = {}
        if 'schedule' not in user_data:
            user_data['schedule'] = {}
        if 'preferences' not in user_data:
            user_data['preferences'] = {}
        if 'current_ai_mode' not in user_data:
            user_data['current_ai_mode'] = None
            
        session['user_data'] = user_data
        return user_data
    except Exception as e:
        print(f"Error in get_user_data: {e}")
        # Trả về dữ liệu mặc định nếu session không hoạt động
        return {
            'deadlines': {},
            'schedule': {},
            'preferences': {},
            'current_ai_mode': None,
            'conversations': {},
            'current_conversation_id': None
        }


def save_user_data(data):
    """Lưu dữ liệu người dùng vào session"""
    try:
        session['user_data'] = data
        session.permanent = True
    except Exception as e:
        print(f"Error in save_user_data: {e}")


def create_new_conversation():
    """Tạo cuộc hội thoại mới"""
    try:
        user_data = get_user_data()
        conversation_id = str(uuid.uuid4())
        
        conversation = {
            'id': conversation_id,
            'title': f"Cuộc hội thoại {len(user_data['conversations']) + 1}",
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': [],
            'ai_mode': None
        }
        
        user_data['conversations'][conversation_id] = conversation
        user_data['current_conversation_id'] = conversation_id
        save_user_data(user_data)
        
        return conversation
    except Exception as e:
        print(f"Error in create_new_conversation: {e}")
        # Trả về conversation mặc định
        conversation_id = str(uuid.uuid4())
        return {
            'id': conversation_id,
            'title': "Cuộc hội thoại mặc định",
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'messages': [],
            'ai_mode': None
        }


def get_current_conversation():
    """Lấy cuộc hội thoại hiện tại"""
    try:
        user_data = get_user_data()
        
        # Nếu chưa có cuộc hội thoại nào, tạo mới
        if not user_data.get('current_conversation_id') or user_data['current_conversation_id'] not in user_data.get('conversations', {}):
            return create_new_conversation()
        
        return user_data['conversations'][user_data['current_conversation_id']]
    except Exception as e:
        print(f"Error in get_current_conversation: {e}")
        return create_new_conversation()


def switch_conversation(conversation_id):
    """Chuyển sang cuộc hội thoại khác"""
    user_data = get_user_data()
    
    if conversation_id in user_data['conversations']:
        user_data['current_conversation_id'] = conversation_id
        save_user_data(user_data)
        return user_data['conversations'][conversation_id]
    
    return None


def add_message_to_conversation(question, answer, ai_mode=None):
    """Thêm tin nhắn vào cuộc hội thoại hiện tại với thread safety"""
    try:
        user_data = get_user_data()
        conversation = get_current_conversation()
        
        # Đảm bảo conversation tồn tại và có structure đúng
        if not conversation or 'messages' not in conversation:
            conversation = create_new_conversation()
            user_data['conversations'][conversation['id']] = conversation
            user_data['current_conversation_id'] = conversation['id']
        
        message = {
            'id': str(uuid.uuid4()),
            'question': question,
            'answer': answer,
            'timestamp': datetime.now().isoformat(),
            'ai_mode': ai_mode
        }
        
        # Thêm message vào conversation
        conversation['messages'].append(message)
        conversation['updated_at'] = datetime.now().isoformat()
        
        # Cập nhật tiêu đề nếu đây là tin nhắn đầu tiên
        if len(conversation['messages']) == 1:
            # Tạo tiêu đề từ câu hỏi đầu tiên (giới hạn 50 ký tự)
            title = question[:50] + "..." if len(question) > 50 else question
            conversation['title'] = title
        
        # Cập nhật AI mode cho conversation
        if ai_mode:
            conversation['ai_mode'] = ai_mode
            user_data['current_ai_mode'] = ai_mode
        
        # Lưu ngay lập tức để tránh mất dữ liệu
        save_user_data(user_data)
        
        # Debug log
        print(f"[DEBUG] Added message to conversation {conversation['id']}, total messages: {len(conversation['messages'])}")
        
        return message
    except Exception as e:
        print(f"Error in add_message_to_conversation: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_conversation_history():
    """Lấy danh sách tất cả cuộc hội thoại"""
    try:
        user_data = get_user_data()
        conversations = []
        
        for conv_id, conv in user_data['conversations'].items():
            conversations.append({
                'id': conv['id'],
                'title': conv['title'],
                'created_at': conv['created_at'],
                'updated_at': conv['updated_at'],
                'message_count': len(conv['messages']),
                'ai_mode': conv.get('ai_mode'),
                'is_current': conv_id == user_data['current_conversation_id']
            })
        
        # Sắp xếp theo thời gian cập nhật mới nhất
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        return conversations
    except Exception as e:
        print(f"Error in get_conversation_history: {e}")
        return []


def delete_conversation(conversation_id):
    """Xóa cuộc hội thoại"""
    user_data = get_user_data()
    
    if conversation_id in user_data['conversations']:
        del user_data['conversations'][conversation_id]
        
        # Nếu xóa cuộc hội thoại hiện tại, chuyển sang cuộc hội thoại khác hoặc tạo mới
        if user_data['current_conversation_id'] == conversation_id:
            if user_data['conversations']:
                # Chuyển sang cuộc hội thoại mới nhất
                latest_conv = max(user_data['conversations'].items(), 
                                key=lambda x: x[1]['updated_at'])
                user_data['current_conversation_id'] = latest_conv[0]
            else:
                # Tạo cuộc hội thoại mới
                user_data['current_conversation_id'] = None
        
        save_user_data(user_data)
        return True
    
    return False


def set_ai_mode(mode):
    """Thiết lập chế độ AI hiện tại"""
    user_data = get_user_data()
    conversation = get_current_conversation()
    
    user_data['current_ai_mode'] = mode
    conversation['ai_mode'] = mode
    save_user_data(user_data)


def get_ai_mode():
    """Lấy chế độ AI hiện tại"""
    user_data = get_user_data()
    return user_data.get('current_ai_mode', None)


def cleanup_old_conversations():
    """Dọn dẹp các cuộc hội thoại cũ để tối ưu memory"""
    try:
        user_data = get_user_data()
        conversations = user_data.get('conversations', {})
        
        # Tăng giới hạn lên 50 conversations thay vì 10
        max_conversations = 50
        
        if len(conversations) <= max_conversations:
            return
        
        # Sắp xếp theo thời gian cập nhật
        sorted_convs = sorted(
            conversations.items(), 
            key=lambda x: x[1].get('updated_at', ''), 
            reverse=True
        )
        
        # Giữ lại conversations mới nhất
        keep_convs = dict(sorted_convs[:max_conversations])
        
        # Cập nhật lại dữ liệu
        user_data['conversations'] = keep_convs
        
        # Nếu current conversation bị xóa, chuyển sang conversation mới nhất
        if user_data.get('current_conversation_id') not in keep_convs:
            if keep_convs:
                user_data['current_conversation_id'] = list(keep_convs.keys())[0]
            else:
                user_data['current_conversation_id'] = None
        
        save_user_data(user_data)
        print(f"[DEBUG] Cleaned up conversations, kept {len(keep_convs)} out of {len(conversations)}")
        
    except Exception as e:
        print(f"Error in cleanup_old_conversations: {e}")


def get_conversation_context_summary(conversation_id):
    """Lấy tóm tắt ngữ cảnh của cuộc hội thoại để cải thiện context preservation"""
    try:
        user_data = get_user_data()
        conversation = user_data['conversations'].get(conversation_id)
        
        if not conversation or not conversation.get('messages'):
            return ""
        
        # Lấy 3 tin nhắn đầu và 3 tin nhắn cuối để tạo context summary
        messages = conversation['messages']
        if len(messages) <= 6:
            return ""
        
        first_messages = messages[:3]
        last_messages = messages[-3:]
        
        summary = "Tóm tắt ngữ cảnh cuộc hội thoại:\n"
        summary += "Phần đầu:\n"
        for msg in first_messages:
            summary += f"Q: {msg['question'][:100]}...\n"
            summary += f"A: {msg['answer'][:100]}...\n"
        
        summary += "\nPhần gần đây:\n"
        for msg in last_messages:
            summary += f"Q: {msg['question'][:100]}...\n"
            summary += f"A: {msg['answer'][:100]}...\n"
        
        return summary
        
    except Exception as e:
        print(f"Error in get_conversation_context_summary: {e}")
        return ""
