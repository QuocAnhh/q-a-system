from datetime import datetime
from config import SYSTEM_PROMPTS
from openai_manager import get_smart_response, openai_manager


def _get_task_type_from_subject(subject):
    """Xác định task type từ subject để chọn model phù hợp"""
    subject_lower = subject.lower()
    
    if any(keyword in subject_lower for keyword in ['programming', 'lập trình', 'code', 'thuật toán', 'algorithm']):
        return "programming"
    elif any(keyword in subject_lower for keyword in ['math', 'toán', 'calculus', 'algebra', 'geometry']):
        return "math"
    elif any(keyword in subject_lower for keyword in ['document', 'tài liệu', 'analysis', 'phân tích']):
        return "document_analysis"
    else:
        return "general"





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

    if any(keyword in q for keyword in ['đại số tuyến tính', 'linear algebra', 'ma trận', 'matrix', 'vector', 'không gian vector', 'hệ phương trình tuyến tính']):
        print(f"[DEBUG] Detected linear algebra keywords, routing to handle_linear_algebra_questions")
        return handle_linear_algebra_questions(question)

    if any(keyword in q for keyword in ['xác suất thống kê', 'probability', 'statistics', 'phân phối', 'distribution', 'kiểm định giả thuyết', 'hypothesis testing', 'hồi quy']):
        print(f"[DEBUG] Detected probability statistics keywords, routing to handle_probability_statistics_questions")
        return handle_probability_statistics_questions(question)

    if any(keyword in q for keyword in ['giải tích', 'calculus', 'vi phân', 'differential', 'tích phân', 'integral', 'đạo hàm', 'derivative', 'giới hạn', 'limit']):
        print(f"[DEBUG] Detected calculus keywords, routing to handle_calculus_questions")
        return handle_calculus_questions(question)
    
    # General fallback với prompt đơn giản
    try:        
        general_prompt = """Bạn là trợ lý học tập thông minh. Trả lời câu hỏi một cách chính xác và hữu ích. 
        Sử dụng HTML formatting cho câu trả lời đẹp mắt."""
        
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=general_prompt,
            task_type="general",
            temperature=0.3
        )
        
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
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS['math'],
            task_type="math",
            temperature=0.3
        )
        print(f"[DEBUG] Math AI response: {ai_response[:100]}...")
        
        return {
            "answer": ai_response,
            "suggestions": ["Hỏi thêm về Toán", "Bài tập thực hành", "Ví dụ cụ thể", "Chuyển sang môn khác"],
            "ai_mode": "math"
        }
    except Exception as e:
        print(f"[DEBUG] Math AI error: {e}")
        return {
            "answer": """📐 <strong>Toán học</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Toán học. Tuy nhiên, đây là một số công thức cơ bản:<br><br>
            
            <strong>📊 Hình học:</strong><br>
            • Chu vi hình tròn: <span class="formula">C = 2πr</span><br>
            • Diện tích hình tròn: <span class="formula">S = πr²</span><br>
            • Định lý Pythagore: <span class="formula">a² + b² = c²</span><br><br>
            
            <strong>📈 Đại số:</strong><br>
            • Công thức nghiệm phương trình bậc 2: <span class="formula">x = (-b ± √(b²-4ac))/2a</span><br>
            • Hằng đẳng thức: <span class="formula">(a+b)² = a² + 2ab + b²</span><br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Công thức hình học", "Giải phương trình", "Bài tập thực hành", "Chuyển sang môn khác"],
            "ai_mode": "math"
        }


def handle_physics_questions(question):
    """Xử lý câu hỏi về Vật lý bằng AI thực sự"""
    
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS['physics'],
            task_type="general",
            temperature=0.3
        )
        
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
            • Công suất: <span class="formula">P = UI</span><br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Cơ học", "Điện học", "Quang học", "Chuyển sang môn khác"],
            "ai_mode": "physics"
        }


def handle_programming_questions(question):
    """Xử lý câu hỏi về Lập trình bằng AI thực sự"""
    print(f"[DEBUG] handle_programming_questions called with: {question}")
    
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS['programming'],
            task_type="programming",
            temperature=0.2  # Lower temperature for more precise code
        )
        print(f"[DEBUG] Programming AI response: {ai_response[:100]}...")
        
        return {
            "answer": ai_response,
            "suggestions": ["Code example", "Best practices", "Debug help", "Chuyển sang môn khác"],
            "ai_mode": "programming"
        }
    except Exception as e:
        print(f"[DEBUG] Programming AI error: {e}")
        return {
            "answer": """💻 <strong>Lập trình</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Lập trình. Tuy nhiên, đây là một số khái niệm cơ bản:<br><br>
            
            <strong>🐍 Python cơ bản:</strong><br>
            • In ra màn hình: <code>print("Hello World")</code><br>
            • Khai báo biến: <code>x = 10</code><br>
            • Vòng lặp: <code>for i in range(5):</code><br><br>
            
            <strong>🌐 JavaScript cơ bản:</strong><br>
            • In ra console: <code>console.log("Hello World")</code><br>
            • Khai báo biến: <code>let x = 10;</code><br>
            • Hàm: <code>function myFunction() {}</code><br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Python basics", "JavaScript", "Algorithms", "Chuyển sang môn khác"],
            "ai_mode": "programming"
        }


