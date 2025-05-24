# NLP Chatbot Project

Một chatbot thông minh đa chuyên ngành với khả năng quản lý cuộc hội thoại, hỗ trợ các môn học.

## Features

- **Hỗ trợ AI đa chuyên ngành**: Xử lý chuyên biệt cho các môn học khác nhau
- **Quản lý cuộc hội thoại**: Tạo, chuyển đổi và xóa cuộc hội thoại với lịch sử lưu trữ
- **Giao diện web hiện đại**: Thiết kế responsive với thanh điều hướng bên và chat real-time
- **Kiến trúc modular**: Cấu trúc code rõ ràng, dễ bảo trì với phân tách rõ ràng các chức năng
- **Lưu trữ phiên làm việc**: Tự động lưu và tải cuộc hội thoại

## Project Structure

```
Project-NLP/
├── api/                    # Các module API backend
│   ├── main.py            # Ứng dụng Flask và REST endpoints
│   ├── config.py          # Cấu hình và system prompts
│   ├── session_manager.py # Manage các cuộc hội thoại và phiên làm việc
│   ├── ai_handlers.py     # Xử lý AI cho từng chuyên ngành
│   └── utils.py           # Các hàm tiện ích
├── frontend/              # Giao diện web
│   ├── index.html         # HTML chính với layout sidebar
│   └── chatbot.js         # JavaScript cho quản lý cuộc hội thoại
├── data/                  # Lưu trữ dữ liệu
└── requirements.txt       # Các lib python cần thiết
```

## Requirements

- Python 3.13+
- Flask framework
- OpenAI API key
- Các package được liệt kê trong `requirements.txt`

## Installation

```bash
git clone https://github.com/QuocAnhh/q-a-system.git
cd Project-NLP
pip install -r requirements.txt
```

Tạo file `.env` trong thư mục `api/` và thêm OpenAI API key:
```
OPENAI_API_KEY=sk-xxxx
```

## Running the Application

### Khởi động Backend API
```bash
cd api
python main.py
```
API server sẽ chạy tại `http://localhost:5000`

### Truy cập Frontend
Mở file `frontend/index.html` trong trình duyệt web hoặc chạy qua local server:

```bash
cd frontend
python -m http.server 8080
```
Sau đó truy cập `http://localhost:8080`

## API Endpoints

### Core Chat
- `POST /chat` - Gửi tin nhắn và nhận phản hồi từ AI

### Conversation Management
- `GET /conversations` - Lấy danh sách tất cả cuộc hội thoại
- `POST /conversations/new` - Tạo cuộc hội thoại mới
- `GET /conversations/<id>` - Lấy cuộc hội thoại cụ thể
- `DELETE /conversations/<id>` - Xóa cuộc hội thoại
- `POST /conversations/<id>/switch` - Chuyển sang cuộc hội thoại khác

### Utility
- `GET /mode` - Lấy chế độ AI hiện tại
- `POST /mode` - Thiết lập chế độ AI (math, physics, programming, study)

## AI Models Used

- **Text Generation**: OpenAI GPT-3.5-turbo 

## Key Features

### Conversation Management
- Tạo cuộc hội thoại mới với tiêu đề tự động
- Chuyển đổi giữa nhiều luồng hội thoại
- Xóa cuộc hội thoại không cần thiết
- Lịch sử hội thoại được lưu trữ lâu dài

### Modular Backend
- Split chức năng với các module chuyên biệt
- Manage cấu hình tập trung
- Xử lý lỗi tốt và validation
- Monitor cuộc hội thoại bằng UUID

## Notes

- Cần có OpenAI API key để sử dụng các tính năng AI
- Cuộc hội thoại được tự động lưu và duy trì giữa các phiên làm việc
- Ứng dụng hỗ trợ nhiều cuộc hội thoại đồng thời với ngữ cảnh độc lập
- Hỗ trợ tiếng Việt toàn diện trong giao diện và phản hồi AI

