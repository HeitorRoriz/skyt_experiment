def cycpattern_check(a, b):
    if len(b) > len(a):
        return False
    return b in (b + b) and any(b[i:i+len(b)] in a for i in range(len(b)))

# Test cases
print(cycpattern_check("abcd", "abd"))  # False
print(cycpattern_check("hello", "ell"))  # True
print(cycpattern_check("whassup", "psus"))  # False
print(cycpattern_check("abab", "baa"))  # True
print(cycpattern_check("efef", "eeff"))  # False
print(cycpattern_check("himenss", "simen"))  # True
