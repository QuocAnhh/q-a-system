import re
import requests
from datetime import datetime
from config import Config
from db_session_manager import get_user_data, save_user_data


def handle_deadline_commands(question, user_data):
    """Xử lý các lệnh liên quan đến deadline"""
    q = question.strip()
    deadlines = user_data.get('deadlines', {})
    
    #xem tất cả deadline
    if re.match(r'^deadline$|xem deadline', q, re.I):
        if not deadlines:
            return {"answer": "Chưa có deadline nào được lưu."}
        
        # sắp xếp theo ngày
        sorted_deadlines = sorted(deadlines.items(), key=lambda x: x[1])
        
        result = "<strong>Danh sách deadline:</strong><br>"
        for subject, date in sorted_deadlines:
            days_left = calculate_days_left(date)
            urgency = get_urgency_icon(days_left)
            status = f"{days_left} ngày nữa" if days_left > 0 else "Đã hết hạn"
            result += f"{urgency} <strong>{subject}</strong>: {date} ({status})<br>"
        
        return {
            "answer": result,
            "suggestions": ["Thêm deadline mới", "Xóa deadline", "Lịch tuần này"]
        }
    
    #add deadline mới
    add_match = re.match(r'^thêm deadline (.+) (\d{4}-\d{2}-\d{2})$', q, re.I)
    if add_match:
        subject = add_match.group(1)
        date = add_match.group(2)
        
        # Validate date
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return {"answer": "Định dạng ngày không hợp lệ. Vui lòng sử dụng YYYY-MM-DD"}
        
        deadlines[subject] = date
        user_data['deadlines'] = deadlines
        save_user_data(user_data)
        
        return {
            "answer": f"Đã lưu deadline cho <strong>{subject}</strong>: <strong>{date}</strong>",
            "suggestions": ["Xem tất cả deadline", "Thêm deadline khác", "Tìm tài liệu " + subject]
        }
    
    # del deadline
    remove_match = re.match(r'^xóa deadline (.+)$', q, re.I)
    if remove_match:
        subject = remove_match.group(1)
        if subject in deadlines:
            del deadlines[subject]
            user_data['deadlines'] = deadlines
            save_user_data(user_data)
            return {"answer": f"Đã xóa deadline cho <strong>{subject}</strong>"}
        else:
            return {"answer": f"Không tìm thấy deadline cho <strong>{subject}</strong>"}
    
    return {"answer": "Lệnh deadline không hợp lệ. Ví dụ: 'thêm deadline Toán 2024-12-25' hoặc 'deadline'"}


def handle_calendar_commands(question, user_data):
    """Xử lý các lệnh liên quan đến lịch"""
    q = question.lower().strip()
    
    if 'hôm nay' in q or 'today' in q:
        return get_today_schedule(user_data)
    
    if 'tuần này' in q or 'this week' in q:
        return get_week_schedule(user_data)
    
    # add lịch học
    add_schedule_match = re.match(r'thêm lịch học (.+) (thứ \d+|chủ nhật) (.+)', q, re.I)
    if add_schedule_match:
        subject = add_schedule_match.group(1)
        day_of_week = add_schedule_match.group(2)
        time = add_schedule_match.group(3)
        
        return add_recurring_schedule(subject, day_of_week, time, user_data)
    
    return {"answer": "Lệnh lịch không hợp lệ. Ví dụ: 'lịch hôm nay', 'thêm lịch học Vật lý thứ 2 8:00'"}


def handle_document_search(question, user_data):
    """Xử lý tìm kiếm tài liệu"""
    # abtract từ khóa tìm kiếm
    search_query = re.sub(r'tìm|tài liệu|về|cho|môn|học', '', question, flags=re.I).strip()
    
    if not search_query:
        return {"answer": "Vui lòng cho biết bạn muốn tìm tài liệu về chủ đề gì?"}
    
    # Tạo link tìm kiếm
    encoded_query = requests.utils.quote(search_query)
    
    result = f"<strong>Tài liệu về \"{search_query}\":</strong><br><br>"
    
    # Google Custom Search
    search_results = search_documents_google(search_query)
    if search_results:
        result += "<strong>Kết quả tìm kiếm:</strong><br>"
        for i, item in enumerate(search_results[:3], 1):
            result += f"{i}. <a href='{item['link']}' target='_blank'>{item['title']}</a><br>"
            if 'snippet' in item:
                result += f"   <em>{item['snippet'][:100]}...</em><br>"
        result += "<br>"
    
    result += "<strong>Tài nguyên học tập miễn phí:</strong><br>"
    result += f"<a href='https://scholar.google.com/scholar?q={encoded_query}' target='_blank'>Google Scholar</a> - Bài báo khoa học<br>"
    result += f"<a href='https://www.youtube.com/results?search_query={encoded_query}' target='_blank'>YouTube</a> - Video hướng dẫn<br>"
    result += f"<a href='https://www.coursera.org/search?query={encoded_query}' target='_blank'>Coursera</a> - Khóa học trực tuyến<br>"
    result += f"<a href='https://www.edx.org/search?q={encoded_query}' target='_blank'>edX</a> - Khóa học miễn phí<br>"
    result += f"<a href='https://github.com/search?q={encoded_query}&type=repositories' target='_blank'>GitHub</a> - Code và dự án<br>"
    result += f"<a href='https://www.khanacademy.org/search?page_search_query={encoded_query}' target='_blank'>Khan Academy</a> - Bài giảng miễn phí<br>"
    
    # check deadline liên quan
    deadlines = user_data.get('deadlines', {})
    related_deadlines = []
    
    for subject, date in deadlines.items():
        if (search_query.lower() in subject.lower() or 
            subject.lower() in search_query.lower()):
            related_deadlines.append((subject, date))
    
    if related_deadlines:
        result += "<br><strong>Deadline liên quan:</strong><br>"
        for subject, date in related_deadlines:
            days_left = calculate_days_left(date)
            status = f"{days_left} ngày nữa" if days_left > 0 else "Đã hết hạn"
            result += f"{subject}: {date} ({status})<br>"
    
    suggestions = [
        f"Thêm deadline {search_query}",
        "Tìm video YouTube",
        "Xem lịch học"
    ]
    
    return {
        "answer": result,
        "suggestions": suggestions
    }


