from flask import session
from database import get_db
from typing import Dict, List, Optional, Any
import uuid


def get_user_id():
    """Get or create user ID from session"""
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']


def get_actual_user_id():
    """Get actual user ID from database (ensures user exists)"""
    db = get_db()
    session_user_id = get_user_id()
    return db.get_or_create_user(session_user_id)


def get_user_data() -> Dict:
    """Get user data (preferences, deadlines, schedule) - compatible with old interface"""
    db = get_db()
    user_id = get_user_id()
    
    # đảm bảo user tồn tại trong database - use user_id as session_id for compatibility
    actual_user_id = db.get_or_create_user(user_id)
    
    # Get user data
    user_data = db.get_user_data(actual_user_id)
      # lấy current conversation info for compatibility
    current_conv = db.get_current_conversation(actual_user_id)
    conversations = db.get_conversations(actual_user_id)
    
    # chuyển đổi to old format for compatibility
    conversations_dict = {}
    for conv in conversations:
        conv_detail = db.get_conversation(conv['id'], user_id)
        if conv_detail:
            conversations_dict[conv['id']] = conv_detail
    
    return {
        'deadlines': user_data.get('deadlines', {}),
        'schedule': user_data.get('schedule', {}),
        'preferences': user_data.get('preferences', {}),
        'current_ai_mode': current_conv.get('ai_mode') if current_conv else None,
        'conversations': conversations_dict,
        'current_conversation_id': current_conv.get('id') if current_conv else None
    }


def save_user_data(preferences: Dict = None, deadlines: Dict = None, schedule: Dict = None):
    """Save user data - compatible with old interface"""
    db = get_db()
    user_id = get_user_id()
    db.save_user_data(user_id, preferences, deadlines, schedule)


def create_new_conversation(title: str = None, ai_mode: str = None) -> Dict:
    """Create new conversation"""
    db = get_db()
    user_id = get_user_id()
    
    if not title:
        # Generate title based on timestamp
        from datetime import datetime
        title = f"Hội thoại {datetime.now().strftime('%d/%m %H:%M')}"
    
    return db.create_conversation(user_id, title, ai_mode)


def get_current_conversation() -> Optional[Dict]:
    """Get current active conversation"""
    db = get_db()
    user_id = get_user_id()
    return db.get_current_conversation(user_id)


def switch_conversation(conversation_id: str) -> Optional[Dict]:
    """Switch to different conversation"""
    db = get_db()
    user_id = get_user_id()
    return db.switch_conversation(conversation_id, user_id)


def add_message_to_conversation(question: str, answer: str, ai_mode: str = None, metadata: Dict = None) -> Optional[Dict]:
    """Add message to current conversation"""
    db = get_db()
    user_id = get_user_id()
    
    # lấy hoặc tạo current conversation
    current_conv = db.get_current_conversation(user_id)
    if not current_conv:
        # tạo new conversation nếu ko tồn tại
        title = question[:50] + "..." if len(question) > 50 else question
        current_conv = db.create_conversation(user_id, title, ai_mode)
    
    return db.add_message(current_conv['id'], user_id, question, answer, ai_mode, metadata)


def get_conversation_history(limit: int = 50) -> List[Dict]:
    """Get conversation history with proper is_current marking"""
    db = get_db()
    user_id = get_user_id()
    return db.get_conversations(user_id, limit)


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation"""
    db = get_db()
    user_id = get_user_id()
    return db.delete_conversation(conversation_id, user_id)


def cleanup_old_conversations(keep_count: int = 50):
    """Clean up old conversations"""
    db = get_db()
    user_id = get_user_id()
    db.cleanup_old_conversations(user_id, keep_count)


def export_all_data() -> Dict:
    """Export all user data for debugging"""
    db = get_db()
    user_id = get_user_id()
    return db.export_all_data(user_id)


def export_to_html() -> str:
    """Export chat history to HTML format"""
    db = get_db()
    user_id = get_user_id()
    return db.export_to_html(user_id)


# Migration function to move data from session to database
def migrate_session_to_database():
    """Migrate existing session data to database (one-time operation)"""
    if 'user_data' not in session:
        return False
    
    try:
        db = get_db()
        user_id = get_user_id()
        
        # Ensure user exists
        db.get_or_create_user(session.get('session_id', user_id))
        
        session_data = session['user_data']
        
        # Migrate user preferences, deadlines, schedule
        preferences = session_data.get('preferences', {})
        deadlines = session_data.get('deadlines', {})
        schedule = session_data.get('schedule', {})
        
        if preferences or deadlines or schedule:
            db.save_user_data(user_id, preferences, deadlines, schedule)
        
        # Migrate conversations
        conversations = session_data.get('conversations', {})
        current_conv_id = session_data.get('current_conversation_id')
        
        for conv_id, conv_data in conversations.items():
            # Create conversation in database
            new_conv = db.create_conversation(
                user_id,
                conv_data.get('title', 'Migrated Conversation'),
                conv_data.get('ai_mode')
            )
            
            # Add messages
            for msg in conv_data.get('messages', []):
                db.add_message(
                    new_conv['id'],
                    user_id,
                    msg.get('question', ''),
                    msg.get('answer', ''),
                    msg.get('ai_mode'),
                    {'migrated': True, 'original_timestamp': msg.get('timestamp')}
                )
            
            # Set as active if it was the current conversation
            if conv_id == current_conv_id:
                db.switch_conversation(new_conv['id'], user_id)
        
        # Clear session data after successful migration
        session.pop('user_data', None)
        
        print(f"Successfully migrated {len(conversations)} conversations to database")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
