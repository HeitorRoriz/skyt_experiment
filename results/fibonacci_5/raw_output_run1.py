```python
def fibonacci_5(n):
    if n <= 1:
        return [0, 1]
    else:
        fib_list = fibonacci_5(n - 1)
        fib_list.append(fib_list[-1] + fib_list[-2])
        return fib_list

result = fibonacci_5(5)
print(result)
```