def handle_chemistry_questions(question):
    """Xử lý câu hỏi về Hóa học"""
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS['chemistry'],
            task_type="general",
            temperature=0.3
        )
        
        return {
            "answer": ai_response,
            "suggestions": ["Phản ứng hóa học", "Bảng tuần hoàn", "Thí nghiệm", "Chuyển sang môn khác"],
            "ai_mode": "chemistry"
        }
    except Exception as e:
        return {
            "answer": """🧪 <strong>Hóa học</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Hóa học. Tuy nhiên, đây là một số kiến thức cơ bản:<br><br>
            
            <strong>⚛️ Nguyên tố:</strong><br>
            • Hydro (H): Nguyên tử số 1<br>
            • Carbon (C): Nguyên tử số 6<br>
            • Oxygen (O): Nguyên tử số 8<br><br>
            
            <strong>🔬 Phản ứng cơ bản:</strong><br>
            • Cháy: <span class="formula">C + O₂ → CO₂</span><br>
            • Tổng hợp nước: <span class="formula">2H₂ + O₂ → 2H₂O</span><br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Bảng tuần hoàn", "Phản ứng hóa học", "Công thức hóa học", "Chuyển sang môn khác"],
            "ai_mode": "chemistry"
        }


def handle_history_questions(question):
    """Xử lý câu hỏi về Lịch sử"""
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS['history'],
            task_type="general",
            temperature=0.3
        )
        
        return {
            "answer": ai_response,
            "suggestions": ["Lịch sử Việt Nam", "Lịch sử thế giới", "Nhân vật lịch sử", "Chuyển sang môn khác"],
            "ai_mode": "history"
        }
    except Exception as e:
        return {
            "answer": """📚 <strong>Lịch sử</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Lịch sử. Tuy nhiên, đây là một số sự kiện quan trọng:<br><br>
            
            <strong>🇻🇳 Lịch sử Việt Nam:</strong><br>
            • 2879 TCN: Vua Hùng dựng nước<br>
            • 1945: Cách mạng tháng 8<br>
            • 1975: Thống nhất đất nước<br><br>
            
            <strong>🌍 Lịch sử thế giới:</strong><br>
            • 1789: Cách mạng Pháp<br>
            • 1945: Kết thúc Thế chiến II<br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Việt Nam", "Thế giới", "Nhân vật", "Chuyển sang môn khác"],
            "ai_mode": "history"
        }


