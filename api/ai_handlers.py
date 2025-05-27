import openai
from datetime import datetime
from config import SYSTEM_PROMPTS, Config

openai.api_key = Config.OPENAI_API_KEY


def call_openai_api(question, system_prompt, subject):
    """Gọi OpenAI API với prompt đơn giản và tập trung"""
    try:
        print(f"[DEBUG] call_openai_api called for subject: {subject}")
        print(f"[DEBUG] Question: {question}")
        
        # Đơn giản hóa system prompt - chỉ tập trung vào câu hỏi hiện tại
        focused_prompt = f"""{system_prompt}

NHIỆM VỤ: Trả lời trực tiếp câu hỏi "{question}" một cách chính xác và chi tiết.
Sử dụng HTML formatting để câu trả lời đẹp mắt."""
        
        messages = [
            {"role": "system", "content": focused_prompt},
            {"role": "user", "content": question}
        ]
        
        print(f"[DEBUG] Sending request to OpenAI with {len(messages)} messages")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1000,
            temperature=0.3,  # Giảm temperature để có câu trả lời tập trung hơn
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"[DEBUG] OpenAI response received: {answer[:100]}...")
        
        return answer
    except Exception as e:
        print(f"[ERROR] OpenAI API Error: {e}")
        return f"Hiện tại có lỗi kết nối với AI. Vui lòng thử lại sau. Chi tiết lỗi: {str(e)}"


def handle_ai_question(question):
    """Xử lý câu hỏi AI thông minh với logic detect được cải thiện"""
    q = question.lower()
    print(f"[DEBUG] handle_ai_question called with: {question}")
    
    # QUAN TRỌNG: Kiểm tra programming trước vì "thuật toán" chứa "toán"
    if any(keyword in q for keyword in ['lập trình', 'programming', 'code', 'python', 'javascript', 'thuật toán', 'algorithm', 'decision tree', 'machine learning', 'ai']):
        print(f"[DEBUG] Detected programming keywords, routing to handle_programming_questions")
        return handle_programming_questions(question)
    
    # Kiểm tra math sau, nhưng loại trừ trường hợp là thuật toán
    if any(keyword in q for keyword in ['toán', 'math', 'công thức', 'tính', 'phương trình']) and 'thuật toán' not in q and 'algorithm' not in q:
        print(f"[DEBUG] Detected math keywords, routing to handle_math_questions")
        return handle_math_questions(question)
    
    if any(keyword in q for keyword in ['vật lý', 'physics', 'lực', 'năng lượng', 'tốc độ']):
        return handle_physics_questions(question)
    
    if any(keyword in q for keyword in ['hóa học', 'chemistry', 'phản ứng', 'nguyên tố']):
        return handle_chemistry_questions(question)
    
    if any(keyword in q for keyword in ['lịch sử', 'history', 'việt nam', 'thế giới']):
        return handle_history_questions(question)
    
    if any(keyword in q for keyword in ['tiếng anh', 'english', 'grammar', 'vocabulary']):
        return handle_english_questions(question)
    
    if any(keyword in q for keyword in ['học', 'ôn thi', 'thi cử', 'kiểm tra', 'mẹo', 'phương pháp']):
        return handle_study_questions(question)
    
    if any(keyword in q for keyword in ['thời gian', 'kế hoạch', 'lịch trình', 'quản lý']):
        return handle_time_management_questions(question)
    
    # General fallback với prompt đơn giản
    try:        
        general_prompt = """Bạn là trợ lý học tập thông minh. Trả lời câu hỏi một cách chính xác và hữu ích. 
        Sử dụng HTML formatting cho câu trả lời đẹp mắt."""
        
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
    print(f"[DEBUG] handle_math_questions called with: {question}")
    
    try:
        ai_response = call_openai_api(question, SYSTEM_PROMPTS['math'], "Toán học")
        print(f"[DEBUG] Math AI response: {ai_response[:100]}...")
        
        return {
            "answer": ai_response,
            "suggestions": ["Hỏi thêm về Toán", "Bài tập thực hành", "Ví dụ cụ thể", "Chuyển sang môn khác"],
            "ai_mode": "math"
        }
    except Exception as e:
        print(f"[DEBUG] Math AI error: {e}")
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
    """Xử lý câu hỏi về Hóa học bằng AI thực sự"""
    try:
        ai_response = call_openai_api(question, SYSTEM_PROMPTS['chemistry'], "Hóa học")
        
        return {
            "answer": ai_response,
            "suggestions": ["Phản ứng hóa học", "Bảng tuần hoàn", "Thí nghiệm", "Chuyển sang môn khác"],
            "ai_mode": "chemistry"
        }
    except Exception as e:
        return {
            "answer": """🧪 <strong>Hóa học</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Hóa học. Tuy nhiên, đây là một số kiến thức cơ bản:<br><br>
            
            <strong>⚛️ Nguyên tử:</strong><br>
            • Proton (+), Neutron (0), Electron (-)<br>
            • Số hiệu nguyên tử = số proton<br><br>
            
            <strong>🔄 Phản ứng cơ bản:</strong><br>
            • 2H₂ + O₂ → 2H₂O<br>
            • NaCl → Na⁺ + Cl⁻<br><br>
            
            <strong>📊 Bảng tuần hoàn:</strong><br>
            • 18 nhóm, 7 chu kỳ<br>
            • Kim loại - Phi kim - Khí hiếm""",
            "suggestions": ["Phản ứng hóa học", "Bảng tuần hoàn", "Cân bằng phương trình", "Chuyển sang môn khác"],
            "ai_mode": "chemistry"
        }


