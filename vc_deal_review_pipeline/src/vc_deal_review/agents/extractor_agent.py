# 1. Explicitly import BOTH cast and Optional from typing
from typing import cast, Optional

from vc_deal_review.agents.base_agent import BaseAgent
from vc_deal_review.schema.deal_input import DealInput

# 2. Verify 'utils' (plural) matches your physical directory name exactly
from vc_deal_review.utils.config import get_model_name

class ExtractorAgent(BaseAgent):
    """
    Agent responsible for transforming unstructured text documents from the 
    startup deal package into a structured, validated Pydantic dataset.
    """
    def __init__(self, model_name: Optional[str] = None):
        if model_name is None:
            model_name = get_model_name()
            
        super().__init__(temperature=0.0, model_name=model_name)
        self.structured_llm = self.llm.with_structured_output(DealInput)


    def extract_deal_data(self, unstructured_text: str) -> DealInput:
        """
        Parses raw text data and cleanly maps parameters directly into 
        type-enforced fields (e.g., converting text-based cash metrics into floats).
        """
        system_instruction = (
            "You are an expert VC Analyst specializing in document extraction. "
            "Your objective is to ingest the provided raw text data package from a startup's "
            "pitch materials, financial models, and terms sheets, and map them with 100% precision "
            "into the requested schema. Ensure all currency and numerical figures are extracted "
            "as standard floating-point numbers (e.g., convert '$1.5M' to 1500000.0)."
        )
        
        prompt = f"{system_instruction}\n\nHere is the raw data package:\n{unstructured_text}"
        
        # Invoke the Claude structured extraction pipeline
        result: DealInput = cast(DealInput, self.structured_llm.invoke(prompt))
        return result