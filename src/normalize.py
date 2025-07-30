import re

def normalize_code_output(code: str) -> str:
    """
    Normalize Python code for repeatability checks:
    - Remove markdown code block markers (triple backticks, etc.)
    - Remove docstrings (triple quotes)
    - Remove comments
    - Normalize indentation (convert tabs to spaces)
    - Remove blank lines and strip each line
    """
    if not code:
        return ""
    # Remove markdown code block markers (```python ... ```)
    code = re.sub(r"^```(?:python)?\s*", "", code.strip(), flags=re.MULTILINE)
    code = re.sub(r"```$", "", code, flags=re.MULTILINE)
    # Remove docstrings (triple quotes)
    code = re.sub(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', '', code)
    # Remove comments
    code = re.sub(r'#.*', '', code)
    # Normalize indentation: replace tabs with 4 spaces
    code = code.replace('\t', '    ')
    # Remove blank lines and strip each line
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    normalized = '\n'.join(lines)
    return normalized


def extract_code(output):
    match = re.search(r"```python(.*?)```", output, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_reflection(output):
    match = re.search(r"\{.*?\}", output, re.DOTALL)
    return match.group(0).strip() if match else ""

def is_code_compliant(code: str) -> bool:
    uses_recursion = "return" in code and re.search(r"fibonacci\s*\(", code, re.IGNORECASE)
    defines_function = re.search(r"def\s+fibonacci\s*\(", code, re.IGNORECASE)
    # Allow comments since LLMs often add them despite instructions
    return bool(uses_recursion and defines_function)

# Dictionary mapping known variants to canonical string
CANONICAL_INTENT_MAP = {
    # Dev/user intents for Fibonacci
    re.compile(r".*fibonacci.*20.*", re.IGNORECASE): "generate python code for the first 20 fibonacci numbers",
    re.compile(r".*20.*fibonacci.*", re.IGNORECASE): "generate python code for the first 20 fibonacci numbers",
    # Add more canonical mappings as needed
}

# Fallback canonicalization for synonyms
SYNONYM_MAP = [
    (re.compile(r"produce|compute|return|implement|create|write", re.IGNORECASE), "generate"),
    (re.compile(r"function to|function that|function which|function for", re.IGNORECASE), ""),
    (re.compile(r"python code to|python code that|python code for", re.IGNORECASE), "python code to"),
]

FILLER_WORDS = [
    r"a ", r"the ", r"to ", r"that ", r"which ", r"for ", r"of ", r"and ", r"with "
]

def normalize_intent(intent: str) -> str:
    if not intent or not isinstance(intent, str):
        return ""
    s = intent.lower().strip()
    # Remove filler words
    for word in FILLER_WORDS:
        s = s.replace(word, " ")
    # Apply synonym replacements
    for pattern, repl in SYNONYM_MAP:
        s = pattern.sub(repl, s)
    # Canonicalize using regex dictionary
    for pattern, canonical in CANONICAL_INTENT_MAP.items():
        if pattern.match(s):
            return canonical
    # Remove extra whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s

def normalize_intents(intents: dict) -> dict:
    """
    Given a dict with 'developer_intent' and 'user_intent' (each a dict with a 'goal' field),
    normalize both to a canonical string and return a new dict with 'normalized_developer_intent' and 'normalized_user_intent'.
    """
    result = intents.copy()
    if 'developer_intent' in intents and 'goal' in intents['developer_intent']:
        result['normalized_developer_intent'] = normalize_intent(intents['developer_intent']['goal'])
    if 'user_intent' in intents and 'goal' in intents['user_intent']:
        result['normalized_user_intent'] = normalize_intent(intents['user_intent']['goal'])
    return result
