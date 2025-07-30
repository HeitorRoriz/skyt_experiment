```python
def fibonacci(n):
    fiblist = [0, 1]
    while len(fiblist) < n:
        fiblist.append(fiblist[-1] + fiblist[-2])
    return fiblist[:n]
```