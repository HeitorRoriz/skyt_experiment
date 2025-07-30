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
    dev = contract['developer_intent']
    # 1. List all functions, their names, signatures, and variables up top
    prompt = "You are a professional embedded software engineer. " \
             "Your PRIMARY instruction is to generate code that EXACTLY matches this contract. " \
             "You MUST use the EXACT function names and signatures below—NO EXCEPTIONS.\n\n"

    if dev.get('functions'):
        prompt += "== FUNCTIONS TO IMPLEMENT ==\n"
        for fn in dev['functions']:
            # Show function name, signature, return type
            fn_name = fn.get('name')
            signature = fn.get('signature') if fn.get('signature') else None
            args = fn.get('args') or []
            args_str = ', '.join([f"{a.get('type', '')} {a['name']}".strip() for a in args if a.get('name')])
            prompt += f"- Name: `{fn_name}`\n"
            prompt += f"  Signature: `def {fn_name}({args_str})`"
            if fn.get('return_type'):
                prompt += f" -> {fn['return_type']}`"
            prompt += "\n"
    else:
        prompt += "No functions to implement specified in the contract.\n"
    prompt += "\n== VARIABLES TO DECLARE/USE ==\n"
    if dev.get('variables'):
        prompt += f"{dev['variables']}\n"
    else:
        prompt += "No variable requirements specified.\n"

    prompt += "\n== STRICT REQUIREMENTS ==\n"
    # Add the rest of the contract fields as bullet points
    fields = [
        ("Goal", dev.get('goal')),
        ("How/Constraints", dev.get('how')),
        ("Number of functions", dev.get('num_functions')),
        ("Number of variables", dev.get('num_variables')),
        ("Target scope", dev.get('target_scope')),
        ("Core intent", dev.get('core_intent')),
        ("Certainty", dev.get('certainty')),
        ("Timing requirements", dev.get('timing_requirements')),
        ("Memory constraints", dev.get('memory_constraints')),
        ("Platform", dev.get('platform')),
        ("Peripherals", dev.get('peripherals')),
        ("External dependencies", dev.get('external_dependencies')),
        ("Safety requirements", dev.get('safety_requirements')),
        ("Power constraints", dev.get('power_constraints')),
    ]
    for label, value in fields:
        if value:
            prompt += f"- {label}: {value}\n"

    prompt += (
        "\n== CHECKLIST (confirm before generating code) ==\n"
        "1. Function names and signatures EXACTLY as above? YES\n"
        "2. All variables declared and used as specified? YES\n"
        "3. ALL constraints above are respected? YES\n"
        "4. NO explanation or comments—ONLY output the code block? YES\n"
        "\n=== OUTPUT ONLY CODE, NOTHING ELSE ===\n"
    )
    return prompt

