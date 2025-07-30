```python
def fibonacci_4():
    result = [0, 1]
    while len(result) < 4:
        result.append(result[-1] + result[-2])
    return result
```