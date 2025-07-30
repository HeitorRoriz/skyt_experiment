from experiment import run_experiment
from config import EXPERIMENT_TEMPLATES, NUM_RUNS, MODEL, TEMPERATURE, USE_PROMPT_CONTRACT
from user_intent_extract import extract_intent

if __name__ == "__main__":
    for idx, template in enumerate(EXPERIMENT_TEMPLATES):
        # Base task structure
        task = {
            "id": f"prompt-{idx}",
            "model": MODEL,
            "temperature": TEMPERATURE,
            **template
        }
        
        # Add contract-specific fields only if using prompt contracts
        if USE_PROMPT_CONTRACT:
            task.update({
                "intent": extract_intent(template["prompt"]),
                "constraints": ["Use recursion", "No comments", "No explanation", "First 20 Fibonacci numbers"],
                "language": "Python",
                "function_name": "fibonacci",
                "expected_output_type": "list of int",
                "output_format": "code only"
            })
        for run_id in range(1, NUM_RUNS + 1):
            print(f"Running prompt {idx+1}/{len(EXPERIMENT_TEMPLATES)}, run {run_id}/{NUM_RUNS}")
            try:
                run_experiment(task, run_id)
            except Exception as e:
                print(f"Error running experiment for prompt {idx}, run {run_id}: {e}")