def handle_english_questions(question):
    """Xử lý câu hỏi về Tiếng Anh"""
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS['english'],
            task_type="general",
            temperature=0.3
        )
        
        return {
            "answer": ai_response,
            "suggestions": ["Grammar", "Vocabulary", "Speaking practice", "Chuyển sang môn khác"],
            "ai_mode": "english"
        }
    except Exception as e:
        return {
            "answer": """🇬🇧 <strong>English</strong><br><br>
            Sorry, there's currently an issue with the English AI. However, here are some basic grammar rules:<br><br>
            
            <strong>📝 Grammar basics:</strong><br>
            • Present Simple: I/You/We/They + verb<br>
            • Present Simple: He/She/It + verb + s<br>
            • Past Simple: verb + ed (regular verbs)<br><br>
            
            <strong>📚 Common phrases:</strong><br>
            • How are you? - Bạn có khỏe không?<br>
            • What's your name? - Tên bạn là gì?<br>
            • Nice to meet you! - Rất vui được gặp bạn!<br><br>
            
            Please ask a specific question so I can help you better!""",
            "suggestions": ["Grammar rules", "Vocabulary", "Common phrases", "Chuyển sang môn khác"],
            "ai_mode": "english"
        }


def handle_study_questions(question):
    """Xử lý câu hỏi về phương pháp học tập"""
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS['study'],
            task_type="general",
            temperature=0.3
        )
        
        return {
            "answer": ai_response,
            "suggestions": ["Phương pháp học", "Lịch trình ôn thi", "Kỹ thuật ghi nhớ", "Chuyển sang môn khác"],
            "ai_mode": "study"
        }
    except Exception as e:
        return {
            "answer": """📖 <strong>Phương pháp học tập</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Học tập. Tuy nhiên, đây là một số mẹo hiệu quả:<br><br>
            
            <strong>🎯 Kỹ thuật Pomodoro:</strong><br>
            • Học 25 phút, nghỉ 5 phút<br>
            • Sau 4 chu kỳ, nghỉ 15-30 phút<br><br>
            
            <strong>🧠 Kỹ thuật ghi nhớ:</strong><br>
            • Ôn lại sau 1 ngày, 1 tuần, 1 tháng<br>
            • Tạo flashcards cho từ khóa quan trọng<br>
            • Học nhóm để trao đổi kiến thức<br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Lập kế hoạch", "Kỹ thuật ghi nhớ", "Ôn thi hiệu quả", "Chuyển sang môn khác"],
            "ai_mode": "study"
        }


def handle_time_management_questions(question):
    """Xử lý câu hỏi về quản lý thời gian"""
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS['time_management'],
            task_type="general",
            temperature=0.3
        )
        
        return {
            "answer": ai_response,
            "suggestions": ["Lập kế hoạch", "Ưu tiên công việc", "Công cụ quản lý", "Chuyển sang môn khác"],
            "ai_mode": "time_management"
        }
    except Exception as e:
        return {
            "answer": """⏰ <strong>Quản lý thời gian</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI Quản lý thời gian. Tuy nhiên, đây là một số mẹo hữu ích:<br><br>
            
            <strong>📅 Ma trận Eisenhower:</strong><br>
            • Quan trọng & Gấp: Làm ngay<br>
            • Quan trọng & Không gấp: Lên kế hoạch<br>
            • Không quan trọng & Gấp: Ủy thác<br>
            • Không quan trọng & Không gấp: Loại bỏ<br><br>
            
            <strong>🎯 Quy tắc 80/20:</strong><br>
            • 20% công việc mang lại 80% kết quả<br>
            • Tập trung vào nhiệm vụ quan trọng nhất<br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Lập kế hoạch học tập", "Ưu tiên công việc", "Cân bằng học tập", "Chuyển sang môn khác"],
            "ai_mode": "time_management"
        }


