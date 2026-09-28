def find_max(words):
    def unique_char_count(word):
        return len(set(word))
    
    max_word = ""
    max_unique_count = 0
    
    for word in words:
        unique_count = unique_char_count(word)
        if (unique_count > max_unique_count or 
            (unique_count == max_unique_count and word < max_word)):
            max_unique_count = unique_count
            max_word = word
            
    return max_word
