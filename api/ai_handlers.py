
import openai
from datetime import datetime
from config import SYSTEM_PROMPTS, Config
from session_manager import set_ai_mode, get_ai_mode, add_message_to_conversation

openai.api_key = Config.OPENAI_API_KEY


def call_openai_api(question, system_prompt, subject):
    """Gọi OpenAI API với system prompt"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return f"Hiện tại có lỗi kết nối với AI. Vui lòng thử lại sau. Chi tiết lỗi: {str(e)}"


def handle_ai_question(question):
    """Xử lý câu hỏi AI thông minh"""
    q = question.lower()
    
    if any(keyword in q for keyword in ['toán', 'math', 'công thức', 'tính', 'phương trình']):
        return handle_math_questions(question)
    
    if any(keyword in q for keyword in ['vật lý', 'physics', 'lực', 'năng lượng', 'tốc độ']):
        return handle_physics_questions(question)
    
    if any(keyword in q for keyword in ['hóa học', 'chemistry', 'phản ứng', 'nguyên tố']):
        return handle_chemistry_questions(question)
    
    if any(keyword in q for keyword in ['lập trình', 'programming', 'code', 'python', 'javascript']):
        return handle_programming_questions(question)
    
    if any(keyword in q for keyword in ['lịch sử', 'history', 'việt nam', 'thế giới']):
        return handle_history_questions(question)
    
    if any(keyword in q for keyword in ['tiếng anh', 'english', 'grammar', 'vocabulary']):
        return handle_english_questions(question)
    
    if any(keyword in q for keyword in ['học', 'ôn thi', 'thi cử', 'kiểm tra', 'mẹo', 'phương pháp']):
        return handle_study_questions(question)
    
    if any(keyword in q for keyword in ['thời gian', 'kế hoạch', 'lịch trình', 'quản lý']):
        return handle_time_management_questions(question)
    
    try:
        # Sử dụng system prompt chung cho giáo dục
        general_prompt = """Bạn là một trợ lý học tập thông minh, thân thiện và hiểu biết rộng.
        Nhiệm vụ của bạn là:
        - Trả lời các câu hỏi học tập một cách chính xác và dễ hiểu
        - Đưa ra lời khuyên học tập phù hợp
        - Khuyến khích tinh thần ham học hỏi
        - Trả lời bằng tiếng Việt, sử dụng HTML formatting cho câu trả lời đẹp
        - Luôn tích cực và hỗ trợ học sinh"""
        
        ai_response = call_openai_api(question, general_prompt, "Học tập chung")
        
        return {
            "answer": ai_response,
            "suggestions": ["Hỏi về môn học cụ thể", "Phương pháp học tập", "Quản lý thời gian", "Tìm tài liệu"],
            "ai_mode": "general"
        }
        
    except Exception as e:
        # Fallback message nếu API lỗi
        return {
            "answer": f"""🤖 Tôi hiểu bạn đang hỏi về: "{question}"
            
            <strong>💡 Gợi ý:</strong><br>
            • Hãy hỏi cụ thể hơn về môn học bạn quan tâm<br>
            • Tôi có thể giải thích các khái niệm về Toán, Vật lý, Hóa học, Lập trình...<br>
            • Hoặc hỏi về cách quản lý thời gian học tập hiệu quả<br><br>
            
            <strong>Ví dụ:</strong><br>
            • "Giải thích định lý Pythagore"<br>
            • "Công thức tính vận tốc trong vật lý"<br>
            • "Cách học Python cho người mới bắt đầu"<br>
            • "Làm thế nào để ôn thi hiệu quả?"<br><br>
            
            <em>Lưu ý: Hiện đang có vấn đề với AI, tôi sẽ cố gắng hỗ trợ bạn tốt nhất có thể!</em>
            """,
            "suggestions": ["Hỏi về Toán", "Hỏi về Vật lý", "Hỏi về Lập trình", "Mẹo học tập"]
        }


def handle_math_questions(question):
    """Xử lý câu hỏi về Toán học bằng AI thực sự"""
    set_ai_mode("math")
    try:
        ai_response = call_openai_api(question, SYSTEM_PROMPTS['math'], "Toán học")
        
        return {
            "answer": ai_response,
            "suggestions": ["Hỏi thêm về Toán", "Bài tập thực hành", "Ví dụ cụ thể", "Chuyển sang môn khác"],
            "ai_mode": "math"
        }
    except Exception as e:
        return {
            "answer": """🧮 <strong>Toán học</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Toán học. Tuy nhiên, tôi vẫn có thể hỗ trợ bạn với các công thức cơ bản:<br><br>
            
            <strong>📐 Hình học:</strong><br>
            • Diện tích hình vuông: <span class="formula">S = a²</span><br>
            • Diện tích hình tròn: <span class="formula">S = πr²</span><br>
            • Định lý Pythagore: <span class="formula">a² + b² = c²</span><br><br>
            
            <strong>📊 Đại số:</strong><br>
            • Công thức nghiệm bậc 2: <span class="formula">x = (-b ± √(b²-4ac))/2a</span><br>
            • Hằng đẳng thức: <span class="formula">(a+b)² = a² + 2ab + b²</span><br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Công thức hình học", "Giải phương trình", "Bài tập thực hành", "Chuyển sang môn khác"],
            "ai_mode": "math"
        }


