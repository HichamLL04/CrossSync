import re

def clean_text(text: str) -> str:
    # Remove ASS style tags: {\tag...}
    text = re.sub(r'\{[^}]+\}', '', text)
    # Remove HTML tags: <tag...>
    text = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespace
    return text.strip()
