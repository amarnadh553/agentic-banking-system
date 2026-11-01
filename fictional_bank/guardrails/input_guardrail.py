import re
from typing import Dict, Any

class InputGuardrail:
    def __init__(self, blocked_keywords, blocked_phrases):
        
        self.blocked_keywords = blocked_keywords
        self.blocked_phrases = blocked_phrases
        self.keyword_patterns = [re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE) for keyword in self.blocked_keywords]
        self.phrase_patterns = [re.compile(re.escape(phrase), re.IGNORECASE) for phrase in self.blocked_phrases]

    def check(self, user_question: str) -> Dict[str, Any]:
        matched_keywords = []
        matched_phrases = []
        for keyword, pattern in zip(self.blocked_keywords, self.keyword_patterns):
            if pattern.search(user_question):
                matched_keywords.append(keyword)
        for phrase, pattern in zip(self.blocked_phrases, self.phrase_patterns):
            if pattern.search(user_question):
                matched_phrases.append(phrase)
        blocked = bool(matched_keywords or matched_phrases)
        return {
            "allowed": not blocked,
            "blocked": blocked,
            "matched_keywords": matched_keywords,
            "matched_phrases": matched_phrases,
            "reason": ("Restricted input pattern detected." if blocked else "Input validation passed.")
        }