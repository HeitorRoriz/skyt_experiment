import ast
FORBIDDEN_IMPORTS = {"random","numpy.random","secrets","requests"}
FORBIDDEN_CALLS = {("time","sleep"),("uuid",None),("datetime","now")}
def check_determinism_rules(source: str):
    errs = []
    try:
        t = ast.parse(source)
    except Exception as e:
        return [f"Parse error: {e}"]
    for n in ast.walk(t):
        if isinstance(n, ast.AsyncFunctionDef): errs.append("Forbidden async def")
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name in FORBIDDEN_IMPORTS: errs.append(f"Forbidden import: {a.name}")
        if isinstance(n, ast.ImportFrom) and n.module in FORBIDDEN_IMPORTS:
            errs.append(f"Forbidden import: {n.module}")
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name):
                mod, attr = n.func.value.id, n.func.attr
                for m,a in FORBIDDEN_CALLS:
                    if mod==m and (a is None or a==attr):
                        errs.append(f"Forbidden call: {mod}.{attr if a else ''}".rstrip('.'))
            elif isinstance(n.func, ast.Name) and n.func.id in {"sleep"}:
                errs.append("Forbidden call: sleep")
    return errs
