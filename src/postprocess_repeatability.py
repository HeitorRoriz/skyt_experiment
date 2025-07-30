import pandas as pd
from collections import Counter
from config import RESULTS_FILE, NUM_RUNS
from normalize import normalize_code_output
import time
import os
import sys

def is_file_locked(filepath):
    if not os.path.exists(filepath):
        return False
    try:
        with open(filepath, 'rb+'):  # Try to open for reading and writing
            return False
    except IOError:
        return True

def compute_repeatability():
    print(f"[DEBUG] Checking if results file is locked: {RESULTS_FILE}")
    if not os.path.exists(RESULTS_FILE):
        print(f"[ERROR] The results file '{RESULTS_FILE}' does not exist. Please run the experiment first.")
        sys.exit(1)
    if is_file_locked(RESULTS_FILE):
        print(f"[ERROR] The results file '{RESULTS_FILE}' is locked. Please close it in Excel or any other program and try again.")
        sys.exit(1)
    print("[DEBUG] Reading results file...")
    df = pd.read_excel(RESULTS_FILE)
    print("[DEBUG] Results file loaded.")
    summary = []
    repeatability_map = {}

    # We'll recompute normalized_output from raw_output for each row
    df['fresh_normalized_output'] = df['raw_output'].apply(normalize_code_output)

    for prompt, group in df.groupby('prompt'):
        outputs = group['fresh_normalized_output'].tolist()
        count = Counter(outputs)
        most_common_count = count.most_common(1)[0][1] if count else 0
        repeatability_score = most_common_count / len(outputs) if outputs else 0
        repeatability_map[prompt] = repeatability_score
        summary.append({
            'prompt': prompt,
            'repeatability_score': repeatability_score,
            'num_runs': len(outputs),
            'most_common_output_count': most_common_count
        })
    summary_df = pd.DataFrame(summary)
    print("[DEBUG] Writing repeatability summary...")
    summary_df.to_excel('outputs/repeatability_summary.xlsx', index=False)
    print("[DEBUG] Adding repeatability_score to each run in results file...")
    df['repeatability_score'] = df['prompt'].map(repeatability_map)
    df.to_excel(RESULTS_FILE, index=False)
    print("[DEBUG] Done. Repeatability metrics updated.")

# This block checks if the script is being run directly (not imported as a module).
if __name__ == "__main__":
    compute_repeatability()
