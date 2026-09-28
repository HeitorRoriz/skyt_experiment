# FSE 2027 paper source

ACM research-track draft. The study and the recompute commands are in the repository README.

`main.tex` uses `acmart` with the `acmsmall`, `screen`, `review`, and `anonymous` options. Author names stay commented out until camera-ready.

## Compile

From this folder, with TeX Live or MiKTeX:

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

Figures read by `main.tex`: `fig1.pdf`, `fig_arrows.pdf`, `fig_disagreement.pdf`, `fig_lift.pdf`, and `figures/fig_diversity_signal.pdf`.
