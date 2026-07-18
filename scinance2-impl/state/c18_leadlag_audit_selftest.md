# H-18 Methodik-Aequivalenz-Test (c18_leadlag_audit vs. c17_c41_lead_lag)

> Aequivalenz-Test (N=500), KEIN Aufloesungs-Audit — vergleicht die c18-Batch-Pipeline gegen die ORIGINALE c17_c41_lead_lag-Pipeline auf identischem synthetischem Input.

- **Backend:** `torch-cuda` · **N-Surrogates:** 500 · **injizierter Lag:** 3
- **all_point_estimates_match:** ja
- **all_p_values_exact_match:** ja
- **equivalence_holds:** ja

| Variante | TE/Coh original | TE/Coh batched | |diff| | Punkt match | p original | p batched | p exakt | Surrogate-Ensemble bit-identisch |
|---|---:|---:|---:|---|---:|---:|---|---|
| `TE_fwd_lag2` | 0.007680 | 0.007680 | 0.00000000 | ja | 0.656687 | 0.656687 | ja | nein |
| `TE_rev_lag2` | 0.013995 | 0.013995 | 0.00000000 | ja | 0.111776 | 0.111776 | ja | nein |
| `TE_fwd_lag3` | 0.934730 | 0.934730 | 0.00000000 | ja | 0.001996 | 0.001996 | ja | nein |
| `TE_rev_lag3` | 0.009701 | 0.009701 | 0.00000000 | ja | 0.379242 | 0.379242 | ja | nein |
| `WCOH` | 0.942382 | 0.942382 | 0.00000000 | ja | 0.001996 | 0.001996 | ja | nein |
