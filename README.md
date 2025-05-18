# Project NLP

## Cấu trúc thư mục

- `app/`: Xử lý NLP backend (retriever, generator)
- `api/`: REST API cho frontend (FastAPI)
- `frontend/`: Đặt mã nguồn giao diện tại đây
- `data/`: Dữ liệu

## Chạy backend API

```bash
cd api
uvicorn main:app --reload
```

## Giao tiếp API

- POST `/ask` với JSON: `{ "question": "..." }`
- Nhận về: matched_question, answer, score, generated

## Frontend

- Đặt mã nguồn giao diện ở folder `frontend/`
- Gọi API theo hướng dẫn trên

# Q&A System

This is a simple Q&A system project written in Python.

## Requirements
- Python 3.13.2
- Required dependencies (listed in `requirements.txt`)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/QuocAnhh/q-a-system.git
   ```
2. Navigate to the project directory:
   ```bash
   cd q-a-system
   ```
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the application:
```bash
streamlit run app.py
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.