def handle_physics_questions(question):
    """Xử lý câu hỏi về Vật lý bằng AI thực sự"""
    set_ai_mode("physics")
    
    try:
        ai_response = call_openai_api(question, SYSTEM_PROMPTS['physics'], "Vật lý")
        
        return {
            "answer": ai_response,
            "suggestions": ["Hỏi thêm về Vật lý", "Thí nghiệm thực tế", "Ví dụ ứng dụng", "Chuyển sang môn khác"],
            "ai_mode": "physics"
        }
    except Exception as e:
        return {
            "answer": """⚡ <strong>Vật lý</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Vật lý. Tuy nhiên, đây là một số công thức cơ bản:<br><br>
            
            <strong>🏃 Cơ học:</strong><br>
            • Lực: <span class="formula">F = ma</span><br>
            • Vận tốc: <span class="formula">v = s/t</span><br>
            • Gia tốc: <span class="formula">a = Δv/Δt</span><br><br>
            
            <strong>⚡ Điện học:</strong><br>
            • Định luật Ohm: <span class="formula">V = IR</span><br>
            • Công suất: <span class="formula">P = VI</span><br><br>
            
            <strong>🌊 Sóng:</strong><br>
            • Vận tốc sóng: <span class="formula">v = fλ</span><br><br>
            
            Hãy hỏi về hiện tượng vật lý cụ thể!""",
            "suggestions": ["Cơ học", "Điện học", "Quang học", "Thí nghiệm"],
            "ai_mode": "physics"
        }


def handle_programming_questions(question):
    """Xử lý câu hỏi về Lập trình bằng AI thực sự"""
    set_ai_mode("programming")
    
    try:
        ai_response = call_openai_api(question, SYSTEM_PROMPTS['programming'], "Lập trình")
        
        return {
            "answer": ai_response,
            "suggestions": ["Code examples", "Best practices", "Debugging tips", "Chuyển sang môn khác"],
            "ai_mode": "programming"
        }
    except Exception as e:
        return {
            "answer": """💻 <strong>Lập trình</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI lập trình. Tuy nhiên, đây là một số ví dụ cơ bản:<br><br>
            
            <strong>🐍 Python cơ bản:</strong><br>
            <div class="code-block">
            <div class="code-header">Python</div>
            <div class="code-content">
            # In ra "Hello World"<br>
            print("Hello, World!")<br><br>
            
            # Vòng lặp for<br>
            for i in range(5):<br>
            &nbsp;&nbsp;&nbsp;&nbsp;print(f"Số {i}")
            </div>
            </div><br>
            
            <strong>📚 Tài nguyên học tập:</strong><br>
            • Python.org - Tài liệu chính thức<br>
            • W3Schools - Tutorial từ cơ bản<br>
            • GitHub - Các dự án mẫu<br><br>
            
            Hãy hỏi về ngôn ngữ lập trình cụ thể!""",
            "suggestions": ["Python basics", "JavaScript", "Web development", "Algorithms"],
            "ai_mode": "programming"
        }


def handle_chemistry_questions(question):
    """Xử lý câu hỏi về Hóa học"""
    set_ai_mode("chemistry")
    
    return {
        "answer": """🧪 <strong>Hóa học</strong><br><br>
        <strong>⚛️ Bảng tuần hoàn:</strong><br>
        • Hydro (H): Nguyên tử số 1<br>
        • Carbon (C): Nguyên tử số 6<br>
        • Oxygen (O): Nguyên tử số 8<br><br>
        
        <strong>🔬 Phản ứng cơ bản:</strong><br>
        • Phản ứng cháy: <span class="formula">C + O₂ → CO₂</span><br>
        • Phản ứng acid-base: <span class="formula">HCl + NaOH → NaCl + H₂O</span><br><br>
        
        <strong>⚖️ Định luật bảo toàn khối lượng:</strong><br>
        Khối lượng chất tham gia = Khối lượng sản phẩm<br><br>
        
        Hãy hỏi về phản ứng hóa học cụ thể!""",
        "suggestions": ["Phản ứng hóa học", "Bảng tuần hoàn", "Phân tích định lượng", "Hóa hữu cơ"],
        "ai_mode": "chemistry"
    }


