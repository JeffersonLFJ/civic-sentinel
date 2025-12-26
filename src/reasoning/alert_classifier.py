from typing import Literal

UrgencyLevel = Literal["baixa", "media", "alta"]

class AlertClassifier:
    """
    Classifies the urgency of a document or situation.
    """
    
    async def classify(self, text: str) -> UrgencyLevel:
        """
        Determines urgency based on keywords or LLM analysis.
        """
        text_lower = text.lower()
        
        # Rule-based heuristics (Fast)
        high_urgency_keywords = ["emergência", "risco de vida", "calamidade", "desvio imediato", "perigo eminente"]
        medium_urgency_keywords = ["irregularidade", "suspeita", "atraso", "falta de medicamento"]
        
        for ko in high_urgency_keywords:
            if ko in text_lower:
                return "alta"
                
        for ko in medium_urgency_keywords:
            if ko in text_lower:
                return "media"
                
        return "baixa"

alert_classifier = AlertClassifier()
