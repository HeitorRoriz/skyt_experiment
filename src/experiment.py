import time
from config import MAX_ATTEMPTS, DELAY_SECONDS, USE_PROMPT_CONTRACT
from intent_extract import extract_dev_intent, extract_user_intent
from contract import create_prompt_contract, build_llm_prompt_for_code
from llm import call_llm, call_llm_simple
from normalizer import extract_code, extract_reflection, is_code_compliant, normalize_code_output
from log import log_results, log_experiment_result
from delta import compute_output_delta


def run_experiment(task, run_id):
    compliant = False
    code = ""
    reflection = ""
    raw_output = ""
    normalized_dev_intent = None
    normalized_user_intent = None
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        if USE_PROMPT_CONTRACT:
            # Use prompt contract mode
            dev_intent = extract_dev_intent(task["prompt"])
            user_intent = extract_user_intent(task["prompt"])
            
            # Create contract structure for LLM
            contract_data = {
                "developer_intent": dev_intent,
                "user_intent": {"goal": user_intent}
            }
            
            # Build prompt using contract structure
            system_message = "You are a professional software engineer. Generate code that fulfills the following contract."
            user_prompt = build_llm_prompt_for_code(contract_data)
            
            # Call LLM with contract structure
            raw_output = call_llm({
                "system_message": system_message,
                "user_prompt": user_prompt
            })
            
            normalized_dev_intent = dev_intent.get("goal", "")
            normalized_user_intent = user_intent
        else:
            # Use simple prompt mode
            raw_output = call_llm_simple(task["prompt"])
        
        reflection = extract_reflection(raw_output)
        code = extract_code(raw_output)
        
        if USE_PROMPT_CONTRACT:
            # TODO: Implement proper contract-based compliance checking
            # For now, accept all attempts since we don't have a proper contract object
            compliant = True  # Placeholder - needs proper contract integration
            log_experiment_result(task["id"], attempt, compliant, code, reflection, normalized_dev_intent, normalized_user_intent)
            break  # Accept first attempt until proper contract system is integrated
        else:
            # Skip compliance checking for simple prompts - always accept first attempt
            compliant = True  # Set to True for logging purposes
            log_experiment_result(task["id"], attempt, compliant, code, reflection, normalized_dev_intent, normalized_user_intent)
            break  # Exit after first attempt when not using contracts

    normalized_output = normalize_code_output(code)
    delta = compute_output_delta(raw_output, normalized_output)
    
    if USE_PROMPT_CONTRACT:
        # Generate final contract log for results
        dev_intent = extract_dev_intent(task["prompt"])
        user_intent = extract_user_intent(task["prompt"])
        
        contract_log = create_prompt_contract(
            prompt=task["prompt"],
            dev_intent=dev_intent,
            user_intent={"goal": user_intent},
            model=task.get("model", "gpt-3.5-turbo"),
            temperature=task.get("temperature", 0.7),
            run_id=run_id,
            raw_output=raw_output,
            normalized_output=normalized_output,
            delta=delta
        )
        log_results(contract_log)
    else:
        # Create a simplified log structure for non-contract mode
        simple_log = {
            "id": f"{task['id']}-{run_id}",
            "timestamp": "",  # Will be filled by log_results if needed
            "model": task.get("model", ""),
            "temperature": task.get("temperature", 0.0),
            "prompt": task["prompt"],
            "run_id": run_id,
            "hash": "",  # Will be computed by log_results if needed
            "raw_output": raw_output,
            "normalized_output": normalized_output,
            "delta": delta,
            "developer_intent": "",
            "user_intent": "",
            "normalized_developer_intent": "",
            "normalized_user_intent": ""
        }
        log_results(simple_log)
    
    return code if compliant else None
