```python
def fibonacci_3(n):
    fibonacci = [0, 1, 1]
    if n <= 3:
        return fibonacci[:n]
    for i in range(3, n):
        fibonacci.append(fibonacci[-1] + fibonacci[-2] + fibonacci[-3])
    return fibonacci
```