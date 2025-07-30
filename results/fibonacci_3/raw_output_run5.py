```python
def fibonacci_3(n):
    fib_sequence = [0, 1, 1]
    for i in range(3, n):
        fib_sequence.append(fib_sequence[i-1] + fib_sequence[i-2] + fib_sequence[i-3])
    return fib_sequence[:n]
```