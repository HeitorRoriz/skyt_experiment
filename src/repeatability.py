# src/repeatability.py

import os
import json
import pandas as pd
from collections import defaultdict
from config import RESULTS_DIR
from contract import PromptContract

def normalize_code_for_comparison(code):
    """Normalize code for comparison by removing whitespace and comments"""
    if not code:
        return ""
    
    # Remove leading/trailing whitespace and normalize line endings
    lines = [line.strip() for line in code.strip().split('\n')]
    # Remove empty lines and comments
    normalized_lines = []
    for line in lines:
        if line and not line.startswith('#'):
            normalized_lines.append(line)
    
    return '\n'.join(normalized_lines)

def load_run_statuses(contract_name):
    """Load the status of each run (raw, normalized, rescued, failed)"""
    contract_dir = os.path.join(RESULTS_DIR, contract_name)
    if not os.path.exists(contract_dir):
        return []
    
    statuses = []
    for filename in os.listdir(contract_dir):
        if filename.startswith("final_status_run") and filename.endswith(".txt"):
            filepath = os.path.join(contract_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    status = f.read().strip()
                    statuses.append(status)
            except Exception:
                statuses.append("unknown")
    
    return statuses

def load_experiment_outputs(contract_name):
    """Load all final outputs for a specific contract from results directory"""
    outputs = []
    
    # Look for final output files for this contract in subdirectory
    contract_dir = os.path.join(RESULTS_DIR, contract_name)
    if not os.path.exists(contract_dir):
        print(f"Contract directory '{contract_dir}' does not exist")
        return outputs
    
    # Find all final_run*.py files for this contract
    # These represent the final working code (raw, normalized, or rescued)
    for filename in os.listdir(contract_dir):
        if filename.startswith("final_run") and filename.endswith(".py"):
            filepath = os.path.join(contract_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # Only include non-empty outputs
                        outputs.append(content)
            except Exception as e:
                print(f"Warning: Could not read {filepath}: {e}")
    
    return outputs

def calculate_repeatability_score(contract_name):
    """Calculate repeatability score for a specific contract"""
    outputs = load_experiment_outputs(contract_name)
    
    if len(outputs) == 0:
        return 0.0, 0, "No outputs found"
    
    if len(outputs) == 1:
        return 1.0, 1, "Only one output found"
    
    # Normalize outputs for comparison
    normalized_outputs = [normalize_code_for_comparison(output) for output in outputs]
    
    # Count unique outputs
    unique_outputs = set(normalized_outputs)
    
    # Find the most common output
    output_counts = defaultdict(int)
    for output in normalized_outputs:
        output_counts[output] += 1
    
    # Get the count of the most frequent output
    max_count = max(output_counts.values()) if output_counts else 0
    
    # Calculate repeatability score as #equal_outputs/#runs
    total_runs = len(outputs)
    repeatability_score = max_count / total_runs if total_runs > 0 else 0.0
    
    return repeatability_score, max_count, f"{max_count}/{total_runs} outputs were identical"

def calculate_all_repeatability_scores():
    """Calculate repeatability scores for all contracts"""
    if not os.path.exists(RESULTS_DIR):
        print(f"Results directory '{RESULTS_DIR}' does not exist")
        return {}
    
    # Find all contract names from subdirectories
    contract_names = set()
    for item in os.listdir(RESULTS_DIR):
        item_path = os.path.join(RESULTS_DIR, item)
        if os.path.isdir(item_path):
            # Check if this directory contains final_run*.py files
            has_final_files = any(
                f.startswith("final_run") and f.endswith(".py")
                for f in os.listdir(item_path)
            )
            if has_final_files:
                contract_names.add(item)
    
    scores = {}
    print("\n" + "="*60)
    print("REPEATABILITY SCORES")
    print("="*60)
    
    for contract_name in sorted(contract_names):
        score, equal_count, description = calculate_repeatability_score(contract_name)
        scores[contract_name] = {
            'score': score,
            'equal_outputs': equal_count,
            'description': description
        }
        
        print(f"Contract: {contract_name}")
        print(f"  Repeatability Score: {score:.2f} ({description})")
        print()
    
    # Calculate overall average
    if scores:
        avg_score = sum(s['score'] for s in scores.values()) / len(scores)
        print(f"Overall Average Repeatability Score: {avg_score:.2f}")
        print("="*60)
    
    return scores

def save_repeatability_report(scores, output_file="outputs/repeatability_report.json"):
    """Save repeatability scores to a JSON report file"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    report = {
        "timestamp": str(os.path.getctime(RESULTS_DIR)) if os.path.exists(RESULTS_DIR) else "unknown",
        "contracts": scores,
        "summary": {
            "total_contracts": len(scores),
            "average_score": sum(s['score'] for s in scores.values()) / len(scores) if scores else 0.0
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Repeatability report saved to: {output_file}")

def load_contract_details(contract_name):
    """Load contract details from the contract JSON file"""
    contract_dir = os.path.join(RESULTS_DIR, contract_name)
    contract_file = os.path.join(contract_dir, "contract.json")
    
    if os.path.exists(contract_file):
        try:
            contract = PromptContract.from_json(contract_file)
            return contract
        except Exception as e:
            print(f"Warning: Could not load contract from {contract_file}: {e}")
    
    return None

def get_original_prompt_from_contract(contract):
    """Extract or reconstruct the original prompt from contract details"""
    if not contract:
        return "Unknown prompt"
    
    # Try to reconstruct a meaningful prompt from contract details
    prompt_parts = []
    
    if contract.required_logic == "recursion":
        prompt_parts.append("Write a recursive Python function")
    else:
        prompt_parts.append("Write a Python function")
    
    if contract.function_name != "fibonacci":
        prompt_parts.append(f"named {contract.function_name}")
    
    # Add constraints info
    if "first 20 numbers" in contract.constraints:
        prompt_parts.append("to generate the first 20 Fibonacci numbers")
    
    if "return as list" in contract.constraints:
        prompt_parts.append("and return them as a list")
    
    return " ".join(prompt_parts) + "."

def export_repeatability_to_excel(scores, output_file="outputs/repeatability_detailed_report.xlsx"):
    """Export detailed repeatability analysis to Excel file"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    detailed_data = []
    
    for contract_name, score_info in scores.items():
        # Load contract details
        contract = load_contract_details(contract_name)
        
        # Get original prompt
        original_prompt = get_original_prompt_from_contract(contract)
        
        # Get contract details as string
        contract_details = ""
        if contract:
            contract_dict = contract.to_dict()
            contract_details = json.dumps(contract_dict, indent=2)
        
        # Load all outputs and statuses for this contract
        outputs = load_experiment_outputs(contract_name)
        statuses = load_run_statuses(contract_name)
        
        # Normalize outputs for comparison
        normalized_outputs = [normalize_code_for_comparison(output) for output in outputs]
        
        # Count occurrences of each unique output
        output_counts = defaultdict(int)
        for output in normalized_outputs:
            output_counts[output] += 1
        
        # Get the most common output count
        max_count = max(output_counts.values()) if output_counts else 0
        
        # Calculate status statistics
        status_counts = defaultdict(int)
        for status in statuses:
            status_counts[status] += 1
        
        # Prepare code columns (up to 10 runs)
        code_columns = {}
        status_columns = {}
        for i, output in enumerate(outputs[:10]):  # Limit to 10 runs for Excel readability
            code_columns[f'Code_Run_{i+1}'] = output
            status_columns[f'Status_Run_{i+1}'] = statuses[i] if i < len(statuses) else "unknown"
        
        # Fill empty columns if fewer than 10 runs
        for i in range(len(outputs), 10):
            code_columns[f'Code_Run_{i+1}'] = ""
            status_columns[f'Status_Run_{i+1}'] = ""
        
        # Create status summary
        status_summary = f"Raw: {status_counts.get('raw', 0)}, Normalized: {status_counts.get('normalized', 0)}, Rescued: {status_counts.get('rescued', 0)}, Failed: {status_counts.get('failed', 0)}"
        
        # Create row data
        row_data = {
            'Contract_Name': contract_name,
            'Original_Prompt': original_prompt,
            'Contract_Details': contract_details,
            'Total_Runs': len(outputs),
            'Similar_Code_Count': max_count,
            'Repeatability_Score': score_info['score'],
            'Score_Description': score_info['description'],
            'Status_Summary': status_summary,
            'Rescued_Count': status_counts.get('rescued', 0),
            **code_columns,
            **status_columns
        }
        
        detailed_data.append(row_data)
    
    # Create DataFrame and export to Excel
    df = pd.DataFrame(detailed_data)
    
    # Reorder columns for better readability
    column_order = [
        'Contract_Name', 'Original_Prompt', 'Contract_Details',
        'Total_Runs', 'Similar_Code_Count', 'Repeatability_Score', 'Score_Description',
        'Status_Summary', 'Rescued_Count'
    ] + [f'Code_Run_{i+1}' for i in range(10)] + [f'Status_Run_{i+1}' for i in range(10)]
    
    df = df.reindex(columns=column_order)
    
    # Export to Excel with formatting
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Repeatability_Analysis', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Repeatability_Analysis']
        
        # Adjust column widths
        worksheet.column_dimensions['A'].width = 20  # Contract_Name
        worksheet.column_dimensions['B'].width = 50  # Original_Prompt
        worksheet.column_dimensions['C'].width = 40  # Contract_Details
        worksheet.column_dimensions['D'].width = 15  # Total_Runs
        worksheet.column_dimensions['E'].width = 20  # Similar_Code_Count
        worksheet.column_dimensions['F'].width = 20  # Repeatability_Score
        worksheet.column_dimensions['G'].width = 30  # Score_Description
        
        # Adjust code column widths
        for i in range(10):
            col_letter = chr(ord('H') + i)  # H, I, J, K, L, M, N, O, P, Q
            worksheet.column_dimensions[col_letter].width = 25
    
    print(f"Detailed repeatability report exported to Excel: {output_file}")
    return output_file

if __name__ == "__main__":
    scores = calculate_all_repeatability_scores()
    if scores:
        save_repeatability_report(scores)
        export_repeatability_to_excel(scores)
