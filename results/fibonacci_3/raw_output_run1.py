```python
def fibonacci_3(n):
    fib_list = [0, 1, 1]
    while len(fib_list) < n:
        fib_list.append(fib_list[-1] + fib_list[-2])
    return fib_list
```