# NLP Chatbot Project


## Features

### Google Calendar Integration
- **Google Calendar connection**: Xác thực OAuth2 với Google
- **Create events**: Tạo lịch hẹn, cuộc họp từ tin nhắn tự nhiên
- **Deadline management**: Tự động tạo và theo dõi deadline dự án
- **View upcoming events**: Hiển thị sự kiện trong 7 ngày tới

### Database & Storage
- **SQLite Database**: Lưu trữ cuộc hội thoại và metadata
- **Session Management**: Quản lý phiên người dùng và trạng thái
- **Export feature**: Xuất cuộc hội thoại ra HTML


## Project Structure

```
Project-NLP/
├── api/                           # Backend API modules
│   ├── main.py                   # Ứng dụng Flask & REST endpoints
│   ├── config.py                 # Cấu hình & system prompts
│   ├── database.py               # Xử lý database SQLite
│   ├── db_session_manager.py     # Quản lý session database
│   ├── ai_handlers.py            # Xử lý AI cho các môn học
│   ├── openai_manager.py         # Quản lý API OpenAI
│   ├── utils.py                  # Hàm tiện ích
│   ├── calendar_integration.py   # Lớp tích hợp calendar chính
│   ├── calendar_manager.py       # Quản lý Google Calendar API
│   ├── calendar_ai_parser.py     # AI parser cho yêu cầu calendar
│   └── __init__.py
├── frontend/                     # Giao diện web
│   ├── index.html               # HTML chính với sidebar
│   ├── chatbot.js               # JavaScript cho chat & calendar
│   ├── style.css                # Giao diện
│   └── images/                  # Tài sản UI
├── data/                        # Lưu trữ dữ liệu
│   ├── chatbot.db              # Database SQLite
│   ├── credentials.json        # Thông tin Google Calendar
│   ├── calendar_tokens/        # Lưu trữ OAuth tokens
│   └── faq.json               # Dữ liệu FAQ
├── models/                      # Cấu hình mô hình AI
├── requirements.txt             # Thư viện Python
├── .env                        # Biến môi trường
└── README.md                   # File này
```

## Installation

### Prerequisites
- Python 3.13
- OpenAI API key
- Google Cloud Console project with Calendar API enabled

### Setup Steps

1. **Clone the repository**
```bash
git clone https://github.com/QuocAnhh/q-a-system.git
cd Project-NLP
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
Tạo file `.env` ở thư mục gốc:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration
FLASK_ENV=development
DEBUG=True

# Google Calendar Configuration
GOOGLE_CALENDAR_CLIENT_ID=your_google_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=your_google_client_secret
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:5000/calendar/oauth2callback
```

4. **Setup Google Calendar API**
- Vào [Google Cloud Console](https://console.cloud.google.com/)
- Tạo project mới hoặc chọn project có sẵn
- Bật Google Calendar API
- Tạo OAuth 2.0 credentials (Desktop application)
- Tải credentials và lưu thành `data/credentials.json`

5. **Initialize database**
Database SQLite sẽ được tạo tự động khi chạy lần đầu.

## 🚀 Running the Application

```bash
cd api
python main.py
```

Ứng dụng sẽ chạy tại `http://localhost:5000`

## 📡 API Endpoints

### Core Chat
- `POST /chat` - Gửi tin nhắn và nhận phản hồi AI
- `GET /mode` - Lấy chế độ AI hiện tại
- `POST /mode` - Đặt chế độ AI (math, physics, programming, study,...)

### Conversation Management
- `GET /conversations` - Lấy tất cả cuộc hội thoại
- `POST /conversations/new` - Tạo cuộc hội thoại mới
- `GET /conversations/<id>` - Lấy cuộc hội thoại cụ thể
- `DELETE /conversations/<id>` - Xóa cuộc hội thoại
- `POST /conversations/<id>/switch` - Chuyển sang cuộc hội thoại
- `GET /conversations/<id>/export` - Xuất cuộc hội thoại ra HTML

### Google Calendar Integration
- `GET /calendar/auth/status` - Kiểm tra trạng thái xác thực
- `GET /calendar/auth/url` - Lấy URL xác thực OAuth
- `GET /calendar/oauth2callback` - Xử lý callback OAuth
- `POST /calendar/auth/callback` - Xử lý callback xác thực từ frontend
- `POST /calendar/process` - Xử lý yêu cầu calendar ngôn ngữ tự nhiên
- `GET /calendar/events` - Lấy sự kiện sắp tới

### Utility
- `GET /health` - Kiểm tra trạng thái hệ thống
- `GET /` - Trả về giao diện frontend

## 🤖 AI Capabilities

### Supported Subjects
- **Mathematics**: Đại số, giải tích, xác suất thống kê, giải bài tập
- **Physics**: Cơ học, nhiệt động lực học, điện từ học
- **Programming**: Python, JavaScript, thuật toán, debug
- **General Study**: Hỗ trợ nghiên cứu, viết, giải thích

### Calendar Natural Language Processing
AI có thể hiểu và xử lý các yêu cầu về lịch như:
- "Tạo lịch họp ngày mai 9h sáng"
- "Đặt deadline dự án cuối tháng"
- "Nhắc tôi nộp bài tập vào thứ 5"
- "Xem lịch tuần này"

## Configuration

### AI Models
- **Primary**: OpenAI GPT-3.5-turbo
- **Fallback**: GPT-4 cho các yêu cầu phức tạp
- **Calendar AI**: Prompt chuyên biệt cho thao tác calendar

### Database Schema
- **conversations**: Lưu metadata cuộc hội thoại
- **messages**: Lưu từng tin nhắn chat
- **user_sessions**: Theo dõi session và tuỳ chọn người dùng


## Troubleshooting

### Common Issues

1. **Google Calendar not connecting**
   - Kiểm tra file credentials.json có trong thư mục data/
   - Đảm bảo redirect URI trùng với Google Console
   - Đã bật Calendar API

2. **OpenAI API errors**
   - Kiểm tra API key hợp lệ và còn credit
   - Kiểm tra giới hạn và quota

3. **Database errors**
   - Đảm bảo thư mục data/ có quyền ghi
   - Kiểm tra file SQLite không bị lỗi

### Debug Mode
Đặt `DEBUG=True` trong `.env` để xem log lỗi chi tiết.


## Contributing

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/ten-tinh-nang`)
3. Commit thay đổi (`git commit -m 'Add comment'`)
4. Push lên branch (`git push origin feature/ten-tinh-nang`)
5. Tạo Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT models
- Google for Calendar API
- Flask framework community
- Contributors and testers

