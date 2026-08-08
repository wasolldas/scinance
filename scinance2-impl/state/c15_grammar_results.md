# C-15 Trade-Tape-Event-Grammatik — H-15 Mess-Gate (KAPITALFREI)

- **Hypothese:** H-15 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-08-08T17:08:10+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/bybit/publicTrade (H-15, read-only harvester tree)`
- **Modus:** full · **ran_on_gpu:** ja · **gate_valid:** ja
- **Raster:** 2026-03-27..2026-07-04 (100 Tage) · Purged Walk-Forward 4 Folds, 1-Tag-Embargo, Seeds [42, 43, 44]
- **Transformer (vorab fixiert):** Decoder-only causal, d_model=256, layers=4, heads=4, Kontext 1024, Vocab 128
- **Baseline:** KT-geglaettetes Variable-Order-Markov k<=4 + interpoliert (beste je Fold), GLEICHER Train-Fold
- **Null:** 200 Within-Hour-of-Day-Block-Shuffle-Surrogate (Blocklaenge 256 Events)
- **FDR-Familie:** F-GRAMMAR (5 Symbole) · **BH-FDR alpha:** 0.1 · **p_crit:** 0.0050
- **KAPITALFREI:** ja — reine Existence-of-Structure-Messung, keine Kapital-Metriken.

> Gate-Urteil faellt der gate-auditor gegen H-15. WEITER verlangt: OOS-Token-CE des Transformers >=2% relativ niedriger als die beste Markov-k-(k<=4)-Baseline bei >=4/5 Symbolen UND CE-Luecke ueber dem 95. Perzentil der Surrogat-Luecken-Verteilung, nach BH-FDR alpha=0.10 ueber F-GRAMMAR. Hartes Kriterium, kein GRAUBEREICH, kein Vocab-/Kontext-/Architektur-Nachjustieren.

## Differenzierung zum gesperrten Informationstheorie-Cluster (Pflicht)

> Differenzierung zu den gesperrten Informationstheorie-Clustern (PE/TE, H-06/H-04) ist konzeptionell sauber: (1) EVENT-STREAM statt Renditen — tokenisiert wird der publicTrade-Fluss (Side x Signed-Size-Quantil x Log-Inter-Arrival), keine Preis-/Rendite-Serie; (2) CROSS-ENTROPY als SCORING-RULE zweier expliziter Modelle (Causal-Transformer vs. Variable-Order-Markov) statt eines Entropie-SCHAETZERS (keine Permutations-Entropie, keine Transfer-Entropie); (3) KEIN rho-/Trading-Gate — reine kapitalfreie Existence-of-Structure-Messung. Eine Handelsfolge waere NEUE H-15b, NICHT impliziert.

## F-GRAMMAR je Symbol (Gate-Kern)

| Symbol | Markov-CE (beste) | Transformer-CE | rel. Luecke | >=2%? | Surrogat-p95 | Luecke>p95? | p | FDR-sig | Symbol besteht |
|---|---:|---:|---:|:---:|---:|:---:|---:|:---:|:---:|
| BTCUSDT | 1.2155 | 1.1778 | 0.0310 | ja | 0.02567 | ja | 0.0050 | ja | JA |
| ETHUSDT | 1.1085 | 1.0648 | 0.0394 | ja | 0.03138 | ja | 0.0050 | ja | JA |
| SOLUSDT | 1.6446 | 1.6003 | 0.0269 | ja | 0.02698 | ja | 0.0050 | ja | JA |
| BNBUSDT | 1.9201 | 1.9216 | -0.0008 | nein | -0.02077 | ja | 0.0050 | ja | nein |
| XRPUSDT | 2.0898 | 1.9803 | 0.0524 | ja | 0.06013 | ja | 0.0050 | ja | JA |

**Symbole bestehen:** 4 von 5 · **>=4/5 (gate-neutral):** JA

## Fold-Detail

### BTCUSDT

| Fold | Train-Events | Test-Events | beste Baseline | Markov-CE | Transformer-CE (Seeds) | Luecke |
|---:|---:|---:|---|---:|---|---:|
| 0 | 36077234 | 30623396 | interp_k4 | 1.4451 | 1.4091, 1.4095, 1.4095 | 0.03569 |
| 1 | 68724086 | 27075348 | interp_k4 | 1.2962 | 1.2631, 1.2613, 1.2626 | 0.03385 |
| 2 | 97720422 | 49770278 | interp_k4 | 1.2206 | 1.1786, 1.1773, 1.1784 | 0.04256 |
| 3 | 149528466 | 45120426 | interp_k4 | 1.0057 | 0.9697, 0.9696, 0.9698 | 0.03603 |

### ETHUSDT

| Fold | Train-Events | Test-Events | beste Baseline | Markov-CE | Transformer-CE (Seeds) | Luecke |
|---:|---:|---:|---|---:|---|---:|
| 0 | 39830484 | 33314118 | interp_k4 | 1.4291 | 1.3851, 1.3844, 1.3851 | 0.04420 |
| 1 | 75415664 | 31583395 | interp_k4 | 1.0886 | 1.0502, 1.0509, 1.0511 | 0.03783 |
| 2 | 109294235 | 55216871 | interp_k4 | 1.0365 | 0.9951, 0.9954, 0.9953 | 0.04122 |
| 3 | 166763892 | 52229108 | interp_k4 | 0.9922 | 0.9428, 0.9427, 0.9428 | 0.04942 |

### SOLUSDT

| Fold | Train-Events | Test-Events | beste Baseline | Markov-CE | Transformer-CE (Seeds) | Luecke |
|---:|---:|---:|---|---:|---|---:|
| 0 | 10726380 | 7682296 | interp_k4 | 1.8755 | 1.8244, 1.8282, 1.8260 | 0.04931 |
| 1 | 19171998 | 9386459 | interp_k4 | 1.5943 | 1.5589, 1.5594, 1.5602 | 0.03484 |
| 2 | 29148865 | 11667780 | interp_k4 | 1.5838 | 1.5384, 1.5386, 1.5385 | 0.04528 |
| 3 | 41275198 | 11704776 | interp_k4 | 1.5940 | 1.5464, 1.5464, 1.5465 | 0.04759 |

### BNBUSDT

| Fold | Train-Events | Test-Events | beste Baseline | Markov-CE | Transformer-CE (Seeds) | Luecke |
|---:|---:|---:|---|---:|---|---:|
| 0 | 1350123 | 1097984 | interp_k4 | 2.1902 | 2.2173, 2.2117, 2.2089 | -0.02242 |
| 1 | 2527296 | 1516408 | interp_k4 | 2.0512 | 2.0417, 2.0425, 2.0394 | 0.01003 |
| 2 | 4152329 | 3054616 | interp_k4 | 1.7887 | 1.7807, 1.7805, 1.7780 | 0.00900 |
| 3 | 7285264 | 1614306 | interp_k4 | 1.8618 | 1.8798, 1.8800, 1.8789 | -0.01777 |

### XRPUSDT

| Fold | Train-Events | Test-Events | beste Baseline | Markov-CE | Transformer-CE (Seeds) | Luecke |
|---:|---:|---:|---|---:|---|---:|
| 0 | 7504733 | 6815303 | interp_k4 | 2.1883 | 2.0708, 2.0753, 2.0700 | 0.11624 |
| 1 | 15068653 | 7888056 | interp_k4 | 2.0483 | 1.9448, 1.9438, 1.9391 | 0.10581 |
| 2 | 23441389 | 12123678 | interp_k4 | 2.0677 | 1.9604, 1.9597, 1.9590 | 0.10802 |
| 3 | 35888623 | 8764943 | interp_k4 | 2.0810 | 1.9734, 1.9711, 1.9703 | 0.10942 |

*Erzeugt von `c15_grammar/driver.py` (read-only Harvester-Baum). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-15.*