```python
def fibonacci_4():
    fibonacci = [0, 1]
    for i in range(2, 4):
        fibonacci.append(fibonacci[i-1] + fibonacci[i-2])
    return fibonacci
```