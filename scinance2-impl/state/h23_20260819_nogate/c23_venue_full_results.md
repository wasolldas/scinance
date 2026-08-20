# H-17 · Venue-Fingerprint Mess-Gate (Contrastive-Embedding, F-VENUE, KAPITALFREI, GPU)

- **Hypothese:** H-23 — `scinance2-impl/state/hypothesis_registry.md` (Welle 5)
- **Erzeugt:** 2026-08-19T16:46:39+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/{bybit,binance}/publicTrade (2026-03-27..2026-07-04)`
- **Panel:** 10 Nodes = 5 Symbole x {Bybit, Binance}, publicTrade only, 5-Min-Event-Fenster, 4 Kanaele (Inter-Trade-Dauer, Log-Trade-Size, Aggressor-Sign, Tick-Direction)
- **Normalisierung:** Pro-Tag-Quantil-Normalisierung je Kanal/Node (Rang -> Uniform) — zerstoert triviale Venue-Tells (Tick-Size, Fee-Size-Clustering, Aktivitaetslevel); Diagnostik-Test in tests/unit/test_c17_venue.py
- **Encoder/Training:** Temporal-CNN (dilatiert) + Masked-Mean-Pool (count-invariant) + Projection-Head · InfoNCE (Positive = Fenster desselben Nodes zu anderen Zeiten, Negative = voller Batch, Batch >= 2048), Frozen-Linear-Probe fuer Venue-Identitaet
- **Folds:** Leave-One-Symbol-Out, 5 Folds, Test = letzte 3 Wochen des ausgelassenen Symbols
- **Null:** Within-Symbol-Within-Day-Label-Permutation, 20 VOLLE Retrainings je Fold (kein Frozen-Model-Shuffling) · Seed: 42
- **FDR-Familie:** F-VENUE (5 Fold-Tests) · BH-FDR alpha 0.1 · p_crit 0.0952 · FDR-signifikant: 5
- **KAPITALFREI:** ja — reine Struktur-/Existenzfrage. Eine Handelsfolge waere NEUE H-17b, NICHT impliziert.
- **Compute-Gate:** torch=ja · CUDA=ja · Batch 2048 (Min 2048) · erreichte Schritte (Min) 10000 (techn. Min 1) · **verdikt-tragend: ja**

> Gate-Urteil faellt der gate-auditor gegen H-17. WEITER verlangt: Held-out-Balanced-Accuracy >= 0,60 in >= 4/5 Leave-One-Symbol-Out-Folds gegen die 20-Retrainings-Permutations-Null nach BH-FDR alpha=0,10 ueber F-VENUE UND Non-Redundanz-Gate |Spearman rho| < 0,6 gegen die c12_frag-Tages-lambda2/IPR-Serie. DROP: Pooled-Accuracy < 0,55 ODER < 4/5 Folds ODER |rho| >= 0,6 (REDUNDANT zu H-12, DROP unabhaengig von der Accuracy). Kein Graubereich.

**WEITER-Indikation:** nein · Folds bestanden: 5/5 (ja) · Folds auswertbar: 5/5 · Pooled-Balanced-Accuracy: 0.8914 (>= 0.55: ja)

## Folds (Gate-Kern)

| Fold (Symbol out) | Test-Zeitraum | Train/Test-Fenster | Balanced Acc (>= 0,60) | Null (min..max) | p | FDR-sig | auswertbar | bestanden |
|---|---|---:|---:|---|---:|:---:|:---:|:---:|
| BNBUSDT | 2026-06-14..2026-07-04 | 230399/11845 | 0.7603 (ja) | 0.269..0.857 | 0.0952 | ja | ja | ja |
| BTCUSDT | 2026-06-14..2026-07-04 | 228630/12096 | 0.9312 (ja) | 0.384..0.500 | 0.0476 | ja | ja | ja |
| ETHUSDT | 2026-06-14..2026-07-04 | 228630/12096 | 0.9773 (ja) | 0.216..0.942 | 0.0476 | ja | ja | ja |
| SOLUSDT | 2026-06-14..2026-07-04 | 228631/12096 | 0.9531 (ja) | 0.117..0.719 | 0.0476 | ja | ja | ja |
| XRPUSDT | 2026-06-14..2026-07-04 | 228630/12096 | 0.8370 (ja) | 0.470..0.742 | 0.0476 | ja | ja | ja |

## Non-Redundanz-Gate gegen c12_frag/H-12 (vorregistriert, bindend)

- c12-Payload vorhanden: nein · ueberlappende Tage: 0 (techn. Floor 10)
- Spearman rho vs. lambda2: n/a · vs. IPR(v2): n/a · max|rho|: n/a (Schwelle 0.6)
- auswertbar: nein · **REDUNDANT (DROP): nein** · bestanden: nein

## Taegliche Cross-Venue-Embedding-Distance-Serie (sekundaer, nicht-urteilstragend)

- Tage: 100
- Median: 0.1478 · Min: 0.1050 · Max: 0.2318

*Erzeugt von `scripts/c17_venue.py` (Welle 5, read-only Harvester). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-17.*
