def is_happy(s):
    if len(s) < 3:
        return False
    
    for i in range(len(s) - 2):
        # Check if all 3 consecutive characters are distinct
        if len(set(s[i:i+3])) != 3:
            return False
    
    return True