def search_documents_google(query):
    """Tìm kiếm tài liệu qua Google Custom Search API"""
    try:
        api_key = Config.GOOGLE_CONFIG['api_key']
        search_engine_id = Config.GOOGLE_CONFIG['search_engine_id']
        
        if api_key == 'YOUR_GOOGLE_API_KEY':
            return []  # API key chưa được cấu hình
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': f"{query} filetype:pdf OR site:youtube.com OR site:coursera.org OR site:edx.org",
            'num': 5
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data.get('items', [])
        
    except Exception as e:
        print(f"Error in Google Search API: {e}")
        return []


def get_today_schedule(user_data):
    """Lấy lịch hôm nay"""
    schedule = user_data.get('schedule', {})
    today = datetime.now().strftime('%A').lower()
    
    today_events = schedule.get(today, [])
    
    if not today_events:
        return {
            "answer": "Hôm nay bạn không có lịch học nào được lưu trong hệ thống.",
            "suggestions": ["Thêm lịch học", "Xem lịch tuần", "Xem deadline"]
        }
    
    result = "<strong>Lịch hôm nay:</strong><br>"
    for event in today_events:
        result += f"{event['time']} - {event['subject']}<br>"
    
    return {
        "answer": result,
        "suggestions": ["Thêm lịch học", "Xem deadline", "Tìm tài liệu"]
    }


def get_week_schedule(user_data):
    """Lấy lịch tuần này"""
    schedule = user_data.get('schedule', {})
    
    if not schedule:
        return {
            "answer": "Bạn chưa có lịch học nào được lưu trong hệ thống.",
            "suggestions": ["Thêm lịch học", "Xem deadline"]
        }
    
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_names = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
    
    result = "<strong>Lịch tuần này:</strong><br>"
    
    for day, day_name in zip(days, day_names):
        events = schedule.get(day, [])
        if events:
            result += f"<br><strong>{day_name}:</strong><br>"
            for event in events:
                result += f"{event['time']} - {event['subject']}<br>"
    
    return {
        "answer": result,
        "suggestions": ["Thêm lịch học", "Xem deadline", "Lịch hôm nay"]
    }


def add_recurring_schedule(subject, day_of_week, time, user_data):
    """Thêm lịch học định kỳ"""
    schedule = user_data.get('schedule', {})
    
    # Convert day name to English key
    day_mapping = {
        'thứ 2': 'monday', 'thứ 3': 'tuesday', 'thứ 4': 'wednesday',
        'thứ 5': 'thursday', 'thứ 6': 'friday', 'thứ 7': 'saturday',
        'chủ nhật': 'sunday'
    }
    
    day_key = day_mapping.get(day_of_week.lower())
    if not day_key:
        return {"answer": "Ngày trong tuần không hợp lệ"}
    
    if day_key not in schedule:
        schedule[day_key] = []
    
    # Check if already exists
    for event in schedule[day_key]:
        if event['subject'] == subject and event['time'] == time:
            return {"answer": f"Lịch học {subject} vào {day_of_week} lúc {time} đã tồn tại"}
    
    schedule[day_key].append({
        'subject': subject,
        'time': time,
        'type': 'recurring'
    })
    
    user_data['schedule'] = schedule
    save_user_data(user_data)
    
    return {
        "answer": f"Đã thêm lịch học <strong>{subject}</strong> vào <strong>{day_of_week}</strong> lúc <strong>{time}</strong>",
        "suggestions": ["Xem lịch tuần", "Thêm deadline", f"Tìm tài liệu {subject}"]
    }


def calculate_days_left(date_str):
    """Tính số ngày còn lại đến deadline"""
    try:
        deadline = datetime.strptime(date_str, '%Y-%m-%d')
        today = datetime.now()
        delta = deadline - today
        return delta.days
    except ValueError:
        return 0


def get_urgency_icon(days_left):
    """Lấy icon theo mức độ khẩn cấp"""
    if days_left <= 0:
        return '🔴'
    elif days_left <= 3:
        return '🟠'
    elif days_left <= 7:
        return '🟡'
    else:
        return '🟢'
