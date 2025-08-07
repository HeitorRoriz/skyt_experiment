```python
def fibonacci_3():
    fib_list = [0, 1]
    for i in range(1, 2):
        fib_list.append(fib_list[i] + fib_list[i-1])
    return fib_list
```