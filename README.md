# Project NLP

## Cấu trúc thư mục
- `app/`: Xử lý NLP backend (retriever, generator)
- `api`: REST API cho frontend (fastapi)
- `data/`: Dữ liệu

## Yêu cầu
- Python 3.13+
- Các thư viện trong `requirements.txt`
- Đã đăng nhập HuggingFace CLI và có quyền truy cập model BkAI

## Cài đặt
```bash
git clone https://github.com/QuocAnhh/q-a-system.git
cd q-a-system
pip install -r requirements.txt
huggingface-cli login  # Đăng nhập để tải model trên huggingface (model gate)
```

## Chạy ứng dụng hỏi đáp
```bash
streamlit run app\app.py
python -m streamlit run app\app.py
```

## Mô hình sử dụng
- Truy xuất: SentenceTransformer (có thể đổi sang model tiếng Việt)
- Sinh câu trả lời: `bkai-foundation-models/vietnamese-llama2-7b-40GB` (đa lĩnh vực, tiếng Việt)

## Ghi chú
- Lần đầu chạy sẽ tự động tải model từ HuggingFace.
- Nếu gặp lỗi quyền truy cập model, hãy "Request access" trên trang model HuggingFace và kiểm tra lại token

## Đóng góp
Mọi đóng góp đều được hoan nghênh!
