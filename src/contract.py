import uuid
import hashlib
import datetime

def create_prompt_contract(
    prompt, 
    dev_intent, 
    user_intent, 
    model, 
    temperature, 
    run_id,
    raw_output,
    normalized_output,
    delta
):
    contract_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()

    return {
        "id": contract_id,
        "timestamp": timestamp,
        "model": model,
        "temperature": temperature,
        "prompt": prompt,
        "run_id": run_id,
        "hash": prompt_hash,
        "developer_intent": dev_intent,
        "user_intent": user_intent,
        "num_functions": dev_intent.get('num_functions'),
        "functions": dev_intent.get('functions'),
        "num_variables": dev_intent.get('num_variables'),
        "variables": dev_intent.get('variables'),
        "target_scope": dev_intent.get('target_scope'),
        "how": dev_intent.get('how'),
        "core_intent": dev_intent.get('core_intent'),
        "certainty": dev_intent.get('certainty'),
        "timing_requirements": dev_intent.get('timing_requirements'),
        "memory_constraints": dev_intent.get('memory_constraints'),
        "platform": dev_intent.get('platform'),
        "peripherals": dev_intent.get('peripherals'),
        "external_dependencies": dev_intent.get('external_dependencies'),
        "safety_requirements": dev_intent.get('safety_requirements'),
        "power_constraints": dev_intent.get('power_constraints'),
        "raw_output": raw_output,
        "normalized_output": normalized_output,
        "delta": delta
    }

def build_llm_prompt_for_code(contract):
    dev_intent = contract['developer_intent']
    prompt = f"""
You are a professional software engineer. Generate code that fulfills the following contract.

Developer Intent:
- Goal: {dev_intent.get('goal')}
- Constraints/How: {dev_intent.get('how')}
- Functions/methods to implement:
"""
    if dev_intent.get('functions'):
        for fn in dev_intent['functions']:
            prompt += f"    - {fn['name']}("
            if fn.get('args'):
                prompt += ', '.join([a['name'] for a in fn['args'] if a.get('name')])
            prompt += ")"
            if fn.get('return_type'):
                prompt += f" -> {fn['return_type']}"
            prompt += "\n"
    prompt += f"- Number of functions: {dev_intent.get('num_functions')}\n"
    prompt += f"- Variables to use: {dev_intent.get('variables')}\n"
    prompt += f"- Number of variables: {dev_intent.get('num_variables')}\n"
    prompt += f"- Target scope: {dev_intent.get('target_scope')}\n"
    prompt += f"- Core intent: {dev_intent.get('core_intent')}\n"
    prompt += f"- Certainty: {dev_intent.get('certainty')}\n"
    prompt += f"- Timing requirements: {dev_intent.get('timing_requirements')}\n"
    prompt += f"- Memory constraints: {dev_intent.get('memory_constraints')}\n"
    prompt += f"- Platform: {dev_intent.get('platform')}\n"
    prompt += f"- Peripherals: {dev_intent.get('peripherals')}\n"
    prompt += f"- External dependencies: {dev_intent.get('external_dependencies')}\n"
    prompt += f"- Safety requirements: {dev_intent.get('safety_requirements')}\n"
    prompt += f"- Power constraints: {dev_intent.get('power_constraints')}\n"

    prompt += "\nThe code should strictly follow these requirements. Do not include any explanation or comments. Only output code.\n"
    return prompt
