```python
def fibonacci_2(n):
    if n <= 1:
        return [n]
    
    next_fibs = fibonacci_2(n - 1)
    next_sum = next_fibs[-1] + (next_fibs[-2] if len(next_fibs) > 1 else 0)
    return next_fibs + [next_sum]
```