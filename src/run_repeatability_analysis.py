# src/run_repeatability_analysis.py

from repeatability import calculate_all_repeatability_scores, save_repeatability_report, export_repeatability_to_excel
import sys

def main():
    """Run repeatability analysis on existing experiment results"""
    print("Running repeatability analysis on existing results...")
    
    try:
        scores = calculate_all_repeatability_scores()
        
        if scores:
            save_repeatability_report(scores)
            excel_file = export_repeatability_to_excel(scores)
            print(f"\nAnalysis complete! Found results for {len(scores)} contracts.")
            
            # Show summary
            total_score = sum(s['score'] for s in scores.values())
            avg_score = total_score / len(scores)
            print(f"Average repeatability score: {avg_score:.2f}")
            print(f"Detailed Excel report: {excel_file}")
            
        else:
            print("No experiment results found. Please run experiments first using main.py or main_with_repeatability.py")
            
    except Exception as e:
        print(f"Error during repeatability analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
