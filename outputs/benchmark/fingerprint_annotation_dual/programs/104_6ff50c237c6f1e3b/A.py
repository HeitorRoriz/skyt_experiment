def is_nested(string):
    n = len(string)
    
    # Try all possible subsequences using bitmask would be too slow
    # Instead, use a greedy approach: try to find valid nested brackets
    
    # Check if we can form a nested structure
    # We need at least 2 opening brackets before we can close them
    
    for i in range(n):
        if string[i] == '[':
            # Try to build a valid nested sequence starting here
            depth = 0
            max_depth = 0
            for j in range(i, n):
                if string[j] == '[':
                    depth += 1
                    max_depth = max(max_depth, depth)
                else:  # ']'
                    depth -= 1
                    if depth < 0:
                        break
            
            # If we reached depth >= 2 and ended with depth 0, we have nesting
            if max_depth >= 2 and depth == 0:
                return True
    
    # Also try from right to left (matching ] with [)
    for i in range(n-1, -1, -1):
        if string[i] == ']':
            depth = 0
            max_depth = 0
            for j in range(i, -1, -1):
                if string[j] == ']':
                    depth += 1
                    max_depth = max(max_depth, depth)
                else:  # '['
                    depth -= 1
                    if depth < 0:
                        break
            
            if max_depth >= 2 and depth == 0:
                return True
    
    return False
