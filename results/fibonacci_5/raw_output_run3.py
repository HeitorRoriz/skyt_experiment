```python
def fibonacci_5(n):
    if n <= 1:
        return n
    else:
        return fibonacci_5(n-1) + fibonacci_5(n-2)

def fibonacci_5_list():
    fib_list = []
    for i in range(5):
        fib_list.append(fibonacci_5(i))
    return fib_list
```