def handle_history_questions(question):
    """Xử lý câu hỏi về Lịch sử bằng AI thực sự"""
    try:
        ai_response = call_openai_api(question, SYSTEM_PROMPTS['history'], "Lịch sử")
        
        return {
            "answer": ai_response,
            "suggestions": ["Lịch sử Việt Nam", "Lịch sử thế giới", "Nhân vật lịch sử", "Chuyển sang môn khác"],
            "ai_mode": "history"
        }
    except Exception as e:
        return {
            "answer": """📜 <strong>Lịch sử</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Lịch sử. Tuy nhiên, đây là một số mốc thời gian quan trọng:<br><br>
            
            <strong>🇻🇳 Lịch sử Việt Nam:</strong><br>
            • 2879 TCN: Nhà nước Văn Lang<br>
            • 1010: Thăng Long thành kinh đô<br>
            • 1945: Tuyên ngôn độc lập<br><br>
            
            <strong>🌍 Lịch sử thế giới:</strong><br>
            • 1789: Cách mạng Pháp<br>
            • 1914-1918: Thế chiến I<br>
            • 1939-1945: Thế chiến II""",
            "suggestions": ["Lịch sử Việt Nam", "Lịch sử thế giới", "Nhân vật lịch sử", "Chuyển sang môn khác"],
            "ai_mode": "history"
        }


def handle_english_questions(question):
    """Xử lý câu hỏi về Tiếng Anh bằng AI thực sự"""
    try:
        ai_response = call_openai_api(question, SYSTEM_PROMPTS['english'], "Tiếng Anh")
        
        return {
            "answer": ai_response,
            "suggestions": ["Grammar", "Vocabulary", "Pronunciation", "Chuyển sang môn khác"],
            "ai_mode": "english"
        }
    except Exception as e:
        return {
            "answer": """🇺🇸 <strong>Tiếng Anh</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Tiếng Anh. Tuy nhiên, đây là một số tips cơ bản:<br><br>
            
            <strong>📚 Grammar cơ bản:</strong><br>
            • Present: I study English<br>
            • Past: I studied English<br>
            • Future: I will study English<br><br>
            
            <strong>💡 Tips học từ vựng:</strong><br>
            • Học 5-10 từ mới mỗi ngày<br>
            • Sử dụng flashcards<br>
            • Đọc sách, xem phim tiếng Anh<br><br>
            
            <strong>🗣️ Luyện speaking:</strong><br>
            • Nói chuyện với bản thân<br>
            • Tham gia câu lạc bộ tiếng Anh<br>
            • Sử dụng apps như HelloTalk""",
            "suggestions": ["Grammar", "Vocabulary", "Pronunciation", "Chuyển sang môn khác"],
            "ai_mode": "english"
        }


