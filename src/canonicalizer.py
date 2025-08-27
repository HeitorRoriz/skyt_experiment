import ast, hashlib
from typing import Optional, Tuple

class DocstringStripper(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), (ast.Str, ast.Constant)):
            node.body = node.body[1:]
        return node
    def visit_ClassDef(self, node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(getattr(node.body[0], "value", None), (ast.Str, ast.Constant)):
            node.body = node.body[1:]
        return node

def _strip_module_docstring(tree: ast.AST) -> ast.AST:
    if isinstance(tree, ast.Module) and tree.body:
        first = tree.body[0]
        if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), (ast.Str, ast.Constant)):
            tree.body = tree.body[1:]
    return tree

def canonicalize_python(source: str, enforce_function_name: Optional[str] = None) -> Tuple[str,str,bool]:
    try:
        tree = ast.parse(source)
    except Exception:
        canon = " ".join(source.split())
        return canon, hashlib.sha256(canon.encode()).hexdigest(), False
    tree = _strip_module_docstring(tree)
    tree = DocstringStripper().visit(tree)
    ast.fix_missing_locations(tree)
    if enforce_function_name:
        for n in tree.body:
            if isinstance(n, ast.FunctionDef):
                n.name = enforce_function_name
                break
    try:
        canon = ast.unparse(tree); ok = True
    except Exception:
        canon = " ".join(source.split()); ok = False
    return canon, hashlib.sha256(canon.encode()).hexdigest(), ok
