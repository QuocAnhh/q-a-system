import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
from config import Config

class GoogleCalendarManager:
    def __init__(self):
        self.service = None
        self.config = Config()
        self.credentials_file = self.config.CALENDAR_SETTINGS['credentials_file']
        self.tokens_dir = self.config.CALENDAR_SETTINGS['tokens_dir']
        self.scopes = self.config.GOOGLE_CALENDAR_CONFIG['scopes']
        self.redirect_uri = self.config.GOOGLE_CALENDAR_CONFIG['redirect_uri']
        
        # Tạo thư mục tokens nếu chưa có
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def check_auth_status(self, user_id: str) -> Dict:
        """Kiểm tra trạng thái authentication của user"""
        token_file = os.path.join(self.tokens_dir, f'token_{user_id}.pickle')
        
        if os.path.exists(token_file):
            try:
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
                    
                if creds and creds.valid:
                    return {
                        'authenticated': True, 
                        'status': 'ready',
                        'message': 'Google Calendar đã kết nối và sẵn sàng'
                    }
                elif creds and creds.expired and creds.refresh_token:
                    return {
                        'authenticated': True, 
                        'status': 'need_refresh',
                        'message': 'Token hết hạn, cần làm mới'
                    }
                else:
                    return {
                        'authenticated': False, 
                        'status': 'need_auth',
                        'message': 'Cần xác thực lại Google Calendar'
                    }
            except Exception as e:
                self.logger.error(f"Error checking auth status: {e}")
                return {
                    'authenticated': False, 
                    'status': 'need_auth',
                    'message': 'Token không hợp lệ, cần xác thực mới'
                }
        else:
            return {
                'authenticated': False, 
                'status': 'need_auth',
                'message': 'Chưa kết nối Google Calendar'
            }
    def get_auth_url(self, user_id: str, redirect_uri: str = None) -> Dict:
        """Tạo URL để user authorize Google Calendar"""
        try:
            if not os.path.exists(self.credentials_file):
                return {
                    'success': False,
                    'message': 'Thiếu file credentials.json. Vui lòng liên hệ admin.'
                }
            
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.scopes)
            
            if redirect_uri:
                flow.redirect_uri = redirect_uri
            else:
                flow.redirect_uri = self.redirect_uri
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id,
                prompt='consent'  # Force consent screen to get refresh token
            )
            
            return {
                'success': True,
                'auth_url': auth_url,
                'message': 'Vui lòng click vào link để kết nối Google Calendar'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating auth URL: {e}")
            return {
                'success': False,
                'message': f'Lỗi tạo auth URL: {str(e)}'
            }
    
    def handle_callback(self, user_id: str, authorization_code: str, redirect_uri: str = None) -> Dict:
        """Xử lý callback sau khi user authorize"""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.scopes)
            
            if redirect_uri:
                flow.redirect_uri = redirect_uri
            else:
                flow.redirect_uri = self.redirect_uri
            
            flow.fetch_token(code=authorization_code)
            creds = flow.credentials
            
            # Lưu token cho user cụ thể
            token_file = os.path.join(self.tokens_dir, f'token_{user_id}.pickle')
            
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            
            self.logger.info(f"Successfully saved credentials for user {user_id}")
            
            return {
                'success': True,
                'message': 'Kết nối Google Calendar thành công! Bây giờ bạn có thể tạo lịch bằng chat.'
            }
            
        except Exception as e:
            self.logger.error(f"Error handling callback: {e}")
            return {
                'success': False,
                'message': f'Lỗi xử lý callback: {str(e)}'
            }
    
    def authenticate_user(self, user_id: str) -> bool:
        """Authenticate specific user và setup service"""
        token_file = os.path.join(self.tokens_dir, f'token_{user_id}.pickle')
        creds = None
        
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed token
                    with open(token_file, 'wb') as token:
                        pickle.dump(creds, token)
                    self.logger.info(f"Refreshed token for user {user_id}")
                except Exception as e:
                    self.logger.error(f"Error refreshing token: {e}")
                    return False
            else:
                return False  # Need new authorization
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            return True
        except Exception as e:
            self.logger.error(f"Error building calendar service: {e}")
            return False
    
    def create_event(self, user_id: str, title: str, start_time: datetime, end_time: datetime, 
                    description: str = "", location: str = "") -> Dict:
        """Create a calendar event"""
        try:
            if not self.authenticate_user(user_id):
                return {
                    'success': False,
                    'message': 'Cần xác thực Google Calendar trước khi tạo sự kiện'
                }
            
            event = {
                'summary': title,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},       # 30 min before
                    ],
                },
            }
            
            created_event = self.service.events().insert(
                calendarId='primary', body=event).execute()
            
            self.logger.info(f"Created event {created_event['id']} for user {user_id}")
            
            return {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink'),
                'message': f'Đã tạo sự kiện: {title}',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error creating event: {e}")
            return {
                'success': False,
                'message': f'Lỗi tạo sự kiện: {str(e)}'
            }
    
    def create_deadline_event(self, user_id: str, title: str, deadline_time: datetime, 
                            description: str = "") -> Dict:
        """Create a deadline event (all-day or specific time)"""
        try:
            if not self.authenticate_user(user_id):
                return {
                    'success': False,
                    'message': 'Cần xác thực Google Calendar trước khi tạo deadline'
                }
            
            # Check if it's all-day deadline (no specific time)
            if deadline_time.hour == 0 and deadline_time.minute == 0:
                # All-day event
                event = {
                    'summary': f"📅 DEADLINE: {title}",
                    'description': f"Deadline: {description}",
                    'start': {
                        'date': deadline_time.date().isoformat(),
                        'timeZone': 'Asia/Ho_Chi_Minh',
                    },
                    'end': {
                        'date': deadline_time.date().isoformat(),
                        'timeZone': 'Asia/Ho_Chi_Minh',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},      # 1 day
                            {'method': 'email', 'minutes': 3 * 24 * 60},  # 3 days
                        ],
                    },
                }
            else:
                # Specific time deadline
                event = {
                    'summary': f"⏰ DEADLINE: {title}",
                    'description': f"Deadline: {description}",
                    'start': {
                        'dateTime': deadline_time.isoformat(),
                        'timeZone': 'Asia/Ho_Chi_Minh',
                    },
                    'end': {
                        'dateTime': (deadline_time + timedelta(hours=1)).isoformat(),
                        'timeZone': 'Asia/Ho_Chi_Minh',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'email', 'minutes': 24 * 60},
                            {'method': 'popup', 'minutes': 60},
                        ],
                    },
                }
            
            created_event = self.service.events().insert(
                calendarId='primary', body=event).execute()
            
            self.logger.info(f"Created deadline {created_event['id']} for user {user_id}")
            
            return {
                'success': True,
                'event_id': created_event['id'],
                'event_link': created_event.get('htmlLink'),
                'message': f'Đã tạo deadline: {title}',
                'deadline_time': deadline_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error creating deadline: {e}")
            return {
                'success': False,
                'message': f'Lỗi tạo deadline: {str(e)}'
            }
    
    def get_upcoming_events(self, user_id: str, days_ahead: int = 7) -> Dict:
        """Lấy danh sách sự kiện sắp tới"""
        try:
            if not self.authenticate_user(user_id):
                return {
                    'success': False,
                    'message': 'Cần xác thực Google Calendar'
                }
            
            now = datetime.now()
            time_max = now + timedelta(days=days_ahead)
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return {
                'success': True,
                'events': events,
                'count': len(events),
                'message': f'Tìm thấy {len(events)} sự kiện trong {days_ahead} ngày tới'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming events: {e}")
            return {
                'success': False,
                'message': f'Lỗi lấy danh sách sự kiện: {str(e)}'
            }
    
    def monitor_quota_usage(self) -> Dict:
        """Monitor Google Calendar API quota usage"""
        try:
            if not self.service:
                return {
                    'quota_status': 'not_authenticated',
                    'message': 'Chưa xác thực'
                }
            
            # Tạo một request đơn giản để check quota
            calendar_list = self.service.calendarList().list(maxResults=1).execute()
            
            self.logger.info(f"Calendar API call successful at {datetime.now()}")
            
            return {
                'quota_status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'message': 'API hoạt động bình thường'
            }
            
        except Exception as e:
            if 'quotaExceeded' in str(e):
                return {
                    'quota_status': 'exceeded',
                    'message': 'Đã vượt quota API, vui lòng thử lại sau'
                }
            else:
                return {
                    'quota_status': 'error',
                    'message': f'Lỗi API: {str(e)}'
                }

# Global instance
calendar_manager = GoogleCalendarManager()
