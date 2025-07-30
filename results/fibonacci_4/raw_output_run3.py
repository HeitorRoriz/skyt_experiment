```python
def fibonacci_4(n):
    seq = [0, 1]
    n0 = 0
    n1 = 1
    for i in range(58):
        n2 = n0 + n1
        seq.append(n2)
        n0 = n1
        n1 = n2
    return seq[:n]
```