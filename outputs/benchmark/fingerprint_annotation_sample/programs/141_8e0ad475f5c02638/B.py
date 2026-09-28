def is_nested(string):
    stack = []
    nested = False
    
    for char in string:
        if char == '[':
            stack.append(char)
            if len(stack) > 1:
                nested = True
        elif char == ']':
            if stack:
                stack.pop()
            else:
                return False
    
    return nested and not stack
