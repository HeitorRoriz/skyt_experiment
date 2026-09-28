def is_nested(string):
    # Count consecutive opening brackets from left
    open_count = 0
    max_open = 0
    for char in string:
        if char == '[':
            open_count += 1
            max_open = max(max_open, open_count)
        else:  # char == ']'
            open_count = max(0, open_count - 1)
    
    # Count consecutive closing brackets from right
    close_count = 0
    max_close = 0
    for char in reversed(string):
        if char == ']':
            close_count += 1
            max_close = max(max_close, close_count)
        else:  # char == '['
            close_count = max(0, close_count - 1)
    
    # We need at least depth 2 from both sides
    return max_open >= 2 and max_close >= 2
