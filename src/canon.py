# src/canon.py
"""
Canonicalization module for SKYT pipeline
Handles code normalization with configurable policies
"""

import ast
import re
import hashlib
import json
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class CanonPolicy:
    """Canonicalization policy configuration"""
    strip_fences: bool = True
    strip_docstrings: bool = True
    strip_comments: bool = True
    normalize_ws: bool = True
    format_black: bool = False  # Future: black formatting
    sort_imports: bool = False  # Future: import sorting
    ident_normalize: bool = True  # Normalize function names


@dataclass
class FoundationalSignature:
    """Foundational signature for anchor canonicalization"""
    struct: str  # AST-normalized hash
    sem: str     # Oracle outputs hash
    effect: str  # Effect signature from compliance
    env: str     # Environment/config hash
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "struct": self.struct,
            "sem": self.sem, 
            "effect": self.effect,
            "env": self.env
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'FoundationalSignature':
        return cls(
            struct=data["struct"],
            sem=data["sem"],
            effect=data["effect"],
            env=data["env"]
        )


def apply_canon(code: str, policy: CanonPolicy, oracle_outputs: Optional[List[Any]] = None, 
               effect_signature: Optional[str] = None, env_hash: Optional[str] = None) -> Dict[str, Any]:
    """
    Apply canonicalization transformations to code
    
    Args:
        code: Raw Python code string
        policy: Canonicalization policy
    
    Returns:
        Dict with canon_code, signature, structural_ok, notes
    """
    if not code or not code.strip():
        return {
            "canon_code": "",
            "signature": "",
            "structural_ok": False,
            "notes": "Empty input code"
        }
    
    notes = []
    
    try:
        # Step 1: Strip fences if enabled
        if policy.strip_fences:
            code = _strip_code_fences(code)
            notes.append("stripped_fences")
        
        # Step 2: Parse AST to validate syntax
        tree = ast.parse(code)
        
        # Step 3: Apply AST transformations
        if policy.strip_docstrings:
            tree = _strip_docstrings(tree)
            notes.append("stripped_docstrings")
        
        if policy.ident_normalize:
            tree = _normalize_function_names(tree)
            notes.append("normalized_identifiers")
        
        # Step 4: Generate canonical code
        canon_code = ast.unparse(tree)
        
        # Step 5: Apply text-level transformations
        if policy.strip_comments:
            canon_code = _strip_comments(canon_code)
            notes.append("stripped_comments")
        
        if policy.normalize_ws:
            canon_code = _normalize_whitespace(canon_code)
            notes.append("normalized_whitespace")
        
        # Generate foundational signature
        foundational_sig = compute_foundational_signature(
            canon_code, policy, oracle_outputs, effect_signature, env_hash
        )
        
        # Legacy signature for backward compatibility
        signature = canon_hash(canon_code, policy)
        
        return {
            "canon_code": canon_code,
            "signature": signature,
            "foundational_signature": foundational_sig,
            "structural_ok": True,
            "notes": "; ".join(notes)
        }
        
    except (SyntaxError, ValueError) as e:
        # Fallback cleanup for invalid syntax
        fallback_code = _fallback_cleanup(code, policy)
        fallback_sig = compute_foundational_signature(
            fallback_code, policy, oracle_outputs, effect_signature, env_hash
        )
        return {
            "canon_code": fallback_code,
            "signature": canon_hash(fallback_code, policy),
            "foundational_signature": fallback_sig,
            "structural_ok": False,
            "notes": f"syntax_error_fallback: {str(e)}"
        }


def canon_hash(code: str, policy: CanonPolicy) -> str:
    """Generate canonical hash signature for code"""
    # Include policy in hash to ensure different policies produce different signatures
    policy_str = f"{policy.strip_fences}{policy.strip_docstrings}{policy.strip_comments}{policy.normalize_ws}{policy.ident_normalize}"
    combined = f"{code}|{policy_str}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]


