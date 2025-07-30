```python
def fibonacci_5(i):
    if i in (0, 1):
        return i
    return fibonacci_5(i-1) + fibonacci_5(i-2)

def fibonacci_lst(num_range):
    return [fibonacci_5(i) for i in range(num_range)]
    
print(fibonacci_lst(5))
```