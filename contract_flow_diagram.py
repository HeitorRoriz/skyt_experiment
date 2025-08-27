# contract_flow_diagram.py
"""
Visual diagram of SKYT contract checker logic flow
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

def create_contract_flow_diagram():
    """Create a flowchart showing the contract checking logic"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 16))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 20)
    ax.axis('off')
    
    # Define colors
    input_color = '#E3F2FD'      # Light blue
    process_color = '#FFF3E0'    # Light orange  
    decision_color = '#F3E5F5'   # Light purple
    success_color = '#E8F5E8'    # Light green
    failure_color = '#FFEBEE'    # Light red
    
    # Helper function to create boxes
    def create_box(x, y, width, height, text, color, text_size=9):
        box = FancyBboxPatch((x-width/2, y-height/2), width, height,
                           boxstyle="round,pad=0.1", 
                           facecolor=color, edgecolor='black', linewidth=1)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=text_size, 
                wrap=True, bbox=dict(boxstyle="round,pad=0.1", alpha=0))
    
    # Helper function to create arrows
    def create_arrow(x1, y1, x2, y2, label=''):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
        if label:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            ax.text(mid_x + 0.2, mid_y, label, fontsize=8, 
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
    
    # Start
    create_box(5, 19, 2, 0.8, 'INPUT:\nRaw LLM Code', input_color, 10)
    
    # Step 1: Determinism Lint
    create_box(5, 17.5, 3, 1, 'STEP 1:\nDeterminism Lint\n(check violations)', process_color)
    create_arrow(5, 18.6, 5, 18)
    
    # Decision: Violations?
    create_box(5, 16, 2.5, 1, 'Violations\nFound?', decision_color)
    create_arrow(5, 17, 5, 16.5)
    
    # Step 2: Canonicalization
    create_box(5, 14.5, 3, 1, 'STEP 2:\nCanonicalization\n(AST transform)', process_color)
    create_arrow(5, 15.5, 5, 15)
    ax.text(5.5, 15.75, 'NO', fontsize=8, color='green', weight='bold')
    
    # Decision: Canonicalization Success?
    create_box(5, 13, 2.5, 1, 'Canonicalization\nSucceeded?', decision_color)
    create_arrow(5, 14, 5, 13.5)
    
    # Step 3: Oracle Check
    create_box(5, 11.5, 3, 1, 'STEP 3:\nOracle Execution\n(fibonacci20 test)', process_color)
    create_arrow(5, 12.5, 5, 12)
    ax.text(5.5, 12.25, 'YES', fontsize=8, color='green', weight='bold')
    
    # Decision: Oracle Available?
    create_box(3, 10, 2.5, 1, 'Oracle\nAvailable?', decision_color)
    create_box(7, 10, 2.5, 1, 'Pass-through\n(oracle=None)', process_color)
    create_arrow(5, 11, 3, 10.5)
    create_arrow(5, 11, 7, 10.5)
    
    # Oracle execution
    create_box(3, 8.5, 2.5, 1, 'Execute Code\n& Check Output', process_color)
    create_arrow(3, 9.5, 3, 9)
    ax.text(3.5, 9.25, 'YES', fontsize=8, color='green', weight='bold')
    
    # Decision: Oracle Pass?
    create_box(3, 7, 2.5, 1, 'Oracle\nPassed?', decision_color)
    create_arrow(3, 8, 3, 7.5)
    
    # Final Decision Logic
    create_box(5, 5.5, 4, 1.2, 'FINAL CHECK:\nNo violations AND\nCanonicalization OK AND\n(Oracle passed OR None)', decision_color, 8)
    
    # Arrows to final decision
    create_arrow(3, 6.5, 4, 6)
    create_arrow(7, 9.5, 6, 6)
    ax.text(6.5, 9, 'Always True', fontsize=8, color='green', weight='bold')
    
    # Success Path
    create_box(2.5, 3.5, 3, 1.2, 'SUCCESS:\nContract Passed\n+ Canonical Code\n+ Signature', success_color)
    create_arrow(4, 5, 2.5, 4.2)
    ax.text(3, 4.6, 'PASS', fontsize=8, color='green', weight='bold')
    
    # Failure Paths
    create_box(7.5, 3.5, 3, 1.2, 'FAILURE:\nContract Failed\n+ Error Message\n+ Violations', failure_color)
    
    # Failure arrows
    create_arrow(6, 5, 7.5, 4.2)
    ax.text(7, 4.6, 'FAIL', fontsize=8, color='red', weight='bold')
    
    # Failure from violations
    create_arrow(6.25, 16, 8.5, 15)
    create_arrow(8.5, 15, 8.5, 4.2)
    ax.text(6.8, 15.5, 'YES', fontsize=8, color='red', weight='bold')
    
    # Failure from canonicalization
    create_arrow(6.25, 13, 8.5, 12)
    create_arrow(8.5, 12, 8.5, 4.2)
    ax.text(6.8, 12.5, 'NO', fontsize=8, color='red', weight='bold')
    
    # Failure from oracle
    create_arrow(1.75, 7, 1, 6)
    create_arrow(1, 6, 1, 2)
    create_arrow(1, 2, 7.5, 2)
    create_arrow(7.5, 2, 7.5, 2.8)
    ax.text(1.3, 6.5, 'NO', fontsize=8, color='red', weight='bold')
    
    # Output boxes
    create_box(2.5, 1.5, 3, 1, 'OUTPUT:\nContractResult\n(passed=True)', success_color)
    create_box(7.5, 1.5, 3, 1, 'OUTPUT:\nContractResult\n(passed=False)', failure_color)
    
    create_arrow(2.5, 2.9, 2.5, 2.1)
    create_arrow(7.5, 2.9, 7.5, 2.1)
    
    # Title
    ax.text(5, 19.7, 'SKYT Contract Checker Logic Flow', 
           fontsize=16, weight='bold', ha='center')
    
    # Legend
    legend_y = 0.5
    create_box(1.5, legend_y, 1, 0.4, 'Input', input_color, 8)
    create_box(3, legend_y, 1, 0.4, 'Process', process_color, 8)
    create_box(4.5, legend_y, 1, 0.4, 'Decision', decision_color, 8)
    create_box(6, legend_y, 1, 0.4, 'Success', success_color, 8)
    create_box(7.5, legend_y, 1, 0.4, 'Failure', failure_color, 8)
    create_box(9, legend_y, 1, 0.4, 'Output', input_color, 8)
    
    plt.tight_layout()
    plt.savefig('contract_checker_flow.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("Contract checker flow diagram saved as 'contract_checker_flow.png'")

if __name__ == "__main__":
    create_contract_flow_diagram()