def handle_history_questions(question):
    """Xử lý câu hỏi về Lịch sử"""
    set_ai_mode("history")
    
    return {
        "answer": """📚 <strong>Lịch sử</strong><br><br>
        <strong>🇻🇳 Lịch sử Việt Nam:</strong><br>
        • Khởi nghĩa Hai Bà Trưng (40-43)<br>
        • Khởi nghĩa Lý Bí (544-548)<br>
        • Thắng lợi Bạch Đằng (938)<br>
        • Cách mạng Tháng Tám (1945)<br><br>
        
        <strong>🌍 Lịch sử thế giới:</strong><br>
        • Cách mạng công nghiệp (1760-1840)<br>
        • Đại chiến thế giới I (1914-1918)<br>
        • Đại chiến thế giới II (1939-1945)<br><br>
        
        Hãy hỏi về giai đoạn lịch sử cụ thể!""",
        "suggestions": ["Lịch sử Việt Nam", "Lịch sử thế giới", "Nhân vật lịch sử", "Sự kiện quan trọng"],
        "ai_mode": "history"
    }


def handle_english_questions(question):
    """Xử lý câu hỏi về Tiếng Anh"""
    set_ai_mode("english")
    
    return {
        "answer": """🇬🇧 <strong>English Learning</strong><br><br>
        <strong>📖 Grammar Basics:</strong><br>
        • Present Simple: I eat, He eats<br>
        • Past Simple: I ate, He ate<br>
        • Future: I will eat, He will eat<br><br>
        
        <strong>📝 Common Phrases:</strong><br>
        • How are you? - Bạn có khỏe không?<br>
        • Nice to meet you - Rất vui được gặp bạn<br>
        • Thank you - Cảm ơn<br><br>
        
        <strong>💡 Study Tips:</strong><br>
        • Đọc sách tiếng Anh đơn giản<br>
        • Xem phim có phụ đề<br>
        • Luyện nói mỗi ngày<br><br>
        
        Ask me specific English questions!""",
        "suggestions": ["Grammar rules", "Vocabulary", "Pronunciation", "Conversation practice"],
        "ai_mode": "english"
    }


def handle_study_questions(question):
    """Xử lý câu hỏi về phương pháp học tập"""
    set_ai_mode("study")
    
    try:
        ai_response = call_openai_api(question, SYSTEM_PROMPTS['study'], "Phương pháp học tập")
        
        return {
            "answer": ai_response,
            "suggestions": ["Kỹ thuật ghi nhớ", "Quản lý thời gian", "Giảm stress", "Lập kế hoạch học tập"],
            "ai_mode": "study"
        }
    except Exception as e:
        return {
            "answer": """📚 <strong>Phương pháp học tập hiệu quả</strong><br><br>
            
            <strong>🎯 Kỹ thuật Pomodoro:</strong><br>
            • Học 25 phút, nghỉ 5 phút<br>
            • Sau 4 lần, nghỉ 15-30 phút<br><br>
            
            <strong>📝 Ghi chú hiệu quả:</strong><br>
            • Sử dụng sơ đồ tư duy (Mind Map)<br>
            • Ghi chú Cornell Method<br>
            • Highlight các ý chính<br><br>
            
            <strong>🧠 Kỹ thuật ghi nhớ:</strong><br>
            • Lặp lại cách quãng (Spaced Repetition)<br>
            • Liên kết thông tin mới với kiến thức cũ<br>
            • Thực hành active recall<br><br>
            
            <strong>⏰ Quản lý thời gian:</strong><br>
            • Lập danh sách việc cần làm<br>
            • Ưu tiên công việc quan trọng<br>
            • Tạo thói quen học tập đều đặn""",
            "suggestions": ["Kỹ thuật ghi nhớ", "Quản lý thời gian", "Giảm stress", "Lập kế hoạch"],
            "ai_mode": "study"
        }


def handle_time_management_questions(question):
    """Xử lý câu hỏi về quản lý thời gian"""
    set_ai_mode("time_management")
    
    return {
        "answer": """⏰ <strong>Quản lý thời gian hiệu quả</strong><br><br>
        
        <strong>📅 Lập kế hoạch hàng ngày:</strong><br>
        • Viết ra 3 việc quan trọng nhất<br>
        • Ước tính thời gian cho mỗi việc<br>
        • Bắt đầu với việc khó nhất<br><br>
        
        <strong>🎯 Ma trận Eisenhower:</strong><br>
        • Quan trọng + Gấp = Làm ngay<br>
        • Quan trọng + Không gấp = Lên kế hoạch<br>
        • Không quan trọng + Gấp = Ủy thác<br>
        • Không quan trọng + Không gấp = Loại bỏ<br><br>
        
        <strong>⚡ Tips nhanh:</strong><br>
        • Tắt thông báo khi học<br>
        • Chuẩn bị mọi thứ từ tối hôm trước<br>
        • Nghỉ ngơi đúng cách<br>
        • Thưởng cho bản thân khi hoàn thành mục tiêu""",
        "suggestions": ["Lập kế hoạch học tập", "Ưu tiên công việc", "Loại bỏ phân tâm", "Tạo thói quen"],
        "ai_mode": "time_management"
    }