def handle_study_questions(question):
    """Xử lý câu hỏi về phương pháp học tập bằng AI thực sự"""
    try:
        ai_response = call_openai_api(question, SYSTEM_PROMPTS['study'], "Phương pháp học tập")
        
        return {
            "answer": ai_response,
            "suggestions": ["Kỹ thuật ghi nhớ", "Lập kế hoạch học", "Động lực học tập", "Chuyển sang môn khác"],
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


def handle_ai_question_with_context(question, context_messages=None):
    """Xử lý câu hỏi AI với context từ lịch sử cuộc trò chuyện"""
    q = question.lower()
    print(f"[DEBUG] handle_ai_question_with_context called with: {question}")
    print(f"[DEBUG] Context messages: {len(context_messages) if context_messages else 0}")
    
    # Detect subject như trước
    if any(keyword in q for keyword in ['lập trình', 'programming', 'code', 'python', 'javascript', 'thuật toán', 'algorithm', 'decision tree', 'machine learning', 'ai']):
        return handle_programming_questions_with_context(question, context_messages)
    
    if any(keyword in q for keyword in ['toán', 'math', 'công thức', 'tính', 'phương trình']) and 'thuật toán' not in q and 'algorithm' not in q:
        return handle_math_questions_with_context(question, context_messages)
    
    if any(keyword in q for keyword in ['vật lý', 'physics', 'lực', 'năng lượng', 'tốc độ']):
        return handle_physics_questions_with_context(question, context_messages)
    
    if any(keyword in q for keyword in ['hóa học', 'chemistry', 'phản ứng', 'nguyên tố']):
        return handle_chemistry_questions_with_context(question, context_messages)
    
    if any(keyword in q for keyword in ['lịch sử', 'history', 'việt nam', 'thế giới']):
        return handle_history_questions_with_context(question, context_messages)
    
    if any(keyword in q for keyword in ['tiếng anh', 'english', 'grammar', 'vocabulary']):
        return handle_english_questions_with_context(question, context_messages)
    
    if any(keyword in q for keyword in ['học', 'ôn thi', 'thi cử', 'kiểm tra', 'mẹo', 'phương pháp']):
        return handle_study_questions_with_context(question, context_messages)
    
    if any(keyword in q for keyword in ['thời gian', 'kế hoạch', 'lịch trình', 'quản lý']):
        return handle_time_management_questions_with_context(question, context_messages)
    
    # General fallback với context
    return handle_general_questions_with_context(question, context_messages)


def call_openai_api_with_context(question, system_prompt, subject, context_messages=None):
    """Gọi OpenAI API với context từ lịch sử cuộc trò chuyện"""
    try:
        print(f"[DEBUG] call_openai_api_with_context called for subject: {subject}")
        print(f"[DEBUG] Question: {question}")
        print(f"[DEBUG] Context messages: {len(context_messages) if context_messages else 0}")
        
        # Xây dựng messages với context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Thêm context messages nếu có
        if context_messages:
            messages.extend(context_messages)
        
        # Thêm câu hỏi hiện tại
        messages.append({"role": "user", "content": question})
        
        print(f"[DEBUG] Sending request to OpenAI with {len(messages)} messages")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=1200,  # Tăng max_tokens để xử lý context
            temperature=0.3,
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"[DEBUG] OpenAI response received: {answer[:100]}...")
        
        return answer
    except Exception as e:
        print(f"[ERROR] OpenAI API Error: {e}")
        return f"Hiện tại có lỗi kết nối với AI. Vui lòng thử lại sau. Chi tiết lỗi: {str(e)}"


def handle_math_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi về Toán học với context"""
    try:
        ai_response = call_openai_api_with_context(question, SYSTEM_PROMPTS['math'], "Toán học", context_messages)
        return {
            "answer": ai_response,
            "suggestions": ["Hỏi thêm về Toán", "Bài tập thực hành", "Ví dụ cụ thể", "Chuyển sang môn khác"],
            "ai_mode": "math"
        }
    except Exception as e:
        return handle_math_questions(question)  # Fallback to non-context version


def handle_programming_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi về Lập trình với context"""
    try:
        ai_response = call_openai_api_with_context(question, SYSTEM_PROMPTS['programming'], "Lập trình", context_messages)
        return {
            "answer": ai_response,
            "suggestions": ["Code examples", "Best practices", "Debugging tips", "Chuyển sang môn khác"],
            "ai_mode": "programming"
        }
    except Exception as e:
        return handle_programming_questions(question)  # Fallback


