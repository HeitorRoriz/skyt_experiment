```python
def fibonacci_4():
    fib_list = [0, 1]
    for i in range(2, 4):
        fib_list.append(fib_list[i-1] + fib_list[i-2])
    return fib_list
```