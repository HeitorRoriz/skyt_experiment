def select_words(s, n):
    def count_consonants(word):
        consonants = set('bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ')
        return sum(1 for char in word if char in consonants)

    if not s:
        return []
    
    words = s.split()
    return [word for word in words if count_consonants(word) == n]
