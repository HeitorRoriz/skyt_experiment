def minPath(grid, k):
    from collections import deque

    n = len(grid)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    min_path = None

    def bfs(start_x, start_y):
        queue = deque([(start_x, start_y, [grid[start_x][start_y]])])
        visited = set([(start_x, start_y)])

        while queue:
            x, y, path = queue.popleft()
            if len(path) == k:
                nonlocal min_path
                if min_path is None or path < min_path:
                    min_path = path
                continue
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < n and 0 <= ny < n:
                    new_path = path + [grid[nx][ny]]
                    queue.append((nx, ny, new_path))

    for i in range(n):
        for j in range(n):
            bfs(i, j)

    return min_path
