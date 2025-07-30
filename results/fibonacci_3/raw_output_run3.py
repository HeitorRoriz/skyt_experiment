```python
def fibonacci_3(n):
    fib_nums = [0, 1, 1]
       
    for i in range(2, n):
        fib_nums.append(fib_nums[-1] + fib_nums[-2] + fib_nums[-3])
        
    return fib_nums
```