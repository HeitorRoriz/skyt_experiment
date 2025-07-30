import re
import uuid
import hashlib
import datetime
import json
from llm import query_llm  # or call_llm
from config import MODEL, TEMPERATURE

COMMON_PREFIXES = [
    r"write (a|an|the)?\s*",
    r"generate\s*",
    r"create\s*",
    r"implement\s*",
    r"can you\s*",
    r"please\s*",
    r"i want you to\s*",
    r"could you\s*",
    r"i need\s*",
    r"i want\s*",
    r"make\s*",
    r"show (me )?",
]

LANGUAGE_SPECIFIC = [
    r"(a )?python (function|script|code|program)\s*(to|that|which|for)?\s*",
    r"(in )?python\s*",
]

USER_INTENT_PROMPT = '''
Given the following user prompt, extract the user's intent as a JSON object with the following fields:
- goal: What is the user trying to achieve?
- domain: What is the domain or context?
- certainty: Is the intent explicit, implicit, or ambiguous?

User prompt: "{prompt}"

Respond with only the JSON object.
'''

DEV_INTENT_PROMPT = '''
Given the following prompt, extract the developer's intent as a JSON object with the following fields:
- goal: What is the developer being asked to do?
- modifiers: List of any constraints or requirements (e.g., recursion, no comments).
- target_scope: What is the scope (function, module, etc.)?
- core_intent: The main type of intent (e.g., generate_code, refactor_code).
- certainty: Is the intent explicit, implicit, or ambiguous?

Prompt: "{prompt}"

Respond with only the JSON object.
'''

def extract_intent(prompt):
    p = prompt.lower().strip()
    for pattern in COMMON_PREFIXES:
        p = re.sub("^" + pattern, "", p)
    for pattern in LANGUAGE_SPECIFIC:
        p = re.sub("^" + pattern, "", p)
    p = p.strip(" .,:;")
    if p:
        return p[0].upper() + p[1:]
    return ""

# This function is called by extract_intent_components(prompt) in this module,
# specifically as a fallback when LLM-based user intent extraction fails.
def infer_user_goal(prompt):
    if "fibonacci" in prompt.lower():
        return "Compute or display a sequence for user/reference"
    if "email" in prompt.lower():
        return "Notify a user or send information"
    if "dashboard" in prompt.lower():
        return "Provide data visualization for user"
    return "Support an end-user task or workflow"

def infer_domain(prompt):
    p = prompt.lower()
    if "fibonacci" in p or "factorial" in p or "prime" in p or "math" in p or "number" in p:
        return "numerical computation"
    if "email" in p or "mail" in p or "message" in p or "notify" in p:
        return "messaging/communication"
    if "dashboard" in p or "chart" in p or "plot" in p or "visualization" in p or "graph" in p:
        return "data visualization"
    if "file" in p or "document" in p or "pdf" in p or "csv" in p:
        return "document processing"
    if "web" in p or "http" in p or "api" in p:
        return "web development"
    return "general software"

def llm_extract_user_intent(prompt):
    llm_prompt = USER_INTENT_PROMPT.format(prompt=prompt)
    response = query_llm(llm_prompt, model=MODEL, temperature=TEMPERATURE)
    try:
        return json.loads(response)
    except Exception:
        # fallback or error handling
        return {}

def extract_intent_components(prompt):
    # Import here to avoid circular import at module level
    from dev_intent_extract import llm_extract_dev_intent
    # Try LLM-based extraction first
    dev_intent = llm_extract_dev_intent(prompt)
    user_intent = llm_extract_user_intent(prompt)
    # Fallback to heuristics if LLM fails
    if not dev_intent or not isinstance(dev_intent, dict) or 'goal' not in dev_intent:
        dev_intent = {
            "goal": extract_intent(prompt),
            "modifiers": [],
            "target_scope": "function_level",
            "core_intent": "generate_code",
            "certainty": "explicit" if extract_intent(prompt) else "ambiguous"
        }
    if not user_intent or not isinstance(user_intent, dict) or 'goal' not in user_intent:
        user_intent = {
            "goal": infer_user_goal(prompt),
            "domain": infer_domain(prompt),
            "certainty": "implicit"
        }
    return {
        "developer_intent": dev_intent,
        "user_intent": user_intent
    } 