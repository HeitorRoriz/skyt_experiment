```python
def fibonacci_3():
    fibonacci = [0, 1]
    for i in range(1, 2):
        fibonacci.append(fibonacci[i] + fibonacci[i-1])
    return fibonacci
```