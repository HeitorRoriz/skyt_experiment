```python
def fibonacci_3():
    fib = [0, 1]
    for i in range(1, 3):
        fib.append(fib[i] + fib[i-1])
    return fib
```