# C-01 OFI-Vorzeichen INVERSE Lesart — H-05b OOS-Konfirmation (KAPITALFREI)

- **Hypothese:** H-05b — `scinance2-impl/state/hypothesis_registry.md` (+ DEC-15)
- **Erzeugt:** 2026-06-30T09:11:36+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/bybit/publicTrade (windows 2026-04-15 + 2026-05-15)` (Symbole: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT)
- **Fenster (vorregistriert):** A@2026-04-15, B@2026-05-15 · je 300000 Ticks/Symbol
- **delta-Lags:** [1, 5, 15, 60, 300] s · **Grid:** 1000 ms · **Surrogates:** 200 · **Seed:** 42
- **FDR-Familie:** F-OFI-INV · **BH-FDR alpha:** 0.1 · **p_crit:** 0.0199
- **Entdeckungszelle ausgeschlossen (per Konstruktion):** ETHUSDT / June-collector w0 / delta=1s (not present in April-May OOS)
- **KAPITALFREI:** ja — reiner Vorzeichen-/Korrelations-Test, keine bps/Edge/PnL.

> Gate-Urteil faellt der gate-auditor gegen H-05b. WEITER (inverse Mess-Existenz) verlangt: sign=- UND p<=0.05 (BH-FDR F-OFI-INV) UND inverse-Konsistenz in >=2 disjunkten Fenstern (Entdeckungszelle ausgeschlossen) UND |corr|>=0.05 ODER Hit-Rate<=0.47. Hartes Ein-Fenster-DROP, kein GRAUBEREICH.

## Inverse-Konsistenz je (Symbol, delta) — Gate-Kern

| Symbol | delta (s) | Fenster gemessen | Fenster inverse-sig | inverse-Fenster | inverse-konsistent (>=2) |
|---|---:|---:|---:|---|---|
| BNBUSDT | 1 | 2 | 0 | [] | nein |
| BNBUSDT | 5 | 2 | 0 | [] | nein |
| BNBUSDT | 15 | 2 | 0 | [] | nein |
| BNBUSDT | 60 | 2 | 0 | [] | nein |
| BNBUSDT | 300 | 2 | 0 | [] | nein |
| BTCUSDT | 1 | 2 | 1 | [0] | nein |
| BTCUSDT | 5 | 2 | 0 | [] | nein |
| BTCUSDT | 15 | 2 | 0 | [] | nein |
| BTCUSDT | 60 | 2 | 0 | [] | nein |
| BTCUSDT | 300 | 2 | 0 | [] | nein |
| ETHUSDT | 1 | 2 | 0 | [] | nein |
| ETHUSDT | 5 | 2 | 1 | [0] | nein |
| ETHUSDT | 15 | 2 | 0 | [] | nein |
| ETHUSDT | 60 | 2 | 0 | [] | nein |
| ETHUSDT | 300 | 2 | 0 | [] | nein |
| SOLUSDT | 1 | 2 | 2 | [0, 1] | JA |
| SOLUSDT | 5 | 2 | 2 | [0, 1] | JA |
| SOLUSDT | 15 | 2 | 1 | [0] | nein |
| SOLUSDT | 60 | 2 | 0 | [] | nein |
| SOLUSDT | 300 | 2 | 0 | [] | nein |
| XRPUSDT | 1 | 2 | 0 | [] | nein |
| XRPUSDT | 5 | 2 | 0 | [] | nein |
| XRPUSDT | 15 | 2 | 0 | [] | nein |
| XRPUSDT | 60 | 2 | 0 | [] | nein |
| XRPUSDT | 300 | 2 | 0 | [] | nein |

**Inverse-konsistente Zellen (>=2 Fenster):** 2 · **mind. eine inverse-konsistent:** ja

## Detail je Fenster / Symbol / delta

### BTCUSDT — Fenster 0 (A@2026-04-15) — 1776211200079..1776231894200 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 20693 | -0.0438 | - | 0.0438 | 0.461 | 0.0050 | ja | JA |
| 5 | 20689 | -0.0391 | - | 0.0391 | 0.502 | 0.0050 | ja | nein |
| 15 | 20679 | -0.0261 | - | 0.0261 | 0.510 | 0.0050 | ja | nein |
| 60 | 20634 | +0.0134 | + | 0.0134 | 0.503 | 0.0547 | nein | nein |
| 300 | 20394 | +0.0194 | + | 0.0194 | 0.496 | 0.0100 | ja | nein |

### BTCUSDT — Fenster 1 (B@2026-05-15) — 1778803200024..1778819108992 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 15907 | -0.0022 | - | 0.0022 | 0.508 | 0.7662 | nein | nein |
| 5 | 15903 | -0.0133 | - | 0.0133 | 0.525 | 0.1194 | nein | nein |
| 15 | 15893 | -0.0065 | - | 0.0065 | 0.524 | 0.4627 | nein | nein |
| 60 | 15848 | -0.0048 | - | 0.0048 | 0.512 | 0.5473 | nein | nein |
| 300 | 15608 | -0.0057 | - | 0.0057 | 0.505 | 0.4776 | nein | nein |

### ETHUSDT — Fenster 0 (A@2026-04-15) — 1776211200029..1776230095587 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 18894 | -0.0419 | - | 0.0419 | 0.541 | 0.0050 | ja | nein |
| 5 | 18890 | -0.0510 | - | 0.0510 | 0.518 | 0.0050 | ja | JA |
| 15 | 18880 | -0.0270 | - | 0.0270 | 0.508 | 0.0050 | ja | nein |
| 60 | 18835 | -0.0052 | - | 0.0052 | 0.505 | 0.4925 | nein | nein |
| 300 | 18595 | -0.0002 | - | 0.0002 | 0.499 | 0.9751 | nein | nein |

### ETHUSDT — Fenster 1 (B@2026-05-15) — 1778803200035..1778813556508 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 10355 | -0.0193 | - | 0.0193 | 0.507 | 0.0846 | nein | nein |
| 5 | 10351 | -0.0111 | - | 0.0111 | 0.518 | 0.2985 | nein | nein |
| 15 | 10341 | -0.0015 | - | 0.0015 | 0.513 | 0.8507 | nein | nein |
| 60 | 10296 | -0.0174 | - | 0.0174 | 0.498 | 0.1144 | nein | nein |
| 300 | 10056 | -0.0028 | - | 0.0028 | 0.511 | 0.7960 | nein | nein |

### SOLUSDT — Fenster 0 (A@2026-04-15) — 1776211200641..1776267045493 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 55843 | -0.0102 | - | 0.0102 | 0.410 | 0.0199 | ja | JA |
| 5 | 55839 | -0.0172 | - | 0.0172 | 0.444 | 0.0050 | ja | JA |
| 15 | 55829 | -0.0132 | - | 0.0132 | 0.470 | 0.0050 | ja | JA |
| 60 | 55784 | -0.0074 | - | 0.0074 | 0.481 | 0.1045 | nein | nein |
| 300 | 55544 | -0.0062 | - | 0.0062 | 0.485 | 0.1692 | nein | nein |

### SOLUSDT — Fenster 1 (B@2026-05-15) — 1778803200005..1778851877322 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 48676 | -0.0505 | - | 0.0505 | 0.421 | 0.0050 | ja | JA |
| 5 | 48672 | -0.0215 | - | 0.0215 | 0.460 | 0.0050 | ja | JA |
| 15 | 48662 | -0.0045 | - | 0.0045 | 0.484 | 0.3234 | nein | nein |
| 60 | 48617 | +0.0099 | + | 0.0099 | 0.492 | 0.0199 | ja | nein |
| 300 | 48377 | +0.0004 | + | 0.0004 | 0.497 | 0.9403 | nein | nein |

### BNBUSDT — Fenster 0 (A@2026-04-15) — 1776211202819..1776383995468 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 172791 | -0.0004 | - | 0.0004 | 0.559 | 0.8756 | nein | nein |
| 5 | 172787 | +0.0078 | + | 0.0078 | 0.536 | 0.0100 | ja | nein |
| 15 | 172777 | +0.0067 | + | 0.0067 | 0.523 | 0.0050 | ja | nein |
| 60 | 172732 | -0.0020 | - | 0.0020 | 0.510 | 0.3085 | nein | nein |
| 300 | 172492 | -0.0009 | - | 0.0009 | 0.501 | 0.7363 | nein | nein |

### BNBUSDT — Fenster 1 (B@2026-05-15) — 1778803200080..1778975990845 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 172789 | +0.0016 | + | 0.0016 | 0.510 | 0.4627 | nein | nein |
| 5 | 172785 | -0.0016 | - | 0.0016 | 0.496 | 0.5274 | nein | nein |
| 15 | 172775 | +0.0030 | + | 0.0030 | 0.495 | 0.1741 | nein | nein |
| 60 | 172730 | -0.0036 | - | 0.0036 | 0.499 | 0.0896 | nein | nein |
| 300 | 172490 | -0.0081 | - | 0.0081 | 0.495 | 0.0050 | ja | nein |

### XRPUSDT — Fenster 0 (A@2026-04-15) — 1776211200276..1776280187988 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 68986 | +0.0074 | + | 0.0074 | 0.427 | 0.0746 | nein | nein |
| 5 | 68982 | +0.0079 | + | 0.0079 | 0.429 | 0.0597 | nein | nein |
| 15 | 68972 | -0.0028 | - | 0.0028 | 0.463 | 0.3881 | nein | nein |
| 60 | 68927 | +0.0087 | + | 0.0087 | 0.492 | 0.0448 | nein | nein |
| 300 | 68687 | -0.0069 | - | 0.0069 | 0.492 | 0.0746 | nein | nein |

### XRPUSDT — Fenster 1 (B@2026-05-15) — 1778803200260..1778846541681 ms

| delta (s) | n | corr | sign | \|corr\| | hit | surr_p | FDR-sig | inverse-sig |
|---:|---:|---:|:---:|---:|---:|---:|:---:|:---:|
| 1 | 43340 | +0.0074 | + | 0.0074 | 0.438 | 0.1045 | nein | nein |
| 5 | 43336 | +0.0081 | + | 0.0081 | 0.479 | 0.0647 | nein | nein |
| 15 | 43326 | +0.0075 | + | 0.0075 | 0.499 | 0.1244 | nein | nein |
| 60 | 43281 | +0.0082 | + | 0.0082 | 0.507 | 0.0846 | nein | nein |
| 300 | 43041 | +0.0037 | + | 0.0037 | 0.505 | 0.4229 | nein | nein |

*Erzeugt von `c01_ofi_sign/oos.py` (H-05b OOS, read-only Harvester-Backfill, DEC-15). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-05b.*