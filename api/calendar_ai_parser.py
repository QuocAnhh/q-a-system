import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import openai
from config import Config

class CalendarAIParser:
    """AI parser for natural language calendar requests"""
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
        
    def parse_calendar_request(self, user_message: str) -> Dict:
        """
        Parse user message to extract calendar-related information
        Returns: {
            'action': 'create_event' | 'create_deadline' | 'list_events' | 'delete_event' | 'none',
            'title': str,
            'date': str (ISO format),
            'time': str (HH:MM),
            'description': str,
            'duration': int (minutes),
            'reminder': int (minutes before),
            'confidence': float (0-1)
        }
        """
        
        # Quick keyword detection first
        calendar_keywords = [
            'lịch', 'deadline', 'hẹn', 'cuộc họp', 'sự kiện', 'nhắc nhở', 
            'meeting', 'event', 'reminder', 'schedule', 'appointment',
            'tạo lịch', 'đặt lịch', 'thêm lịch', 'lên lịch'
        ]
        
        if not any(keyword in user_message.lower() for keyword in calendar_keywords):
            return {'action': 'none', 'confidence': 0.0}
        try:
            # Use AI to parse the request
            prompt = f"""
Phân tích tin nhắn người dùng và trích xuất thông tin lịch. Trả về JSON với format:
{{
    "action": "create_event|create_deadline|list_events|delete_event|none",
    "title": "tên sự kiện",
    "date": "YYYY-MM-DD", 
    "time": "HH:MM",
    "description": "mô tả chi tiết",
    "duration": số_phút,
    "reminder": số_phút_trước_khi_nhắc,
    "confidence": 0.0-1.0
}}

Tin nhắn: "{user_message}"

Lưu ý:
- Nếu không có thời gian cụ thể, mặc định là 09:00
- Nếu không có ngày cụ thể, mặc định là ngày mai
- Duration mặc định là 60 phút
- Reminder mặc định là 15 phút trước
- Nếu chỉ đề cập "deadline" không có thời gian, tạo event cả ngày
- Confidence cao nếu có đầy đủ thông tin ngày giờ
"""
            
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            import json
            try:
                # Find JSON in the response
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = ai_response[json_start:json_end]
                    parsed_data = json.loads(json_str)
                else:
                    parsed_data = json.loads(ai_response)
                
                # Validate and enhance the parsed data
                result = self._validate_and_enhance_parsed_data(parsed_data, user_message)
                return result
                
            except json.JSONDecodeError:
                # Fallback to rule-based parsing
                return self._fallback_rule_based_parsing(user_message)
                
        except Exception as e:
            print(f"AI parsing error: {e}")
            # Fallback to rule-based parsing
            return self._fallback_rule_based_parsing(user_message)
    
    def _validate_and_enhance_parsed_data(self, parsed_data: Dict, original_message: str) -> Dict:
        """Validate and enhance AI parsed data"""
        
        # Default values
        defaults = {
            'action': 'none',
            'title': '',
            'date': '',
            'time': '09:00',
            'description': '',
            'duration': 60,
            'reminder': 15,
            'confidence': 0.0
        }
        
        # Merge with defaults
        result = {**defaults, **parsed_data}
        
        # Validate action
        valid_actions = ['create_event', 'create_deadline', 'list_events', 'delete_event', 'none']
        if result['action'] not in valid_actions:
            result['action'] = 'none'
        
        # Auto-detect action if not specified correctly
        if result['action'] == 'none':
            message_lower = original_message.lower()
            if any(word in message_lower for word in ['tạo', 'đặt', 'thêm', 'lên lịch', 'create']):
                if 'deadline' in message_lower:
                    result['action'] = 'create_deadline'
                else:
                    result['action'] = 'create_event'
            elif any(word in message_lower for word in ['xem', 'hiện', 'list', 'show']):
                result['action'] = 'list_events'
            elif any(word in message_lower for word in ['xóa', 'hủy', 'delete', 'cancel']):
                result['action'] = 'delete_event'
        
        # Validate and fix date
        if result['date']:
            result['date'] = self._normalize_date(result['date'], original_message)
        else:
            # Default to tomorrow if creating event
            if result['action'] in ['create_event', 'create_deadline']:
                tomorrow = datetime.now() + timedelta(days=1)
                result['date'] = tomorrow.strftime('%Y-%m-%d')
        
        # Validate time format
        if result['time']:
            result['time'] = self._normalize_time(result['time'])
        
        # Generate title if missing
        if not result['title'] and result['action'] in ['create_event', 'create_deadline']:
            result['title'] = self._extract_title_from_message(original_message)
        
        # Adjust confidence based on completeness
        if result['action'] != 'none':
            completeness = 0.0
            if result['title']: completeness += 0.3
            if result['date']: completeness += 0.3
            if result['time']: completeness += 0.2
            if result['description']: completeness += 0.2
            
            result['confidence'] = max(result['confidence'], completeness)
        
        return result
    
    def _fallback_rule_based_parsing(self, user_message: str) -> Dict:
        """Fallback rule-based parsing when AI fails"""
        
        message_lower = user_message.lower()
        
        # Detect action
        action = 'none'
        if any(word in message_lower for word in ['tạo', 'đặt', 'thêm', 'lên lịch', 'create', 'add']):
            if 'deadline' in message_lower:
                action = 'create_deadline'
            else:
                action = 'create_event'
        elif any(word in message_lower for word in ['xem', 'hiện', 'list', 'show']):
            action = 'list_events'
        elif any(word in message_lower for word in ['xóa', 'hủy', 'delete', 'cancel']):
            action = 'delete_event'
        
        # Extract basic information
        title = self._extract_title_from_message(user_message)
        date = self._extract_date_from_message(user_message)
        time = self._extract_time_from_message(user_message)
        
        return {
            'action': action,
            'title': title,
            'date': date,
            'time': time or '09:00',
            'description': user_message[:200],  # Use message as description
            'duration': 60,
            'reminder': 15,
            'confidence': 0.6 if action != 'none' else 0.0
        }
    
    def _extract_title_from_message(self, message: str) -> str:
        """Extract event title from message"""
        # Remove common calendar keywords and get the main content
        keywords_to_remove = [
            'tạo lịch', 'đặt lịch', 'thêm lịch', 'lên lịch', 'nhắc nhở',
            'create', 'schedule', 'add', 'meeting', 'event', 'deadline'
        ]
        
        cleaned_message = message
        for keyword in keywords_to_remove:
            cleaned_message = re.sub(keyword, '', cleaned_message, flags=re.IGNORECASE)
        
        # Remove date/time patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{1,2}:\d{2}',
            r'ngày mai', r'hôm nay', r'tuần sau'
        ]
        
        for pattern in date_patterns:
            cleaned_message = re.sub(pattern, '', cleaned_message, flags=re.IGNORECASE)
        
        # Clean and extract meaningful words
        title = re.sub(r'[^\w\s]', ' ', cleaned_message).strip()
        title = re.sub(r'\s+', ' ', title)
        
        if len(title) > 50:
            title = title[:50] + '...'
        
        return title or 'Sự kiện mới'
    
    def _extract_date_from_message(self, message: str) -> str:
        """Extract date from message"""
        try:
            message_lower = message.lower()
            today = datetime.now()
            
            # Check for relative dates
            if any(word in message_lower for word in ['hôm nay', 'today']):
                return today.strftime('%Y-%m-%d')
            elif any(word in message_lower for word in ['ngày mai', 'tomorrow']):
                return (today + timedelta(days=1)).strftime('%Y-%m-%d')
            elif any(word in message_lower for word in ['ngày kia', 'day after tomorrow']):
                return (today + timedelta(days=2)).strftime('%Y-%m-%d')
            elif 'tuần sau' in message_lower or 'next week' in message_lower:
                return (today + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Check for specific dates (DD/MM or DD-MM)
            import re
            date_pattern = r'(\d{1,2})[/-](\d{1,2})'
            match = re.search(date_pattern, message)
            if match:
                day, month = match.groups()
                year = today.year
                try:
                    date_obj = datetime(year, int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    pass
            
            # Check for day names (thứ hai, thứ ba,...)
            day_mapping = {
                'chủ nhật': 6, 'sunday': 6,
                'thứ hai': 0, 'monday': 0,
                'thứ ba': 1, 'tuesday': 1,
                'thứ tư': 2, 'wednesday': 2,
                'thứ năm': 3, 'thursday': 3,
                'thứ sáu': 4, 'friday': 4,
                'thứ bảy': 5, 'saturday': 5
            }
            
            for day_name, weekday in day_mapping.items():
                if day_name in message_lower:
                    days_ahead = weekday - today.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = today + timedelta(days=days_ahead)
                    return target_date.strftime('%Y-%m-%d')
            
            # mặc định là ngày mai nếu không tìm thấy ngày cụ thể
            return (today + timedelta(days=1)).strftime('%Y-%m-%d')
            
        except Exception:
            return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    def _extract_time_from_message(self, message: str) -> str:
        """Extract time from message"""
        try:
            import re
            
            # Pattern for time like 9h, 14h30, 9:30, etc.
            time_patterns = [
                r'(\d{1,2})h(\d{2})',  # 9h30
                r'(\d{1,2})h',         # 9h
                r'(\d{1,2}):(\d{2})',  # 9:30
                r'(\d{1,2})\s*giờ\s*(\d{2})',  # 9 giờ 30
                r'(\d{1,2})\s*giờ',    # 9 giờ
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, message)
                if match:
                    groups = match.groups()
                    hour = int(groups[0])
                    minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                    
                    # Handle AM/PM
                    if 'pm' in message.lower() or 'chiều' in message.lower() or 'tối' in message.lower():
                        if hour < 12:
                            hour += 12
                    elif 'am' in message.lower() or 'sáng' in message.lower():
                        if hour == 12:
                            hour = 0
                    
                    return f"{hour:02d}:{minute:02d}"
            
            # Look for common time expressions
            if 'sáng' in message.lower():
                return "09:00"
            elif 'trưa' in message.lower():
                return "12:00"
            elif 'chiều' in message.lower():
                return "14:00"
            elif 'tối' in message.lower():
                return "19:00"
            
            # Default time
            return "09:00"
            
        except Exception:
            return "09:00"

    def _normalize_date(self, date_str: str, original_message: str) -> str:
        """Normalize date string to YYYY-MM-DD format"""
        if not date_str:
            return ''
        
        # If already in correct format
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str
        
        # Try to parse various formats
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-m-%Y', '%m/%d/%Y']
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # If parsing fails, try to extract from original message
        return self._extract_date_from_message(original_message)
    
    def _normalize_time(self, time_str: str) -> str:
        """Normalize time string to HH:MM format"""
        if not time_str:
            return '09:00'
        
        # Remove spaces and common suffixes
        time_str = time_str.replace(' ', '').lower()
        time_str = re.sub(r'[ap]m$', '', time_str)
        
        # If already in HH:MM format
        if re.match(r'\d{1,2}:\d{2}', time_str):
            parts = time_str.split(':')
            hour = int(parts[0])
            minute = int(parts[1])
            
            # Validate range
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
        
        # Try to extract time
        time_match = re.search(r'(\d{1,2})', time_str)
        if time_match:
            hour = int(time_match.group(1))
            if 0 <= hour <= 23:
                return f"{hour:02d}:00"
        
        return '09:00'  # Default fallback
