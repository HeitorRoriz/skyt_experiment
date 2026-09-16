"""Zhang–Shasha tree edit distance on Python ASTs. GumTree-style labels.

Insert = delete = 1. Relabel = 0 if labels match else 1.
This is not a GumTree Java port; it is the same *question* (edit script
size on ordered labeled trees). Thresholds are documented, not fitted
to benchmark headlines.
"""

from __future__ import annotations

import ast
from typing import List, Optional, Sequence, Tuple


Label = Tuple[str, str]


def ast_label(node: ast.AST) -> Label:
    if isinstance(node, ast.Name):
        return ("Name", node.id)
    if isinstance(node, ast.Constant):
        return ("Constant", repr(node.value))
    if isinstance(node, ast.arg):
        return ("arg", node.arg)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return (type(node).__name__, node.name)
    if isinstance(node, ast.Attribute):
        return ("Attribute", node.attr)
    return (type(node).__name__, "")


class _T:
    __slots__ = ("label", "children")

    def __init__(self, label: Label, children: Sequence["_T"]):
        self.label = label
        self.children = list(children)


def ast_to_tree(node: ast.AST) -> _T:
    return _T(
        ast_label(node),
        [ast_to_tree(child) for child in ast.iter_child_nodes(node)],
    )


def tree_size(tree: _T) -> int:
    return 1 + sum(tree_size(child) for child in tree.children)


def _postorder(root: _T) -> Tuple[List[_T], List[int], List[int]]:
    """Postorder nodes, leftmost-leaf index per node, keyroot indices."""
    nodes: List[_T] = []
    leftmost: List[int] = []

    def walk(node: _T) -> int:
        child_ids = [walk(child) for child in node.children]
        index = len(nodes)
        if child_ids:
            left = leftmost[child_ids[0]]
        else:
            left = index
        nodes.append(node)
        leftmost.append(left)
        return index

    walk(root)
    keyroots = []
    seen_left = set()
    for index in range(len(nodes) - 1, -1, -1):
        left = leftmost[index]
        if left not in seen_left:
            keyroots.append(index)
            seen_left.add(left)
    keyroots.reverse()
    return nodes, leftmost, keyroots


def zhang_shasha(left: _T, right: _T) -> int:
    """Ordered labeled tree edit distance."""
    if left is right:
        return 0
    a_nodes, a_left, a_kr = _postorder(left)
    b_nodes, b_left, b_kr = _postorder(right)
    n = len(a_nodes)
    m = len(b_nodes)
    tree_dist = [[0] * m for _ in range(n)]

    def forest(i: int, j: int) -> None:
        li = a_left[i]
        lj = b_left[j]
        fd: List[List[int]] = [
            [0] * (j - lj + 2) for _ in range(i - li + 2)
        ]
        for x in range(1, i - li + 2):
            fd[x][0] = fd[x - 1][0] + 1
        for y in range(1, j - lj + 2):
            fd[0][y] = fd[0][y - 1] + 1
        for x in range(1, i - li + 2):
            for y in range(1, j - lj + 2):
                ii = li + x - 1
                jj = lj + y - 1
                if a_left[ii] == li and b_left[jj] == lj:
                    relabel = 0 if a_nodes[ii].label == b_nodes[jj].label else 1
                    fd[x][y] = min(
                        fd[x - 1][y] + 1,
                        fd[x][y - 1] + 1,
                        fd[x - 1][y - 1] + relabel,
                    )
                    tree_dist[ii][jj] = fd[x][y]
                else:
                    p = a_left[ii] - li
                    q = b_left[jj] - lj
                    fd[x][y] = min(
                        fd[x - 1][y] + 1,
                        fd[x][y - 1] + 1,
                        fd[p][q] + tree_dist[ii][jj],
                    )

    for i in a_kr:
        for j in b_kr:
            forest(i, j)
    return tree_dist[n - 1][m - 1]


def ted_and_size(code_a: str, code_b: str) -> Optional[Tuple[int, int, int]]:
    """Return (distance, size_a, size_b) or None if either side does not parse."""
    try:
        tree_a = ast.parse(code_a)
        tree_b = ast.parse(code_b)
    except SyntaxError:
        return None
    left = ast_to_tree(tree_a)
    right = ast_to_tree(tree_b)
    return zhang_shasha(left, right), tree_size(left), tree_size(right)
