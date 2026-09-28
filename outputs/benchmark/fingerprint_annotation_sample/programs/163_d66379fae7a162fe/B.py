def minPath(grid, k):
    from collections import deque

    N = len(grid)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    result = []

    def bfs(start_x, start_y):
        queue = deque([(start_x, start_y, [grid[start_x][start_y]])])
        best_path = None
        
        while queue:
            x, y, path = queue.popleft()
            if len(path) == k:
                if best_path is None or path < best_path:
                    best_path = path
                continue
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < N and 0 <= ny < N:
                    queue.append((nx, ny, path + [grid[nx][ny]]))
        
        return best_path

    for i in range(N):
        for j in range(N):
            current_path = bfs(i, j)
            if current_path is not None:
                if not result or current_path < result:
                    result = current_path

    return result
