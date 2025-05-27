"""
Database management for Project-NLP chatbot
SQLite implementation for conversations, messages, and user data
"""
import sqlite3
import json
from datetime import datetime
import uuid
import os
from typing import Dict, List, Optional, Any


class DatabaseManager:
    def __init__(self, db_path: str = "chatbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    session_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    preferences TEXT DEFAULT '{}',
                    deadlines TEXT DEFAULT '{}',
                    schedule TEXT DEFAULT '{}'
                )
            """)
            
            # Conversations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT NOT NULL,
                    ai_mode TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 0,
                    message_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    user_id TEXT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    ai_mode TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations (updated_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages (timestamp)")
            
            conn.commit()
    
    def get_or_create_user(self, session_id: str) -> str:
        """Get existing user or create new one based on session"""
        with self.get_connection() as conn:
            # Try to find existing user
            user = conn.execute(
                "SELECT id FROM users WHERE session_id = ?", 
                (session_id,)
            ).fetchone()
            
            if user:
                # Update last active
                conn.execute(
                    "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?",
                    (user['id'],)
                )
                return user['id']
            else:
                # Create new user
                user_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO users (id, session_id, created_at, last_active) 
                       VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                    (user_id, session_id)
                )
                conn.commit()
                return user_id
    
    def create_conversation(self, user_id: str, title: str, ai_mode: str = None) -> Dict:
        """Create new conversation"""
        conversation_id = str(uuid.uuid4())
        
        with self.get_connection() as conn:
            # Deactivate other conversations
            conn.execute(
                "UPDATE conversations SET is_active = 0 WHERE user_id = ?",
                (user_id,)
            )
            
            # Create new conversation
            conn.execute(
                """INSERT INTO conversations 
                   (id, user_id, title, ai_mode, created_at, updated_at, is_active, message_count)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, 0)""",                (conversation_id, user_id, title, ai_mode)
            )
            conn.commit()
            
            return {
                'id': conversation_id,
                'title': title,
                'ai_mode': ai_mode,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_active': True,
                'message_count': 0,
                'messages': []
            }
    
    def get_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's conversations, correctly marking the active one"""
        with self.get_connection() as conn:
            # First get the active conversation ID
            active_conv = conn.execute(
                "SELECT id FROM conversations WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()
            active_conv_id = active_conv['id'] if active_conv else None
            
            # Get all conversations
            conversations = conn.execute(
                """SELECT * FROM conversations 
                   WHERE user_id = ? 
                   ORDER BY updated_at DESC 
                   LIMIT ?""",
                (user_id, limit)
            ).fetchall()
            
            result = []
            for conv in conversations:
                result.append({
                    'id': conv['id'],
                    'title': conv['title'],
                    'ai_mode': conv['ai_mode'],
                    'created_at': conv['created_at'],
                    'updated_at': conv['updated_at'],
                    'is_current': (conv['id'] == active_conv_id),
                    'message_count': conv['message_count']
                })
            
            return result
    
    def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Dict]:
        """Get specific conversation with messages"""
        with self.get_connection() as conn:
            # Get conversation
            conv = conn.execute(
                """SELECT * FROM conversations 
                   WHERE id = ? AND user_id = ?""",
                (conversation_id, user_id)
            ).fetchone()
            
            if not conv:
                return None
            
            # Get messages
            messages = conn.execute(
                """SELECT * FROM messages 
                   WHERE conversation_id = ? 
                   ORDER BY timestamp ASC""",
                (conversation_id,)
            ).fetchall()
            
            message_list = []
            for msg in messages:
                message_list.append({
                    'id': msg['id'],
                    'question': msg['question'],
                    'answer': msg['answer'],
                    'ai_mode': msg['ai_mode'],
                    'timestamp': msg['timestamp'],
                    'metadata': json.loads(msg['metadata']) if msg['metadata'] else {}
                })
            
            return {
                'id': conv['id'],
                'title': conv['title'],
                'ai_mode': conv['ai_mode'],
                'created_at': conv['created_at'],
                'updated_at': conv['updated_at'],
                'is_current': bool(conv['is_active']),
                'message_count': conv['message_count'],
                'messages': message_list
            }
    
    def switch_conversation(self, conversation_id: str, user_id: str) -> Optional[Dict]:
        """Switch to different conversation"""
        with self.get_connection() as conn:
            # Deactivate all conversations
            conn.execute(
                "UPDATE conversations SET is_active = 0 WHERE user_id = ?",
                (user_id,)
            )
            
            # Activate target conversation
            result = conn.execute(
                "UPDATE conversations SET is_active = 1 WHERE id = ? AND user_id = ?",
                (conversation_id, user_id)
            )
            
            if result.rowcount == 0:
                return None
            
            conn.commit()
            return self.get_conversation(conversation_id, user_id)
    
    def add_message(self, conversation_id: str, user_id: str, question: str, 
                   answer: str, ai_mode: str = None, metadata: Dict = None) -> Dict:
        """Add message to conversation"""
        message_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata else '{}'
        
        with self.get_connection() as conn:
            # Insert message
            conn.execute(
                """INSERT INTO messages 
                   (id, conversation_id, user_id, question, answer, ai_mode, timestamp, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)""",
                (message_id, conversation_id, user_id, question, answer, ai_mode, metadata_json)
            )
            
            # Update conversation
            conn.execute(
                """UPDATE conversations 
                   SET updated_at = CURRENT_TIMESTAMP, 
                       message_count = message_count + 1,
                       ai_mode = COALESCE(?, ai_mode)
                   WHERE id = ?""",
                (ai_mode, conversation_id)
            )
            
            conn.commit()
            
            return {
                'id': message_id,
                'question': question,
                'answer': answer,
                'ai_mode': ai_mode,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete conversation and its messages"""
        with self.get_connection() as conn:
            # Delete messages first
            conn.execute(
                "DELETE FROM messages WHERE conversation_id = ?",
                (conversation_id,)
            )
            
            # Delete conversation
            result = conn.execute(
                "DELETE FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user_id)
            )
            
            conn.commit()
            return result.rowcount > 0
    
    def get_current_conversation(self, user_id: str) -> Optional[Dict]:
        """Get currently active conversation"""
        with self.get_connection() as conn:
            conv = conn.execute(
                """SELECT id FROM conversations 
                   WHERE user_id = ? AND is_active = 1 
                   ORDER BY updated_at DESC LIMIT 1""",
                (user_id,)
            ).fetchone()
            
            if conv:
                return self.get_conversation(conv['id'], user_id)
            return None
    
    def cleanup_old_conversations(self, user_id: str, keep_count: int = 50):
        """Keep only recent conversations"""
        with self.get_connection() as conn:
            # Get conversations to delete
            old_conversations = conn.execute(
                """SELECT id FROM conversations 
                   WHERE user_id = ? 
                   ORDER BY updated_at DESC 
                   LIMIT -1 OFFSET ?""",
                (user_id, keep_count)
            ).fetchall()
            
            for conv in old_conversations:
                self.delete_conversation(conv['id'], user_id)
    
    def get_user_data(self, user_id: str) -> Dict:
        """Get user's preferences, deadlines, schedule"""
        with self.get_connection() as conn:
            user = conn.execute(
                "SELECT preferences, deadlines, schedule FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            
            if user:
                return {
                    'preferences': json.loads(user['preferences']) if user['preferences'] else {},
                    'deadlines': json.loads(user['deadlines']) if user['deadlines'] else {},
                    'schedule': json.loads(user['schedule']) if user['schedule'] else {}
                }
            return {'preferences': {}, 'deadlines': {}, 'schedule': {}}
    
    def save_user_data(self, user_id: str, preferences: Dict = None, 
                      deadlines: Dict = None, schedule: Dict = None):
        """Save user's data"""
        with self.get_connection() as conn:
            updates = []
            params = []
            
            if preferences is not None:
                updates.append("preferences = ?")
                params.append(json.dumps(preferences))
            
            if deadlines is not None:
                updates.append("deadlines = ?")
                params.append(json.dumps(deadlines))
            
            if schedule is not None:
                updates.append("schedule = ?")
                params.append(json.dumps(schedule))
            
            if updates:
                updates.append("last_active = CURRENT_TIMESTAMP")
                params.append(user_id)
                
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, params)
                conn.commit()
    
    def export_all_data(self, user_id: str) -> Dict:
        """Export all user data for debugging/backup"""
        with self.get_connection() as conn:
            # Get user info
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            
            # Get all conversations with messages
            conversations = []
            conv_rows = conn.execute(
                "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            ).fetchall()
            
            for conv in conv_rows:
                messages = conn.execute(
                    "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
                    (conv['id'],)
                ).fetchall()
                
                conversations.append({
                    'id': conv['id'],
                    'title': conv['title'],
                    'ai_mode': conv['ai_mode'],
                    'created_at': conv['created_at'],
                    'updated_at': conv['updated_at'],
                    'is_active': bool(conv['is_active']),
                    'message_count': conv['message_count'],
                    'messages': [dict(msg) for msg in messages]
                })
            
            return {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user_id,
                    'total_conversations': len(conversations),
                    'database_path': self.db_path
                },
                'user_info': dict(user) if user else None,
                'conversations': conversations
            }
    
    def export_to_html(self, user_id: str) -> str:
        """Export chat history to HTML format"""
        data = self.export_all_data(user_id)
        
        html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lịch sử Chat - Copailit AI</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .export-info {{ background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .conversation {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; overflow: hidden; }}
        .conversation-header {{ background: #2196f3; color: white; padding: 15px; }}
        .conversation-title {{ font-size: 18px; font-weight: bold; }}
        .conversation-meta {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
        .messages {{ padding: 0; }}
        .message {{ padding: 15px; border-bottom: 1px solid #eee; }}
        .message:last-child {{ border-bottom: none; }}
        .user-message {{ background: #f8f9fa; }}
        .bot-message {{ background: #fff; }}
        .message-header {{ font-weight: bold; margin-bottom: 8px; color: #1976d2; }}
        .message-content {{ line-height: 1.5; }}
        .timestamp {{ font-size: 12px; color: #666; margin-top: 8px; }}
        .no-conversations {{ text-align: center; color: #666; font-style: italic; padding: 50px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Lịch sử Chat - Copailit AI</h1>
        </div>
        
        <div class="export-info">
            <h3>📊 Thông tin xuất file:</h3>
            <p><strong>Thời gian xuất:</strong> {data['export_info']['timestamp']}</p>
            <p><strong>Tổng số cuộc hội thoại:</strong> {data['export_info']['total_conversations']}</p>
            <p><strong>User ID:</strong> {data['export_info']['user_id']}</p>
        </div>
"""
        
        if not data['conversations']:
            html_content += '<div class="no-conversations">Chưa có cuộc hội thoại nào được lưu.</div>'
        else:
            for i, conv in enumerate(data['conversations'], 1):
                active_badge = "🟢 Đang hoạt động" if conv['is_active'] else ""
                ai_mode_badge = f"🤖 {conv['ai_mode']}" if conv['ai_mode'] else ""
                
                html_content += f"""
        <div class="conversation">
            <div class="conversation-header">
                <div class="conversation-title">#{i}. {conv['title']} {active_badge}</div>
                <div class="conversation-meta">
                    📅 Tạo: {conv['created_at']} | 🔄 Cập nhật: {conv['updated_at']} | 
                    💬 {conv['message_count']} tin nhắn {ai_mode_badge}
                </div>
            </div>
            <div class="messages">
"""
                
                if not conv['messages']:
                    html_content += '<div class="message">Chưa có tin nhắn nào trong cuộc hội thoại này.</div>'
                else:
                    for msg in conv['messages']:
                        # User message
                        html_content += f"""
                <div class="message user-message">
                    <div class="message-header">👤 Bạn:</div>
                    <div class="message-content">{msg['question']}</div>
                    <div class="timestamp">{msg['timestamp']}</div>
                </div>
"""
                        # Bot message
                        html_content += f"""
                <div class="message bot-message">
                    <div class="message-header">🤖 Copailit:</div>
                    <div class="message-content">{msg['answer']}</div>
                    <div class="timestamp">{msg['timestamp']}</div>
                </div>
"""
                
                html_content += """
            </div>
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>"""
        
        return html_content


# Global database instance
db_manager = None

def get_db():
    """Get database manager instance"""
    global db_manager
    if db_manager is None:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'chatbot.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db_manager = DatabaseManager(db_path)
    return db_manager
