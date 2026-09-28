def fruit_distribution(s, n):
    parts = s.split()
    apples = int(parts[0])
    oranges = int(parts[2])
    mangoes = n - apples - oranges
    return mangoes