def _strip_code_fences(code: str) -> str:
    """Remove markdown code fences and language specifiers"""
    # Remove opening fence with optional language
    code = re.sub(r'^```(?:python|py)?\s*\n', '', code, flags=re.MULTILINE)
    # Remove closing fence
    code = re.sub(r'\n```\s*$', '', code, flags=re.MULTILINE)
    return code.strip()


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    """Remove docstrings from AST nodes"""
    class DocstringRemover(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if (node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:]
            return self.generic_visit(node)
        
        def visit_ClassDef(self, node):
            if (node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
                node.body = node.body[1:]
            return self.generic_visit(node)
    
    return DocstringRemover().visit(tree)


def _normalize_function_names(tree: ast.AST) -> ast.AST:
    """Normalize function names to canonical forms"""
    class FunctionNormalizer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            # Normalize common fibonacci function names
            if node.name in ['fib', 'fibonacci', 'fibo', 'fibonacci_sequence']:
                node.name = 'fibonacci'
            return self.generic_visit(node)
    
    return FunctionNormalizer().visit(tree)


def _strip_comments(code: str) -> str:
    """Remove Python comments from code"""
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Simple comment removal (doesn't handle strings with # correctly)
        if '#' in line:
            line = line[:line.index('#')]
        cleaned_lines.append(line.rstrip())
    
    return '\n'.join(cleaned_lines)


def _normalize_whitespace(code: str) -> str:
    """Normalize whitespace and remove empty lines"""
    lines = code.split('\n')
    normalized_lines = []
    
    for line in lines:
        stripped = line.rstrip()
        if stripped:  # Skip empty lines
            normalized_lines.append(stripped)
    
    return '\n'.join(normalized_lines)


def _fallback_cleanup(code: str, policy: CanonPolicy) -> str:
    """Fallback cleanup when AST parsing fails"""
    if policy.strip_fences:
        code = _strip_code_fences(code)
    
    if policy.strip_comments:
        code = _strip_comments(code)
    
    if policy.normalize_ws:
        code = _normalize_whitespace(code)
    
    return code


def compute_foundational_signature(code: str, policy: CanonPolicy, 
                                 oracle_outputs: Optional[List[Any]] = None,
                                 effect_signature: Optional[str] = None,
                                 env_hash: Optional[str] = None) -> FoundationalSignature:
    """
    Compute foundational signature with struct, sem, effect, env components
    
    Args:
        code: Canonical code string
        policy: Canonicalization policy
        oracle_outputs: Oracle test outputs for semantic signature
        effect_signature: Effect signature from compliance checking
        env_hash: Environment configuration hash
    
    Returns:
        FoundationalSignature object
    """
    # Sig_struct: AST-normalized hash
    struct_hash = _compute_structural_hash(code)
    
    # Sig_sem: Oracle outputs hash
    sem_hash = _compute_semantic_hash(oracle_outputs) if oracle_outputs else "no_oracle"
    
    # Sig_effect: Effect signature from compliance
    effect_hash = effect_signature or "no_effects"
    
    # Sig_env: Environment/config hash
    env_sig = env_hash or _compute_env_hash(policy)
    
    return FoundationalSignature(
        struct=struct_hash,
        sem=sem_hash,
        effect=effect_hash,
        env=env_sig
    )


def compute_distance(output_sig: FoundationalSignature, anchor_sig: FoundationalSignature,
                    weights: Optional[Dict[str, float]] = None) -> float:
    """
    Compute weighted distance between output signature and anchor signature
    
    Args:
        output_sig: Signature from current run
        anchor_sig: Anchor signature (from first successful run)
        weights: Component weights (w_struct, w_sem, w_effect, w_env)
    
    Returns:
        Distance score (0.0 if identical, higher for more different)
    """
    if weights is None:
        weights = {"w_struct": 0.4, "w_sem": 0.3, "w_effect": 0.2, "w_env": 0.1}
    
    # Binary distance for each component (0 if same, 1 if different)
    struct_dist = 0.0 if output_sig.struct == anchor_sig.struct else 1.0
    sem_dist = 0.0 if output_sig.sem == anchor_sig.sem else 1.0
    effect_dist = 0.0 if output_sig.effect == anchor_sig.effect else 1.0
    env_dist = 0.0 if output_sig.env == anchor_sig.env else 1.0
    
    # Weighted sum
    distance = (
        weights["w_struct"] * struct_dist +
        weights["w_sem"] * sem_dist +
        weights["w_effect"] * effect_dist +
        weights["w_env"] * env_dist
    )
    
    return distance


def _compute_structural_hash(code: str) -> str:
    """Compute structural hash from AST representation"""
    try:
        tree = ast.parse(code)
        # Use AST dump for structural representation
        ast_str = ast.dump(tree, annotate_fields=False, include_attributes=False)
        return hashlib.sha256(ast_str.encode('utf-8')).hexdigest()[:16]
    except (SyntaxError, ValueError):
        # Fallback to text hash for invalid syntax
        return hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]


def _compute_semantic_hash(oracle_outputs: List[Any]) -> str:
    """Compute semantic hash from oracle test outputs"""
    if not oracle_outputs:
        return "empty_oracle"
    
    # Serialize outputs to stable string representation
    outputs_str = json.dumps(oracle_outputs, sort_keys=True, default=str)
    return hashlib.sha256(outputs_str.encode('utf-8')).hexdigest()[:16]


def _compute_env_hash(policy: CanonPolicy) -> str:
    """Compute environment hash from canonicalization policy"""
    policy_dict = {
        "strip_fences": policy.strip_fences,
        "strip_docstrings": policy.strip_docstrings,
        "strip_comments": policy.strip_comments,
        "normalize_ws": policy.normalize_ws,
        "format_black": policy.format_black,
        "sort_imports": policy.sort_imports,
        "ident_normalize": policy.ident_normalize
    }
    policy_str = json.dumps(policy_dict, sort_keys=True)
    return hashlib.sha256(policy_str.encode('utf-8')).hexdigest()[:16]
