```python
def fibonacci_3(n):
    fib_list = [0, 1, 1]
    for i in range(3, n):
        fib_list.append(fib_list[i-1] + fib_list[i-2])
    return fib_list
```