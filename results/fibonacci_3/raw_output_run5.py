```python
def fibonacci_3(n):
    fib = [0, 1, 1]
    for i in range(3, n):
        fib.append(fib[i-1] + fib[i-2] + fib[i-3])
    return fib[:n]
```