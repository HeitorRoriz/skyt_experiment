#!/usr/bin/env python3
"""Compare transformed code with canon to find differences"""

transformed = """def slugify(text):
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'[\\s]+', '-', text)
    return text.strip('-')"""

canon = """def slugify(text):
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'[\\s]+', '-', text)
    return text.strip('-')"""

print("Transformed:")
print(repr(transformed))
print("\nCanon:")
print(repr(canon))
print(f"\nEqual: {transformed == canon}")
print(f"Equal (stripped): {transformed.strip() == canon.strip()}")

# Character by character comparison
trans_lines = transformed.split('\n')
canon_lines = canon.split('\n')

print(f"\nLine count: transformed={len(trans_lines)}, canon={len(canon_lines)}")

for i, (t, c) in enumerate(zip(trans_lines, canon_lines)):
    if t != c:
        print(f"Line {i} differs:")
        print(f"  Trans: {repr(t)}")
        print(f"  Canon: {repr(c)}")
