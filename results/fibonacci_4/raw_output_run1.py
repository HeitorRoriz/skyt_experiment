```python
def fibonacci_4():
    fibonacci_list = [0, 1]
    for i in range(2, 4):
        fibonacci_list.append(fibonacci_list[i-1] + fibonacci_list[i-2])
    return fibonacci_list
```