def handle_physics_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi về Vật lý với context"""
    try:
        ai_response = call_openai_api_with_context(question, SYSTEM_PROMPTS['physics'], "Vật lý", context_messages)
        return {
            "answer": ai_response,
            "suggestions": ["Hỏi thêm về Vật lý", "Thí nghiệm thực tế", "Ví dụ ứng dụng", "Chuyển sang môn khác"],
            "ai_mode": "physics"
        }
    except Exception as e:
        return handle_physics_questions(question)  # Fallback


def handle_chemistry_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi về Hóa học với context"""
    try:
        ai_response = call_openai_api_with_context(question, SYSTEM_PROMPTS['chemistry'], "Hóa học", context_messages)
        return {
            "answer": ai_response,
            "suggestions": ["Phản ứng hóa học", "Bảng tuần hoàn", "Thí nghiệm", "Chuyển sang môn khác"],
            "ai_mode": "chemistry"
        }
    except Exception as e:
        return handle_chemistry_questions(question)  # Fallback


def handle_history_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi về Lịch sử với context"""
    try:
        ai_response = call_openai_api_with_context(question, SYSTEM_PROMPTS['history'], "Lịch sử", context_messages)
        return {
            "answer": ai_response,
            "suggestions": ["Lịch sử Việt Nam", "Lịch sử thế giới", "Các sự kiện quan trọng", "Chuyển sang môn khác"],
            "ai_mode": "history"
        }
    except Exception as e:
        return handle_history_questions(question)  # Fallback


def handle_english_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi về Tiếng Anh với context"""
    try:
        ai_response = call_openai_api_with_context(question, SYSTEM_PROMPTS['english'], "Tiếng Anh", context_messages)
        return {
            "answer": ai_response,
            "suggestions": ["Grammar tips", "Vocabulary", "Speaking practice", "Chuyển sang môn khác"],
            "ai_mode": "english"
        }
    except Exception as e:
        return handle_english_questions(question)  # Fallback


def handle_study_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi về phương pháp học tập với context"""
    try:
        ai_response = call_openai_api_with_context(question, SYSTEM_PROMPTS['study'], "Phương pháp học tập", context_messages)
        return {
            "answer": ai_response,
            "suggestions": ["Kỹ thuật ghi nhớ", "Lập kế hoạch học", "Động lực học tập", "Chuyển sang môn khác"],
            "ai_mode": "study"
        }
    except Exception as e:
        return handle_study_questions(question)  # Fallback


def handle_time_management_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi về quản lý thời gian với context"""
    try:
        ai_response = call_openai_api_with_context(question, SYSTEM_PROMPTS['study'], "Quản lý thời gian", context_messages)
        return {
            "answer": ai_response,
            "suggestions": ["Lập kế hoạch", "Ưu tiên công việc", "Công cụ quản lý", "Chuyển sang môn khác"],
            "ai_mode": "study"
        }
    except Exception as e:
        return handle_time_management_questions(question)  # Fallback


def handle_general_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi chung với context"""
    try:
        general_prompt = """Bạn là trợ lý học tập thông minh. Trả lời câu hỏi một cách chính xác và hữu ích. 
        Sử dụng HTML formatting cho câu trả lời đẹp mắt. Dựa vào ngữ cảnh cuộc trò chuyện trước đó để đưa ra câu trả lời phù hợp."""
        
        ai_response = call_openai_api_with_context(question, general_prompt, "Học tập chung", context_messages)
        
        return {
            "answer": ai_response,
            "suggestions": ["Hỏi về môn học cụ thể", "Phương pháp học tập", "Quản lý thời gian", "Tìm tài liệu"],
            "ai_mode": "general"
        }
    except Exception as e:
        return handle_ai_question(question)  # Fallback to original function
