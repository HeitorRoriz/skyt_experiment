def is_nested(string):
    n = len(string)
    
    # For each starting position, try to build valid bracket sequences
    for i in range(n):
        if string[i] == '[':
            # Try to find a valid nested sequence starting here
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
                
                # If we've closed back to 0 and had depth >= 2, we found nesting
                if depth == 0 and max_depth >= 2:
                    return True
    
    # Also check from right to left
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
                
                if depth == 0 and max_depth >= 2:
                    return True
    
    return False
