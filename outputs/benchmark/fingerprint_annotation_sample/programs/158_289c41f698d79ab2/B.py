def is_nested(string):
    # Check if we can form a nested structure
    # We need at least 2 '[' followed by at least 2 ']'
    
    # Try to find a valid nested subsequence
    # Scan from left, track opening brackets
    for i in range(len(string)):
        if string[i] == '[':
            # Try to build from here
            open_count = 0
            close_count = 0
            
            # Count opening brackets from position i
            for j in range(i, len(string)):
                if string[j] == '[':
                    open_count += 1
                else:
                    break
            
            # Need at least 2 opening brackets for nesting
            if open_count >= 2:
                # Now look for closing brackets after the opening ones
                for j in range(i + open_count, len(string)):
                    if string[j] == ']':
                        close_count += 1
                        if close_count >= 2:
                            return True
    
    # Try reverse: look for ]] first, then check if there are [[ before
    for i in range(len(string)):
        if string[i] == ']':
            close_count = 0
            open_count = 0
            
            # Count closing brackets from position i
            for j in range(i, len(string)):
                if string[j] == ']':
                    close_count += 1
                else:
                    break
            
            # Need at least 2 closing brackets
            if close_count >= 2:
                # Look for opening brackets before
                for j in range(i - 1, -1, -1):
                    if string[j] == '[':
                        open_count += 1
                        if open_count >= 2:
                            return True
    
    return False