# New subject handlers
def handle_linear_algebra_questions(question):
    """Xử lý câu hỏi về Đại số tuyến tính"""
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS.get('linear_algebra', SYSTEM_PROMPTS['math']),
            task_type="math",
            temperature=0.3
        )
        
        return {
            "answer": ai_response,
            "suggestions": ["Ma trận", "Vector", "Hệ phương trình", "Chuyển sang môn khác"],
            "ai_mode": "linear_algebra"
        }
    except Exception as e:
        return {
            "answer": """🔢 <strong>Đại số tuyến tính</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI. Tuy nhiên, đây là một số khái niệm cơ bản:<br><br>
            
            <strong>📊 Ma trận:</strong><br>
            • Ma trận vuông: số hàng = số cột<br>
            • Ma trận đơn vị: đường chéo chính = 1<br>
            • Định thức: det(A)<br><br>
            
            <strong>➡️ Vector:</strong><br>
            • Tích vô hướng: a·b = |a||b|cos(θ)<br>
            • Độ dài vector: |v| = √(x² + y² + z²)<br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Ma trận", "Vector", "Định thức", "Chuyển sang môn khác"],
            "ai_mode": "linear_algebra"
        }


def handle_probability_statistics_questions(question):
    """Xử lý câu hỏi về Xác suất thống kê"""
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS.get('probability_statistics', SYSTEM_PROMPTS['math']),
            task_type="math",
            temperature=0.3
        )
        
        return {
            "answer": ai_response,
            "suggestions": ["Xác suất", "Phân phối", "Kiểm định", "Chuyển sang môn khác"],
            "ai_mode": "probability_statistics"
        }
    except Exception as e:
        return {
            "answer": """📈 <strong>Xác suất thống kê</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI. Tuy nhiên, đây là một số công thức cơ bản:<br><br>
            
            <strong>🎲 Xác suất:</strong><br>
            • P(A) = số trường hợp thuận lợi / tổng số trường hợp<br>
            • P(A ∪ B) = P(A) + P(B) - P(A ∩ B)<br>
            • P(A|B) = P(A ∩ B) / P(B)<br><br>
            
            <strong>📊 Thống kê:</strong><br>
            • Trung bình: x̄ = Σx/n<br>
            • Phương sai: σ² = Σ(x-x̄)²/n<br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Xác suất cơ bản", "Phân phối chuẩn", "Kiểm định giả thuyết", "Chuyển sang môn khác"],
            "ai_mode": "probability_statistics"
        }


def handle_calculus_questions(question):
    """Xử lý câu hỏi về Giải tích"""
    try:
        ai_response = get_smart_response(
            prompt=question,
            system_prompt=SYSTEM_PROMPTS.get('calculus', SYSTEM_PROMPTS['math']),
            task_type="math",
            temperature=0.3
        )
        
        return {
            "answer": ai_response,
            "suggestions": ["Đạo hàm", "Tích phân", "Giới hạn", "Chuyển sang môn khác"],
            "ai_mode": "calculus"
        }
    except Exception as e:
        return {
            "answer": """∫ <strong>Giải tích</strong><br><br>
            Xin lỗi, hiện tại có lỗi kết nối với AI. Tuy nhiên, đây là một số công thức cơ bản:<br><br>
            
            <strong>📈 Đạo hàm:</strong><br>
            • (x^n)' = n·x^(n-1)<br>
            • (sin x)' = cos x<br>
            • (cos x)' = -sin x<br>
            • (e^x)' = e^x<br><br>
            
            <strong>∫ Tích phân:</strong><br>
            • ∫x^n dx = x^(n+1)/(n+1) + C<br>
            • ∫sin x dx = -cos x + C<br>
            • ∫cos x dx = sin x + C<br><br>
            
            Hãy hỏi câu hỏi cụ thể để tôi có thể hỗ trợ tốt hơn!""",
            "suggestions": ["Quy tắc đạo hàm", "Tích phân cơ bản", "Giới hạn", "Chuyển sang môn khác"],
            "ai_mode": "calculus"
        }


