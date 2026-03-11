# Paper Corrections — v4 (Strict Contract Standards)

> One additional LaTeX change: specify that the strict-compliance variants
> enforce MISRA C and NASA Power of 10 rules.

---

## 1. Section 2.2 — Strict-compliance variants description

**Current:**
```latex
\noindent\textbf{Strict-compliance variants (3):}
    Primality (strict), Binary search (strict), and LRU Cache (strict),
    which impose tighter structural constraints and use higher repair bounds
    (\(k\) up to 15).
```

**Change to:**
```latex
\noindent\textbf{Strict-compliance variants (3):}
    Primality (strict), Binary search (strict), and LRU Cache (strict),
    which impose tighter structural constraints inspired by
    MISRA~C~\cite{misrac2012} and NASA's Power of~10
    rules~\cite{holzmann2006power10}
    (e.g., no \texttt{continue} statements, bounded loops with
    explicit termination, no dynamic imports) and use higher repair bounds
    (\(k\) up to 15).
```

This makes explicit what "tighter structural constraints" means, ties it to the
standards already cited elsewhere in the paper (§3 Related Work, §6 Limitations),
and gives the reader concrete examples of the enforced rules.

---

## Summary

| Priority | Location | Change |
|----------|----------|--------|
| 🟡 Should fix | §2.2 Strict-compliance variants | Name MISRA C and NASA P10 as the standards behind strict contracts |
