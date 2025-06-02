from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta
from calendar_manager import GoogleCalendarManager
from calendar_ai_parser import CalendarAIParser
from db_session_manager import add_message_to_conversation, get_current_conversation
import logging

#logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CalendarIntegration:
    """Main calendar integration class that handles all calendar operations"""
    
    def __init__(self):
        self.calendar_manager = GoogleCalendarManager()
        self.ai_parser = CalendarAIParser()
        
    def process_calendar_request(self, user_id: str, user_message: str) -> Dict[str, Any]:

        
        try:
            # Parse the user message
            parsed_request = self.ai_parser.parse_calendar_request(user_message)
            parsed_request['raw_message'] = user_message
            
            if parsed_request['action'] == 'none' or parsed_request['confidence'] < 0.3:
                return {
                    'success': False,
                    'message': 'Tôi không hiểu yêu cầu lịch của bạn. Hãy thử nói rõ hơn như "Tạo lịch họp ngày mai 9h" hoặc "Đặt deadline dự án ngày 15/12".',
                    'data': None,
                    'action': 'none'
                }
            
            auth_status = self.calendar_manager.check_auth_status(user_id)
            if not auth_status['authenticated']:
                auth_url = self.calendar_manager.get_auth_url(user_id)
                return {
                    'success': False,
                    'message': 'Bạn cần xác thực Google Calendar trước. Nhấn vào link để đăng nhập.',
                    'data': {
                        'auth_url': auth_url,
                        'requires_auth': True
                    },
                    'action': 'auth_required'
                }
            
            action = parsed_request['action']
            
            if action == 'create_event':
                return self._handle_create_event(user_id, parsed_request)
            elif action == 'create_deadline':
                return self._handle_create_deadline(user_id, parsed_request)
            elif action == 'list_events':
                return self._handle_list_events(user_id, parsed_request)
            elif action == 'delete_event':
                return self._handle_delete_event(user_id, parsed_request)
            else:
                return {
                    'success': False,
                    'message': 'Chức năng này chưa được hỗ trợ.',
                    'data': None,
                    'action': 'unsupported'
                }
                
        except Exception as e:
            logger.error(f"Error processing calendar request: {e}")
            return {
                'success': False,
                'message': 'Có lỗi xảy ra khi xử lý yêu cầu lịch. Vui lòng thử lại.',
                'data': None,
                'action': 'error'
            }
    
    def _handle_create_event(self, user_id: str, parsed_request: Dict) -> Dict[str, Any]:
        """Handle creating a new event"""
        
        try:
            # Validate required fields
            if not parsed_request.get('title'):
                return {
                    'success': False,
                    'message': 'Vui lòng cung cấp tên sự kiện.',
                    'data': None,
                    'action': 'validation_error'
                }
            
            if not parsed_request.get('date'):
                return {
                    'success': False,
                    'message': 'Vui lòng cung cấp ngày cho sự kiện.',
                    'data': None,
                    'action': 'validation_error'
                }
            
            # Parse start_time and end_time
            date_str = parsed_request['date']
            time_str = parsed_request.get('time', '09:00')
            duration = parsed_request.get('duration', 60)
            try:
                start_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            except Exception:
                # fallback nếu time_str không đúng định dạng
                start_time = datetime.strptime(date_str, "%Y-%m-%d")
            end_time = start_time + timedelta(minutes=duration)
            title = parsed_request['title']
            description = parsed_request.get('description', '')
            location = parsed_request.get('location', '')
            
            result = self.calendar_manager.create_event(
                user_id,
                title,
                start_time,
                end_time,
                description,
                location
            )
            
            if result['success']:
                # Format response message
                event_time = self._format_datetime(parsed_request['date'], parsed_request.get('time', '09:00'))
                message = f"✅ Đã tạo sự kiện '{parsed_request['title']}' vào {event_time}"
                
                if parsed_request.get('reminder', 15) > 0:
                    message += f"\n🔔 Nhắc nhở trước {parsed_request.get('reminder', 15)} phút"
                
                # Save to conversation
                add_message_to_conversation(parsed_request.get('raw_message', ''), message, ai_mode='calendar', metadata={'calendar_action': 'create_event'})
                conversation = get_current_conversation()
                
                return {
                    'success': True,
                    'message': message,
                    'data': {
                        'event_id': result['event_id'],
                        'event_link': result.get('event_link'),
                        'event_details': {
                            'title': title,
                            'start_time': start_time.isoformat(),
                            'end_time': end_time.isoformat(),
                            'description': description,
                            'location': location
                        }
                    },
                    'action': 'create_event',
                    'conversation': conversation
                }
            else:
                return {
                    'success': False,
                    'message': f"Không thể tạo sự kiện: {result.get('message', 'Unknown error')}",
                    'data': None,
                    'action': 'create_event_failed'
                }
                
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {
                'success': False,
                'message': 'Có lỗi xảy ra khi tạo sự kiện.',
                'data': None,
                'action': 'error'
            }
    
    def _handle_create_deadline(self, user_id: str, parsed_request: Dict) -> Dict[str, Any]:
        """Handle creating a deadline (all-day event)"""
        
        try:
            # Validate required fields
            if not parsed_request.get('title'):
                return {
                    'success': False,
                    'message': 'Vui lòng cung cấp tên deadline.',
                    'data': None,
                    'action': 'validation_error'
                }
            
            if not parsed_request.get('date'):
                return {
                    'success': False,
                    'message': 'Vui lòng cung cấp ngày deadline.',
                    'data': None,
                    'action': 'validation_error'
                }
            
            # tạo deadline
            deadline_data = {
                'title': f"📅 DEADLINE: {parsed_request['title']}",
                'date': parsed_request['date'],
                'description': parsed_request.get('description', f"Deadline cho: {parsed_request['title']}"),
                'reminder_minutes': parsed_request.get('reminder', 60)  # nhắc nhở trước 1 tiếng
            }
            
            result = self.calendar_manager.create_deadline(user_id, deadline_data)
            
            if result['success']:
                # Format response message
                deadline_date = self._format_date(parsed_request['date'])
                message = f"⏰ Đã tạo deadline '{parsed_request['title']}' vào {deadline_date}"
                
                if parsed_request.get('reminder', 60) > 0:
                    reminder_text = self._format_reminder_time(parsed_request.get('reminder', 60))
                    message += f"\n🔔 Nhắc nhở trước {reminder_text}"
                
                # Save to conversation
                add_message_to_conversation(parsed_request.get('raw_message', ''), message, ai_mode='calendar', metadata={'calendar_action': 'create_deadline'})
                conversation = get_current_conversation()
                
                return {
                    'success': True,
                    'message': message,
                    'data': {
                        'event_id': result['event_id'],
                        'event_link': result.get('event_link'),
                        'deadline_details': deadline_data
                    },
                    'action': 'create_deadline',
                    'conversation': conversation
                }
            else:
                return {
                    'success': False,
                    'message': f"Không thể tạo deadline: {result['error']}",
                    'data': None,
                    'action': 'create_deadline_failed'
                }
                
        except Exception as e:
            logger.error(f"Error creating deadline: {e}")
            return {
                'success': False,
                'message': 'Có lỗi xảy ra khi tạo deadline.',
                'data': None,
                'action': 'error'
            }
    
    def _handle_list_events(self, user_id: str, parsed_request: Dict) -> Dict[str, Any]:
        """Handle listing upcoming events"""
        
        try:
            # Get upcoming events (default: next 7 days)
            days_ahead = 7
            result = self.calendar_manager.get_upcoming_events(user_id, days_ahead)
            
            if result['success']:
                events = result['events']
                
                if not events:
                    return {
                        'success': True,
                        'message': f"📅 Bạn không có sự kiện nào trong {days_ahead} ngày tới.",
                        'data': {'events': []},
                        'action': 'list_events'
                    }
                
                # Format events list
                message = f"📅 Lịch của bạn trong {days_ahead} ngày tới:\n\n"
                
                for i, event in enumerate(events[:10], 1):  # Limit to 10 events
                    start_time = event.get('start_time', 'Không xác định')
                    title = event.get('title', 'Không có tiêu đề')
                    
                    # Format datetime
                    if start_time != 'Không xác định':
                        try:
                            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            formatted_time = dt.strftime('%d/%m/%Y %H:%M')
                        except:
                            formatted_time = start_time
                    else:
                        formatted_time = start_time
                    
                    message += f"{i}. **{title}**\n"
                    message += f"   📅 {formatted_time}\n"
                    
                    if event.get('description'):
                        desc = event['description'][:100] + ('...' if len(event['description']) > 100 else '')
                        message += f"   📝 {desc}\n"
                    
                    message += "\n"
                
                if len(events) > 10:
                    message += f"... và {len(events) - 10} sự kiện khác"
                
                return {
                    'success': True,
                    'message': message,
                    'data': {
                        'events': events,
                        'total_count': len(events)
                    },
                    'action': 'list_events'
                }
            else:
                return {
                    'success': False,
                    'message': f"Không thể lấy danh sách sự kiện: {result['error']}",
                    'data': None,
                    'action': 'list_events_failed'
                }
                
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            return {
                'success': False,
                'message': 'Có lỗi xảy ra khi lấy danh sách sự kiện.',
                'data': None,
                'action': 'error'
            }
    
    def _handle_delete_event(self, user_id: str, parsed_request: Dict) -> Dict[str, Any]:
        """Handle deleting an event (basic implementation)"""
        
        return {
            'success': False,
            'message': 'Chức năng xóa sự kiện chưa được triển khai. Bạn có thể xóa trực tiếp trong Google Calendar.',            'data': None,
            'action': 'not_implemented'
        }
    
    def handle_auth_callback(self, user_id: str, auth_code: str) -> Dict[str, Any]:
        """Handle OAuth callback after user authorizes"""
        
        try:
            result = self.calendar_manager.handle_callback(user_id, auth_code)
            
            if result['success']:
                return {
                    'success': True,
                    'message': '✅ Xác thực Google Calendar thành công! Bây giờ bạn có thể sử dụng các chức năng lịch.',
                    'data': {
                        'authenticated': True,
                        'user_email': result.get('user_email')
                    },
                    'action': 'auth_success'
                }
            else:
                return {
                    'success': False,
                    'message': f"Xác thực thất bại: {result['error']}",
                    'data': None,
                    'action': 'auth_failed'
                }
                
        except Exception as e:
            logger.error(f"Auth callback error: {e}")
            return {
                'success': False,
                'message': 'Có lỗi xảy ra trong quá trình xác thực.',
                'data': None,
                'action': 'auth_error'            }
    
    def get_auth_status(self, user_id: str) -> Dict[str, Any]:
        """Get current authentication status for user"""
        
        try:
            auth_status = self.calendar_manager.check_auth_status(user_id)
            
            # Return format that frontend expects
            if auth_status['authenticated']:
                return {
                    'authenticated': True,
                    'status': 'ready',
                    'message': 'Google Calendar đã kết nối và sẵn sàng',
                    'user_email': auth_status.get('user_email'),
                    'expires_at': auth_status.get('expires_at')
                }
            else:
                # Get auth URL for user to authenticate
                auth_url_result = self.calendar_manager.get_auth_url(user_id)
                auth_url = auth_url_result.get('auth_url', '') if auth_url_result.get('success') else ''
                
                return {
                    'authenticated': False,
                    'status': 'not_authenticated',
                    'message': 'Bạn chưa xác thực Google Calendar. Vui lòng kết nối để sử dụng chức năng lịch.',
                    'auth_url': auth_url
                }
                
        except Exception as e:
            logger.error(f"Error checking auth status: {e}")
            return {
                'authenticated': False,
                'status': 'error',
                'message': 'Không thể kiểm tra trạng thái xác thực.',
                'auth_url': ''
            }
    
    def _format_datetime(self, date_str: str, time_str: str) -> str:
        """Format date and time for display"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%d/%m/%Y')
            
            # Format time
            if time_str:
                time_parts = time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                formatted_time = f"{hour:02d}:{minute:02d}"
                return f"{formatted_date} lúc {formatted_time}"
            else:
                return formatted_date
        except:
            return f"{date_str} {time_str}"
    
    def _format_date(self, date_str: str) -> str:
        """Format date for display"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%d/%m/%Y')
        except:
            return date_str
    
    def _format_reminder_time(self, minutes: int) -> str:
        """Format reminder time for display"""
        if minutes < 60:
            return f"{minutes} phút"
        elif minutes < 1440:  # Less than 24 hours
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} giờ"
            else:
                return f"{hours} giờ {remaining_minutes} phút"
        else:  # Days
            days = minutes // 1440
            remaining_hours = (minutes % 1440) // 60
            if remaining_hours == 0:
                return f"{days} ngày"
            else:
                return f"{days} ngày {remaining_hours} giờ"
