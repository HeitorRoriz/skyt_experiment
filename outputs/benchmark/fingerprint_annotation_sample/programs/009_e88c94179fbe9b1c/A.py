def is_nested(string):
    stack = []
    has_nested = False
    
    for char in string:
        if char == '[':
            stack.append(char)
            if len(stack) > 1:
                has_nested = True
        elif char == ']':
            if stack:
                stack.pop()
            else:
                return False
    
    return has_nested and not stack
