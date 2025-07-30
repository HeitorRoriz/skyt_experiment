import uuid
import hashlib
import datetime
import json
from user_intent_extract import extract_intent_components
from llm import query_llm
from config import MODEL, TEMPERATURE
from normalize import normalize_intents

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

def llm_extract_dev_intent(prompt):
    llm_prompt = DEV_INTENT_PROMPT.format(prompt=prompt)
    response = query_llm(llm_prompt, model=MODEL, temperature=TEMPERATURE)
    try:
        return json.loads(response)
    except Exception:
        # fallback or error handling
        return {}

def get_prompt_contract(task):
    # Extract and normalize intents
    dual_intent = extract_intent_components(task["prompt"])
    normalized = normalize_intents(dual_intent)
    constraints_text = "\n".join([f"- {c}" for c in task.get("constraints", [])])
    checklist = []
    if "function_name" in task and task["function_name"]:
        checklist.append(f"Write a {task['language']} function named {task['function_name']}.")
    if "constraints" in task and task["constraints"]:
        for c in task["constraints"]:
            checklist.append(c)
    if "expected_output_type" in task and task["expected_output_type"]:
        checklist.append(f"It must return a value of type: {task['expected_output_type']}.")
    if "output_format" in task and task["output_format"]:
        checklist.append(f"Output format: {task['output_format']}.")
    checklist_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(checklist)])
    prompt = f"""
You are being given a structured Prompt Contract that describes the user's intent, constraints, input context, and expected output.

Your task:
1. Reflect on the Prompt Contract and acknowledge it in structured form (JSON).
2. Then generate the code accordingly.
3. Do not include any explanation or comments — only the reflection and code.

--- Prompt Contract ---
Original Intent: {task.get('intent', '')}  
Normalized Developer Intent: {normalized.get('normalized_developer_intent', '')}  
Normalized User Intent: {normalized.get('normalized_user_intent', '')}  
Constraints:  
{constraints_text}  
Language: {task.get('language', '')}  
Function name: {task.get('function_name', '')}  
Expected output type: {task.get('expected_output_type', '')}  
------------------------

Expected output:
Step 1: JSON acknowledgment of the contract  
Step 2: Code block that fulfills the contract

--- Checklist ---
{checklist_text}

Confirm each item with YES, then output the code only.
"""
    return {
        "system_message": "You are a professional software engineer. You must follow the Prompt Contract strictly. Think carefully before generating code.",
        "user_prompt": prompt
    }

def generate_prompt_contract(experiment: dict, normalized_output: str, raw_output: str, delta: dict) -> dict:
    contract_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    prompt_hash = hashlib.sha256(experiment["prompt"].encode('utf-8')).hexdigest()
    dual_intent = extract_intent_components(experiment["prompt"])
    normalized = normalize_intents(dual_intent)
    return {
        "id": contract_id,
        "timestamp": timestamp,
        "model": experiment["model"],
        "temperature": experiment["temperature"],
        "prompt": experiment["prompt"],
        "run_id": experiment["run_id"],
        "hash": prompt_hash,
        "raw_output": raw_output,
        "normalized_output": normalized_output,
        "delta": delta,
        "developer_intent": dual_intent["developer_intent"],
        "user_intent": dual_intent["user_intent"],
        "normalized_developer_intent": normalized.get("normalized_developer_intent", ""),
        "normalized_user_intent": normalized.get("normalized_user_intent", "")
    } 