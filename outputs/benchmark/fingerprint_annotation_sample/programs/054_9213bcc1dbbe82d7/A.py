def cycpattern_check(a, b):
    if len(b) == 0:
        return False
    return any(b == a[i:i+len(b)] for i in range(len(a))) or any(b == a[i:] + a[:i] for i in range(len(b)))
