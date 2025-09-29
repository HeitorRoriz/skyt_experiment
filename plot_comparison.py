import json
import matplotlib.pyplot as plt
import numpy as np

def calculate_simple_distance(code1, code2):
    """Calculate simple normalized distance between two code strings"""
    if code1 == code2:
        return 0.0
    
    # Simple Levenshtein-like distance
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    # Normalize both strings
    norm1 = '\n'.join(line.strip() for line in code1.split('\n') if line.strip())
    norm2 = '\n'.join(line.strip() for line in code2.split('\n') if line.strip())
    
    edit_distance = levenshtein_distance(norm1, norm2)
    max_len = max(len(norm1), len(norm2))
    
    return min(1.0, edit_distance / max_len) if max_len > 0 else 0.0

def plot_raw_vs_canonical(skyt_results_file):
    """Plot raw vs canonical distance distributions"""
    with open(skyt_results_file, 'r') as f:
        data = json.load(f)
    
    # Get canonical code for distance calculation
    canon_code = data.get("canon_data", {}).get("canonical_code", "")
    
    # Extract distances
    raw_distances = []
    canonical_distances = []
    
    for result in data.get("transformation_results", []):
        # Calculate raw distance from original code to canon
        original_code = result.get("original_code", "")
        if original_code and canon_code:
            raw_distance = calculate_simple_distance(original_code, canon_code)
            raw_distances.append(raw_distance)
        else:
            raw_distances.append(0)
        
        # Canonical distance (after transformation) 
        canonical_distances.append(result.get("final_distance", 0))
    
    # Create clearer comparison plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Distance from Canon (showing canon as reference point)
    ax1.axvline(x=0, color='green', linewidth=3, alpha=0.8, label='Canon (Perfect Match)')
    
    # Plot raw distances as scatter points
    for i, dist in enumerate(raw_distances):
        ax1.scatter(dist, 0.5, color='red', alpha=0.7, s=100, marker='o')
    
    # Plot canonical distances as scatter points  
    for i, dist in enumerate(canonical_distances):
        ax1.scatter(dist, 1.0, color='blue', alpha=0.7, s=100, marker='s')
    
    ax1.set_xlabel('Distance from Canon')
    ax1.set_ylabel('Output Type')
    ax1.set_title('Distance from Canon (Green Line = Perfect Match)')
    ax1.set_yticks([0.5, 1.0])
    ax1.set_yticklabels(['Raw (Before SKYT)', 'Canonical (After SKYT)'])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-0.05, max(max(raw_distances), max(canonical_distances)) + 0.05)
    
    # Plot 2: Histogram comparison
    ax2.hist(raw_distances, bins=10, alpha=0.6, color='red', 
             label=f'Raw (Mean: {np.mean(raw_distances):.3f})')
    ax2.hist(canonical_distances, bins=10, alpha=0.6, color='blue',
             label=f'Canonical (Mean: {np.mean(canonical_distances):.3f})')
    ax2.axvline(x=0, color='green', linewidth=2, linestyle='--', alpha=0.8, label='Canon')
    
    ax2.set_xlabel('Distance from Canon')
    ax2.set_ylabel('Count')
    ax2.set_title('Distribution Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('raw_vs_canonical_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Raw mean: {np.mean(raw_distances):.3f}")
    print(f"Canonical mean: {np.mean(canonical_distances):.3f}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        plot_raw_vs_canonical(sys.argv[1])
    else:
        print("Usage: python plot_comparison.py <skyt_results.json>")
