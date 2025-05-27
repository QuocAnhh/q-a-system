from flask import session
from database import get_db
from typing import Dict, List, Optional, Any
import uuid


def get_user_id():
    known_user_id = "c7edc5dc-5293-474d-9840-c4dff88a88e4"
    session['user_id'] = known_user_id
    print(f"[DEBUG] Using fixed user_id for testing: {session['user_id']}")
    
    return session['user_id']


def get_user_data() -> Dict:
    """Get user data (preferences, deadlines, schedule) - compatible with old interface"""
    db = get_db()
    user_id = get_user_id()  
    
    # get user data
    user_data = db.get_user_data(user_id)
    
    # lấy thông tin cuộc hội thoại hiện tại for compatibility
    current_conv = db.get_current_conversation(user_id)
    conversations = db.get_conversations(user_id)
    
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
    
    # Get or create current conversation
    current_conv = db.get_current_conversation(user_id)
    if not current_conv:
        # Create new conversation if none exists
        title = question[:50] + "..." if len(question) > 50 else question
        current_conv = db.create_conversation(user_id, title, ai_mode)
    
    return db.add_message(current_conv['id'], user_id, question, answer, ai_mode, metadata)


def get_conversation_history(limit: int = 50) -> List[Dict]:
    """Get conversation history with proper is_current marking"""
    db = get_db()
    user_id = get_user_id()
    print(f"[DEBUG] Getting conversations for user_id: {user_id}")
    conversations = db.get_conversations(user_id, limit)
    print(f"[DEBUG] Found {len(conversations)} conversations")
    return conversations


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


def migrate_session_to_database():
    """Migrate existing session data to database (one-time operation)"""
    if 'user_data' not in session:
        return False
    
    try:
        db = get_db()
        user_id = get_user_id()
        
        db.get_or_create_user(session.get('session_id', user_id))
        
        session_data = session['user_data']
        
        preferences = session_data.get('preferences', {})
        deadlines = session_data.get('deadlines', {})
        schedule = session_data.get('schedule', {})
        
        if preferences or deadlines or schedule:
            db.save_user_data(user_id, preferences, deadlines, schedule)
        
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
