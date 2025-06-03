import openai
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from config import Config

# Khởi tạo OpenAI API key
openai.api_key = Config.OPENAI_API_KEY


class ModelTier(Enum):
    """Phân loại các model theo tier hiệu suất và chi phí"""
    BASIC = "basic"           # GPT-3.5-turbo
    ADVANCED = "advanced"     # GPT-4-turbo
    PREMIUM = "premium"       # GPT-4


@dataclass
class ModelConfig:
    """Cấu hình cho mỗi model OpenAI"""
    name: str
    tier: ModelTier
    max_tokens: int
    cost_per_1k_tokens: float
    context_window: int
    best_for: List[str]
    temperature_default: float = 0.7


class OpenAIModelManager:
    """Quản lý việc lựa chọn và sử dụng model OpenAI"""
    
    # Danh sách các model có sẵn với cấu hình
    AVAILABLE_MODELS = {
        "gpt-3.5-turbo": ModelConfig(
            name="gpt-3.5-turbo",
            tier=ModelTier.BASIC,
            max_tokens=4096,
            cost_per_1k_tokens=0.0015,
            context_window=16385,
            best_for=["chatbot", "basic_qa", "summarization", "translation"],
            temperature_default=0.7
        ),
        "gpt-3.5-turbo-16k": ModelConfig(
            name="gpt-3.5-turbo-16k",
            tier=ModelTier.BASIC,
            max_tokens=4096,
            cost_per_1k_tokens=0.003,
            context_window=16385,
            best_for=["long_documents", "detailed_analysis"],
            temperature_default=0.7
        ),
        "gpt-4": ModelConfig(
            name="gpt-4",
            tier=ModelTier.PREMIUM,
            max_tokens=8192,
            cost_per_1k_tokens=0.03,
            context_window=8192,
            best_for=["complex_reasoning", "coding", "creative_writing"],
            temperature_default=0.7
        ),
        "gpt-4-turbo": ModelConfig(
            name="gpt-4-turbo",
            tier=ModelTier.ADVANCED,
            max_tokens=4096,
            cost_per_1k_tokens=0.01,
            context_window=128000,
            best_for=["large_documents", "complex_analysis", "study_tools"],
            temperature_default=0.7
        ),
        "gpt-4o": ModelConfig(
            name="gpt-4o",
            tier=ModelTier.ADVANCED,
            max_tokens=4096,
            cost_per_1k_tokens=0.005,
            context_window=128000,
            best_for=["multimodal", "image_analysis", "advanced_reasoning"],
            temperature_default=0.7
        ),
        "gpt-4o-mini": ModelConfig(
            name="gpt-4o-mini",
            tier=ModelTier.BASIC,
            max_tokens=16384,
            cost_per_1k_tokens=0.00015,
            context_window=128000,
            best_for=["fast_responses", "simple_tasks", "cost_effective"],
            temperature_default=0.7
        )
    }
    DEFAULT_MODEL = "gpt-4o-mini" 
    
    FALLBACK_CHAIN = [
        "gpt-4o-mini",
        "gpt-3.5-turbo",
        "gpt-4-turbo",
        "gpt-4"    ]
    
    def __init__(self):
        self.current_model = self.DEFAULT_MODEL
        self.failed_models = set()  # Track các model đã fail
        self.rate_limit_tracker = {}  # Track rate limiting
    
    @property
    def default_model(self):
        """Trả về model mặc định hiện tại"""
        return self.DEFAULT_MODEL
    
    def get_model_for_task(self, task_type: str) -> str:
        """Lấy model phù hợp nhất cho task cụ thể - sử dụng model mặc định"""
        return self.DEFAULT_MODEL
    
    def _is_model_available(self, model_name: str) -> bool:
        """Kiểm tra xem model có khả dụng không"""
        # Kiểm tra model có trong danh sách failed
        if model_name in self.failed_models:
            return False
        
        # Kiểm tra rate limiting
        if model_name in self.rate_limit_tracker:
            last_limit_time = self.rate_limit_tracker[model_name]
            if time.time() - last_limit_time < 60:  # chờ 1 phút sau khi rate limit
                return False
        
        return model_name in self.AVAILABLE_MODELS
    
    def _get_fallback_model(self) -> str:
        """Tìm model fallback khả dụng"""
        for model in self.FALLBACK_CHAIN:
            if self._is_model_available(model):
                return model
        
        # Nếu tất cả fail, dùng model đầu tiên trong fallback chain
        return self.FALLBACK_CHAIN[0]
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        task_type: str = "general",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Tạo chat completion với automatic model selection và fallback
        """
        model = self.get_model_for_task(task_type)
        model_config = self.AVAILABLE_MODELS[model]
        
        # Sử dụng temperature mặc định của model nếu không được chỉ định
        if temperature is None:
            temperature = model_config.temperature_default
        
        # Sử dụng max_tokens mặc định của model nếu không được chỉ định
        if max_tokens is None:
            max_tokens = min(model_config.max_tokens, 4096)
        
        # Thử gọi API với model đã chọn
        try:
            print(f"[DEBUG] Using model: {model} for task: {task_type}")
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Reset failed status nếu thành công
            if model in self.failed_models:
                self.failed_models.remove(model)
            
            return {
                "response": response,
                "model_used": model,
                "cost_estimate": self._calculate_cost(response, model_config),
                "success": True
            }
            
        except openai.error.RateLimitError as e:
            print(f"[WARNING] Rate limit hit for {model}: {e}")
            self.rate_limit_tracker[model] = time.time()
            return self._try_fallback(messages, task_type, temperature, max_tokens, **kwargs)
        
        except openai.error.InvalidRequestError as e:
            print(f"[ERROR] Invalid request for {model}: {e}")
            self.failed_models.add(model)
            return self._try_fallback(messages, task_type, temperature, max_tokens, **kwargs)
        
        except Exception as e:
            print(f"[ERROR] Unexpected error with {model}: {e}")
            return {
                "response": None,
                "model_used": model,
                "cost_estimate": 0,
                "success": False,
                "error": str(e)
            }
    
    def _try_fallback(
        self,
        messages: List[Dict[str, str]],
        task_type: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Thử sử dụng model fallback"""
        fallback_model = self._get_fallback_model()
        fallback_config = self.AVAILABLE_MODELS[fallback_model]
        
        try:
            print(f"[DEBUG] Falling back to model: {fallback_model}")
            
            response = openai.ChatCompletion.create(
                model=fallback_model,
                messages=messages,
                temperature=temperature,
                max_tokens=min(max_tokens, fallback_config.max_tokens),
                **kwargs
            )
            
            return {
                "response": response,
                "model_used": fallback_model,
                "cost_estimate": self._calculate_cost(response, fallback_config),
                "success": True,
                "fallback_used": True
            }
            
        except Exception as e:
            print(f"[ERROR] Fallback model {fallback_model} also failed: {e}")
            return {
                "response": None,
                "model_used": fallback_model,
                "cost_estimate": 0,
                "success": False,
                "error": f"All models failed. Last error: {str(e)}"
            }
    
    def _calculate_cost(self, response, model_config: ModelConfig) -> float:
        """Tính toán chi phí ước tính của request"""
        try:
            usage = response.usage
            total_tokens = usage.total_tokens
            cost = (total_tokens / 1000) * model_config.cost_per_1k_tokens
            return round(cost, 6)
        except:
            return 0.0
    
    def get_model_info(self, model_name: str) -> Optional[ModelConfig]:
        """Lấy thông tin về model cụ thể"""
        return self.AVAILABLE_MODELS.get(model_name)
    
    def list_available_models(self, tier: Optional[ModelTier] = None) -> List[str]:
        """Liệt kê các model khả dụng, có thể filter theo tier"""
        if tier:
            return [
                name for name, config in self.AVAILABLE_MODELS.items()
                if config.tier == tier
            ]
        return list(self.AVAILABLE_MODELS.keys())
    
    def get_recommended_model(self, task_type: str, budget_conscious: bool = False) -> str:
        """Đề xuất model tốt nhất cho task, có thể ưu tiên chi phí"""
        if budget_conscious:
            # Ưu tiên model rẻ hơn
            budget_models = self.list_available_models(ModelTier.BASIC)
            for model in budget_models:
                if task_type in self.AVAILABLE_MODELS[model].best_for:
                    return model
            return "gpt-3.5-turbo"
        
        return self.get_model_for_task(task_type)
    
    def reset_failed_models(self):
        """Reset danh sách các model đã fail - dùng khi muốn thử lại"""
        self.failed_models.clear()
        print("[INFO] Reset failed models list")
    
    def get_status(self) -> Dict[str, Any]:
        """Lấy status hiện tại của manager"""
        return {
            "current_model": self.current_model,
            "failed_models": list(self.failed_models),
            "rate_limited_models": list(self.rate_limit_tracker.keys()),
            "available_models": self.list_available_models(),
            "total_models": len(self.AVAILABLE_MODELS)
        }


# Khởi tạo global instance
openai_manager = OpenAIModelManager()


# Convenience functions để sử dụng dễ dàng hơn
def get_ai_response(
    messages: List[Dict[str, str]],
    task_type: str = "general",
    **kwargs
) -> str:
    """
    Convenience function để lấy response từ AI
    Returns: string response hoặc error message
    """
    result = openai_manager.chat_completion(messages, task_type, **kwargs)
    
    if result["success"]:
        return result["response"].choices[0].message.content.strip()
    else:
        return f"Lỗi AI: {result.get('error', 'Unknown error')}"


def get_smart_response(
    prompt: str,
    system_prompt: str = "",
    task_type: str = "general",
    **kwargs
) -> str:
    """
    Convenience function cho single prompt
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    return get_ai_response(messages, task_type, **kwargs)



