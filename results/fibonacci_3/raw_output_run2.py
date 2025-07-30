```python
def fibonacci_3(n):
    fibonacci_list = [0, 1, 1]
    for i in range(3, n):
        fibonacci_list.append(fibonacci_list[i-1] + fibonacci_list[i-2])
    return fibonacci_list[:n]
```