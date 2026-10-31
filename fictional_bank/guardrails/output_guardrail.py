import re
from typing import Dict, Any


class OutputGuardrail:
    def __init__(self, mask_emails: bool = False):
        self.mask_emails = mask_emails
        self.leak_patterns = {
            "api_key": re.compile(r"\bsk-[A-Za-z0-9_\-]{10,}"),
            "traceback": re.compile(r"Traceback \(most recent call last\)|File \".+\", line \d+"),
            "secret_name": re.compile(r"\b(OPENAI_API_KEY|LANGSMITH_API_KEY|EVALUATION_API_TOKEN)\b"),
        }
        self.email_pattern = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

    @staticmethod
    def mask(match: re.Match) -> str:
        local_part, domain = match.group(0).split("@", 1)
        return f"{local_part[0]}***@{domain}"

    def check(self, answer: str) -> Dict[str, Any]:
        matched_leaks = [n for n, p in self.leak_patterns.items() if p.search(answer)]
        blocked = bool(matched_leaks)

        safe_answer = answer
        if not blocked and self.mask_emails:
            safe_answer = self.email_pattern.sub(self.mask, answer)

        return {
            "allowed": not blocked,
            "blocked": blocked,
            "matched_leaks": matched_leaks,
            "answer": safe_answer,
            "reason": "Sensitive content detected in the response." if blocked else "Output validation passed.",
        }