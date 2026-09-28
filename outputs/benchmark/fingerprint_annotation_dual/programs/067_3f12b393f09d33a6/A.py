def find_max(words):
    if not words:
        return ""
    
    max_word = max(words, key=lambda word: (len(set(word)), -ord(word[0]) if word else 0, [-ord(c) for c in word]))
    
    # Better approach: find max unique chars first, then sort those candidates
    max_unique = max(len(set(word)) for word in words)
    candidates = [word for word in words if len(set(word)) == max_unique]
    return min(candidates)
