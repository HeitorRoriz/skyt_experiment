```python
def fibonacci_4():
    sequence = [0, 1]
    while len(sequence) < 4:
        sequence.append(sequence[-1] + sequence[-2])
    return sequence
```