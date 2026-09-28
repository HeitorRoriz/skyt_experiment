def select_words(s, n):
    if not s:
        return []
    
    vowels = set('aeiouAEIOU')
    
    def count_consonants(word):
        return sum(1 for char in word if char.isalpha() and char not in vowels)
    
    words = s.split()
    return [word for word in words if count_consonants(word) == n]
