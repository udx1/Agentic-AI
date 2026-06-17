from git import Optional
from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr
from vc_deal_review.utils.config import get_anthropic_api_key, get_model_name

class BaseAgent:
    """Foundational agent wrapper providing unified Claude access and runtime settings."""
    def __init__(self, temperature: float = 0.0, model_name: Optional[str] = None):
        # Fall back to centralized config if no model name is passed explicitly
        if model_name is None:
            model_name = get_model_name()
        
        # Fetching API Key cleanly from centralized configurations
        api_key = get_anthropic_api_key()
        
        # Initializing Claude LLM.
        # Adding 'type: ignore[call-arg]' ensures mypy accepts the underlying LangChain pydantic bindings.
        self.llm = ChatAnthropic(
            model_name=model_name,
            temperature=temperature,
            api_key=SecretStr(api_key),
        )  # type: ignore[call-arg]