# Context-aware handlers (for conversation continuity)
def handle_ai_question_with_context(question, context_messages=None):
    """Xử lý câu hỏi AI với context từ cuộc trò chuyện trước"""
    print(f"[DEBUG] handle_ai_question_with_context called")
    print(f"[DEBUG] Question: {question}")
    print(f"[DEBUG] Context messages: {len(context_messages) if context_messages else 0}")
    
    try:
        # PRIORITY 1: Check for calendar requests first
        calendar_keywords = [
            'lịch', 'deadline', 'hẹn', 'cuộc họp', 'sự kiện', 'nhắc nhở', 
            'meeting', 'event', 'reminder', 'schedule', 'appointment',
            'tạo lịch', 'đặt lịch', 'thêm lịch', 'lên lịch'
        ]
        
        if any(keyword in question.lower() for keyword in calendar_keywords):
            print(f"[DEBUG] Detected calendar request in AI handler")
            try:
                from calendar_integration import CalendarIntegration
                
                # Generate a simple user ID for calendar functionality
                user_id = f"user_{datetime.now().strftime('%Y%m%d')}"
                
                calendar_integration = CalendarIntegration()
                calendar_result = calendar_integration.process_calendar_request(user_id, question)
                
                # Format calendar response for chat interface
                if calendar_result['success']:
                    return {
                        "answer": calendar_result['message'],
                        "suggestions": ["Xem lịch", "Tạo sự kiện khác", "Hỏi về học tập"],
                        "ai_mode": "calendar",
                        "calendar_data": calendar_result.get('data'),
                        "calendar_action": calendar_result.get('action')
                    }
                else:
                    # If calendar fails, provide helpful response
                    print(f"[DEBUG] Calendar processing failed: {calendar_result['message']}")
                    if calendar_result.get('action') == 'auth_required':
                        return {
                            "answer": f"{calendar_result['message']}\n\n💡 **Hoặc bạn có thể hỏi tôi về:**\n• Phương pháp quản lý thời gian hiệu quả\n• Cách lập kế hoạch học tập\n• Mẹo tổ chức công việc",
                            "suggestions": ["Quản lý thời gian", "Lập kế hoạch học", "Hỏi khác"],
                            "ai_mode": "calendar_suggestion",
                            "calendar_data": calendar_result.get('data')
                        }
                    elif calendar_result.get('action') == 'none':
                        # Continue to normal AI processing for non-calendar questions
                        pass
                    else:
                        return {
                            "answer": f"{calendar_result['message']}\n\n💡 **Trong khi đó, tôi có thể giúp bạn:**\n• Lời khuyên về quản lý thời gian\n• Phương pháp lập kế hoạch học tập\n• Kỹ thuật tổ chức công việc hiệu quả",
                            "suggestions": ["Mẹo quản lý thời gian", "Lập kế hoạch học", "Hỏi khác"],
                            "ai_mode": "calendar_fallback"
                        }
                    
            except ImportError:
                print("[DEBUG] Calendar integration not available")
                # Add helpful response about time management
                if any(word in question.lower() for word in ['lịch', 'deadline', 'kế hoạch', 'thời gian']):
                    return {
                        "answer": """📅 **Về quản lý thời gian và lịch trình:**\n\nTôi hiểu bạn quan tâm đến việc quản lý thời gian! Dù chức năng calendar chưa khả dụng, tôi có thể chia sẻ các mẹo hữu ích:\n\n**🎯 Nguyên tắc ưu tiên:**\n• Ma trận Eisenhower: Quan trọng vs Gấp\n• Quy tắc 80/20: Tập trung vào 20% công việc quan trọng\n\n**⏰ Kỹ thuật Pomodoro:**\n• Làm việc 25 phút, nghỉ 5 phút\n• Tăng tập trung và hiệu suất\n\n**📝 Lập kế hoạch:**\n• Viết ra mục tiêu cụ thể\n• Chia nhỏ công việc lớn\n• Đặt deadline thực tế\n\nBạn muốn tôi giải thích chi tiết về phương pháp nào?""",
                        "suggestions": ["Ma trận Eisenhower", "Kỹ thuật Pomodoro", "Lập kế hoạch học tập", "Mẹo tăng hiệu suất"],
                        "ai_mode": "time_management"
                    }
            except Exception as calendar_error:
                print(f"[DEBUG] Calendar integration error: {calendar_error}")
                # Continue to normal AI processing
        
        # PRIORITY 2: Normal AI processing
        # Prepare messages with context
        messages = []
        
        # Add system prompt
        messages.append({
            "role": "system", 
            "content": """Bạn là trợ lý học tập thông minh. Trả lời câu hỏi một cách chính xác và hữu ích.
            Sử dụng HTML formatting cho câu trả lời đẹp mắt. Hãy duy trì ngữ cảnh cuộc trò chuyện.
            
            KHI NGƯỜI DÙNG HỎI VỀ THỜI GIAN/LỊCH TRÌNH:
            - Đưa ra lời khuyên thực tế về quản lý thời gian
            - Gợi ý các phương pháp lập kế hoạch hiệu quả
            - Chia sẻ kỹ thuật tổ chức công việc
            """
        })
        
        # Add context messages if available
        if context_messages:
            for msg in context_messages[-6:]:  # Keep last 6 messages for context
                if msg.get('role') and msg.get('content'):
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })
        
        # Add current question
        messages.append({"role": "user", "content": question})
        
        # Use OpenAI manager for response
        result = openai_manager.chat_completion(
            messages=messages,
            task_type="general",
            temperature=0.3
        )
        
        if result["success"]:
            ai_response = result["response"].choices[0].message.content.strip()
            
            # Check if response should include calendar/time management suggestions
            response_lower = ai_response.lower()
            question_lower = question.lower()
            
            calendar_trigger_words = [
                'thời gian', 'lịch trình', 'deadline', 'kế hoạch', 'nhắc nhở',
                'tổ chức', 'quản lý', 'ưu tiên'
            ]
            
            suggestions = ["Hỏi thêm", "Làm rõ", "Ví dụ", "Chuyển chủ đề"]
            
            if any(word in question_lower or word in response_lower for word in calendar_trigger_words):
                suggestions = ["Mẹo quản lý thời gian", "Kỹ thuật Pomodoro", "Lập kế hoạch học"] + suggestions[:1]
            
            return {
                "answer": ai_response,
                "suggestions": suggestions,
                "ai_mode": "context_aware",
                "model_used": result["model_used"]
            }
        else:
            return {
                "answer": f"Xin lỗi, có lỗi xảy ra: {result.get('error', 'Unknown error')}",
                "suggestions": ["Thử lại", "Hỏi khác", "Đơn giản hóa câu hỏi"],
                "ai_mode": "error"
            }
            
    except Exception as e:
        print(f"[ERROR] Context-aware AI error: {e}")
        return {
            "answer": f"Xin lỗi, có lỗi xảy ra khi xử lý câu hỏi: {str(e)}",
            "suggestions": ["Thử lại", "Hỏi đơn giản hơn"],
            "ai_mode": "error"
        }


