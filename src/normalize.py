import re

import re

def normalize_code_output(code: str) -> str:
    # 1. Remove Markdown code fences (``` or ```python, etc.)
    code = re.sub(r'```[\w]*', '', code)
    
    # 2. Remove triple-quoted (multi-line) comments (docstrings)
    code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    
    # 3. Remove single-line comments
    code = re.sub(r'#.*', '', code)
    
    # 4. Remove lines that are 'example usage', 'usage', or just a print of the main object
    cleaned_lines = []
    for line in code.splitlines():
        stripped = line.strip().lower()
        # Remove lines like: example usage, usage, etc.
        if ('example usage' in stripped) or stripped.startswith('usage') or stripped.startswith('print('):
            continue
        if stripped:  # Only keep non-empty lines
            cleaned_lines.append(stripped)
    
    # Join, remove extra blank lines, and lower-case for robustness
    normalized_code = '\n'.join(cleaned_lines).strip()
    return normalized_code

import re

def extract_code(output):
    match = re.search(r"```python(.*?)```", output, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_reflection(output):
    match = re.search(r"\{.*?\}", output, re.DOTALL)
    return match.group(0).strip() if match else ""

def is_code_compliant(code: str) -> bool:
    uses_recursion = "return" in code and re.search(r"fibonacci\s*\(", code)
    defines_function = "def fibonacci" in code
    no_comments = "#" not in code
    return uses_recursion and defines_function and no_comments

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
