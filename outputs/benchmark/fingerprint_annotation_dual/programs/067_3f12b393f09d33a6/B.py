def find_max(words):
    if not words:
        return ""
    
    # Find the maximum number of unique characters
    max_unique = max(len(set(word)) for word in words)
    
    # Filter words that have the maximum number of unique characters
    candidates = [word for word in words if len(set(word)) == max_unique]
    
    # Return the lexicographically smallest one
    return min(candidates)