# Additional context-aware handlers for specific subjects
def handle_math_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi Toán với context"""
    messages = [{"role": "system", "content": SYSTEM_PROMPTS['math']}]
    if context_messages:
        messages.extend(context_messages[-4:])
    messages.append({"role": "user", "content": question})
    
    result = openai_manager.chat_completion(messages=messages, task_type="math", temperature=0.3)
    if result["success"]:
        return {
            "answer": result["response"].choices[0].message.content.strip(),
            "suggestions": ["Bài tập thêm", "Giải thích chi tiết", "Ví dụ khác"],
            "ai_mode": "math_context"
        }
    return {"answer": "Lỗi xử lý câu hỏi Toán.", "suggestions": ["Thử lại"]}


def handle_programming_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi Lập trình với context"""
    messages = [{"role": "system", "content": SYSTEM_PROMPTS['programming']}]
    if context_messages:
        messages.extend(context_messages[-4:])
    messages.append({"role": "user", "content": question})
    
    result = openai_manager.chat_completion(messages=messages, task_type="programming", temperature=0.2)
    if result["success"]:
        return {
            "answer": result["response"].choices[0].message.content.strip(),
            "suggestions": ["Code example", "Best practices", "Debug help"],
            "ai_mode": "programming_context"
        }
    return {"answer": "Lỗi xử lý câu hỏi Lập trình.", "suggestions": ["Thử lại"]}


