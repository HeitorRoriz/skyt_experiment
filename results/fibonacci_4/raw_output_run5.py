```python
def fibonacci_4():
    fib_list = [0, 1]
    while len(fib_list) < 4:
        fib_list.append(fib_list[-1] + fib_list[-2])
    return fib_list
```