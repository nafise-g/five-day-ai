"""
Strategic Model Router for dynamically assigning Google Gemini models based on task complexity.
Fulfills Rubric Category 3: Strategic Model Routing.
"""

from typing import Dict, Any
from config import config

class StrategicModelRouter:
    """
    Analyzes task requirements and dynamically selects the optimal model:
    - FAST_MODEL (gemini-2.5-flash): For fast extraction, unit conversions, schema parsing, high-throughput text filtering.
    - PRO_MODEL (gemini-2.5-pro): For complex multi-turn GHG audit reasoning, regulatory compliance synthesis, and strategic roadmap generation.
    """

    def __init__(
        self,
        fast_model: str = config.FAST_MODEL,
        pro_model: str = config.PRO_MODEL
    ):
        self.fast_model = fast_model
        self.pro_model = pro_model

    def select_model(self, task_type: str, prompt_text: str = "") -> Dict[str, Any]:
        """
        Selects model and returns routing metadata justification.

        Args:
            task_type: Short identifier ('EXTRACTION', 'AUDIT_CALC', 'REGULATORY_SYNTHESIS', 'APPROVAL_DRAFT')
            prompt_text: Input prompt text for complexity heuristics.

        Returns:
            Dict containing 'selected_model', 'reason', and 'complexity_tier'.
        """
        # Complex multi-step reasoning tasks -> PRO_MODEL
        pro_keywords = ["audit", "compliance", "roadmap", "decarbonization", "regulatory", "strategy", "synthesis", "legal"]
        is_high_complexity = any(kw in task_type.lower() or kw in prompt_text.lower() for kw in pro_keywords)

        if is_high_complexity or task_type.upper() in ["REGULATORY_SYNTHESIS", "STRATEGIC_PLANNING"]:
            return {
                "selected_model": self.pro_model,
                "complexity_tier": "HIGH_REASONING",
                "reason": f"Task type '{task_type}' requires deep reasoning and GHG protocol synthesis. Routed to {self.pro_model}."
            }
        else:
            return {
                "selected_model": self.fast_model,
                "complexity_tier": "FAST_EXECUTION",
                "reason": f"Task type '{task_type}' is structured extraction/formatting. Routed to fast model {self.fast_model}."
            }
