import os
from pathlib import Path

def count_loc():
    total_lines = 0
    src_lines = 0
    file_counts = []
    
    for py_file in Path('.').rglob('*.py'):
        # Skip venv, test files, and cache
        if ('.venv' in str(py_file) or 'test' in py_file.name.lower() 
            or '__pycache__' in str(py_file)):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                total_lines += lines
                if py_file.name.startswith('src/') or 'src' in str(py_file):
                    src_lines += lines
                file_counts.append((str(py_file), lines))
        except:
            pass
    
    # Sort by lines descending
    file_counts.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Total Python LOC (excl. venv/tests): {total_lines:,}")
    print(f"src/ directory LOC: {src_lines:,}")
    print(f"Total files: {len(file_counts)}")
    print("\nTop 15 files by LOC:")
    for i, (file, lines) in enumerate(file_counts[:15], 1):
        print(f"{i:2d}. {lines:4d} {file}")

if __name__ == "__main__":
    count_loc()
