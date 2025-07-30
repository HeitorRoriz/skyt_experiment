import difflib

def compute_output_delta(raw_code: str, normalized_code: str) -> dict:
    raw_lines = raw_code.strip().splitlines()
    norm_lines = normalized_code.strip().splitlines()

    diff = list(difflib.unified_diff(raw_lines, norm_lines, lineterm=""))
    changed_lines = [line for line in diff if line.startswith('+ ') or line.startswith('- ')]

    similarity = difflib.SequenceMatcher(None, raw_code, normalized_code).ratio()

    return {
        "lines_added": sum(1 for line in diff if line.startswith('+ ') and not line.startswith('+++')),
        "lines_removed": sum(1 for line in diff if line.startswith('- ') and not line.startswith('---')),
        "changed_lines": len(changed_lines),
        "diff": '\n'.join(diff),
        "similarity_score": similarity
    }
