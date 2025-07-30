```python
def fibonacci_4():
    fibonacci_series = [0, 1]
    while len(fibonacci_series) < 4:
        fibonacci_series.append(fibonacci_series[-1] + fibonacci_series[-2])
    return fibonacci_series
```ymm