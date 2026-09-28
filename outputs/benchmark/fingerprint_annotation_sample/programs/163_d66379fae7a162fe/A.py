def minPath(grid, k):
    from collections import deque

    N = len(grid)
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    min_path = None

    def bfs(start_i, start_j):
        queue = deque([(start_i, start_j, [grid[start_i][start_j]])])
        while queue:
            i, j, path = queue.popleft()
            if len(path) == k:
                nonlocal min_path
                if min_path is None or path < min_path:
                    min_path = path
                continue
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < N and 0 <= nj < N:
                    queue.append((ni, nj, path + [grid[ni][nj]]))

    for i in range(N):
        for j in range(N):
            bfs(i, j)

    return min_path