# Additional subject handlers with context
def handle_physics_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi Vật lý với context"""
    messages = [{"role": "system", "content": SYSTEM_PROMPTS['physics']}]
    if context_messages:
        messages.extend(context_messages[-4:])
    messages.append({"role": "user", "content": question})
    
    result = openai_manager.chat_completion(messages=messages, task_type="general", temperature=0.3)
    return _format_response_with_fallback(result, "physics_context", ["Thí nghiệm", "Ứng dụng", "Công thức"])


def handle_chemistry_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi Hóa học với context"""
    messages = [{"role": "system", "content": SYSTEM_PROMPTS['chemistry']}]
    if context_messages:
        messages.extend(context_messages[-4:])
    messages.append({"role": "user", "content": question})
    
    result = openai_manager.chat_completion(messages=messages, task_type="general", temperature=0.3)
    return _format_response_with_fallback(result, "chemistry_context", ["Phản ứng", "Thí nghiệm", "Cơ chế"])


def handle_history_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi Lịch sử với context"""
    messages = [{"role": "system", "content": SYSTEM_PROMPTS['history']}]
    if context_messages:
        messages.extend(context_messages[-4:])
    messages.append({"role": "user", "content": question})
    
    result = openai_manager.chat_completion(messages=messages, task_type="general", temperature=0.3)
    return _format_response_with_fallback(result, "history_context", ["Nhân vật", "Sự kiện", "Ý nghĩa"])


def handle_english_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi Tiếng Anh với context"""
    messages = [{"role": "system", "content": SYSTEM_PROMPTS['english']}]
    if context_messages:
        messages.extend(context_messages[-4:])
    messages.append({"role": "user", "content": question})
    
    result = openai_manager.chat_completion(messages=messages, task_type="general", temperature=0.3)
    return _format_response_with_fallback(result, "english_context", ["Grammar", "Vocabulary", "Practice"])


def handle_study_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi Học tập với context"""
    messages = [{"role": "system", "content": SYSTEM_PROMPTS['study']}]
    if context_messages:
        messages.extend(context_messages[-4:])
    messages.append({"role": "user", "content": question})
    
    result = openai_manager.chat_completion(messages=messages, task_type="general", temperature=0.3)
    return _format_response_with_fallback(result, "study_context", ["Kế hoạch", "Phương pháp", "Động lực"])


def handle_time_management_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi Quản lý thời gian với context"""
    messages = [{"role": "system", "content": SYSTEM_PROMPTS['time_management']}]
    if context_messages:
        messages.extend(context_messages[-4:])
    messages.append({"role": "user", "content": question})
    
    result = openai_manager.chat_completion(messages=messages, task_type="general", temperature=0.3)
    return _format_response_with_fallback(result, "time_management_context", ["Lập kế hoạch", "Ưu tiên", "Cân bằng"])


def handle_general_questions_with_context(question, context_messages=None):
    """Xử lý câu hỏi chung với context"""
    messages = [{"role": "system", "content": "Bạn là trợ lý học tập thông minh. Trả lời một cách hữu ích và chính xác."}]
    if context_messages:
        messages.extend(context_messages[-4:])
    messages.append({"role": "user", "content": question})
    
    result = openai_manager.chat_completion(messages=messages, task_type="general", temperature=0.3)
    return _format_response_with_fallback(result, "general_context", ["Hỏi thêm", "Làm rõ", "Chuyển chủ đề"])


def _format_response_with_fallback(result, ai_mode, suggestions):
    """Helper function để format response với fallback"""
    if result["success"]:
        return {
            "answer": result["response"].choices[0].message.content.strip(),
            "suggestions": suggestions,
            "ai_mode": ai_mode
        }
    else:
        return {
            "answer": f"Lỗi xử lý câu hỏi: {result.get('error', 'Unknown error')}",
            "suggestions": ["Thử lại", "Hỏi khác"],
            "ai_mode": "error"
        }


# Study Tools Functions (for future expansion)

