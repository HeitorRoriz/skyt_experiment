def check_if_last_char_is_a_letter(txt):
    if len(txt) == 0:
        return False
    
    last_char = txt[-1]
    
    # Check if last character is alphabetical
    if not last_char.isalpha():
        return False
    
    # Check if it's not part of a word
    # It's not part of a word if:
    # - It's the only character, OR
    # - The character before it is a space
    if len(txt) == 1:
        return True
    
    return txt[-2] == ' '
