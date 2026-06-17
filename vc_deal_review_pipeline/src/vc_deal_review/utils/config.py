import os
from dotenv import load_dotenv

# Automatically load environment variables from the root directory
load_dotenv()

# Centralized Anthropic Model Registry
DEFAULT_LLM_MODEL = "claude-sonnet-4-6"

def get_model_name() -> str:
    """
    Returns the designated active LLM deployment model name.
    """
    return os.getenv("VC_PIPELINE_LLM_MODEL", DEFAULT_LLM_MODEL)

def get_anthropic_api_key() -> str:
    """Retrieves and validates the Anthropic (Claude) API Key footprint."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "CRITICAL EXCEPTION: 'ANTHROPIC_API_KEY' is missing from the system environment variables. "
            "Please ensure it is specified inside your root '.env' file."
        )
    return api_key

