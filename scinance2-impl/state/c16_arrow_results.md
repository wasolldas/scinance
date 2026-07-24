# C-16 Time-Arrow-CNN — H-16 Mess-Gate (KAPITALFREI, GPU)

- **Hypothese:** H-16 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-07-23T22:06:52+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/bybit/publicTrade` (Symbole: BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, 2026-03-27..2026-07-19)
- **Methodik (vorregistriert):** 1s signed trade imbalance (buy - sell taker volume), bybit publicTrade; Morlet-CWT-Log-Power-Scalogram 64 Skalen 2s-256s x 512 Zeit-Bins, Stride 64s; Reversal auf der Roh-Serie VOR der CWT (scalogram_pair); ResNet-18, Single-Channel, 1 Logit, BCE, AdamW, epochs=6, batch=64, lr=0.001; Split: chronologischer Day-Level-Split, letzte 20% der validen Tage held-out (split_days_chronological); Seeds 5, Surrogate 20, Seed 42.
- **FDR-Familie:** F-ARROW · BH-FDR alpha = 0.1
- **KAPITALFREI:** ja — reine Struktur-/Existenzfrage, keine Kosten-/Ertragsrechnung.
- **Verdikt-tragend:** JA
- **Compute:** torch=True cuda=True device=NVIDIA GeForce RTX 5060 Ti

- **Differenzierung (Registry-Pflicht):** KEIN Duplikat des gesperrten Informationstheorie-/Nichtlineare-Dynamik-Clusters (PE/TE/RQA/MFDFA/TDA, H-04/H-06-Linie): H-16 verwendet NIRGENDS einen Entropie-Schaetzer; gemessen wird eine ANDERE Eigenschaft — Zeit-IRREVERSIBILITAET (richtungsabhaengige Asymmetrie des Prozessgesetzes unter Zeitumkehr t -> -t) statt Komplexitaet/Vorhersagbarkeit; und die Null ist die EXAKTE Bayes-optimale AUC = 0,5 des Classifier-Two-Sample-Tests (Lopez-Paz & Oquab 2017) fuer reversible Prozesse — ein exakter, vorab spezifizierbarer Wert, KEIN geschaetzter Schwellenwert aus einer surrogat-kalibrierten Entropie-Statistik.

## F-ARROW-Zellen (fixe 5er-Familie)

| Symbol | AUC (Median) | p (Sign-Test) | FDR-sig | AUC>=0.60 | Surr-p95 (<0.53) | Leak-AUC (<=0.52) | Ablation \|imb\| | Symbol-Gate |
|---|---:|---:|:---:|:---:|---:|---:|---:|:---:|
| BTCUSDT | 0.7331 | 0.000e+00 | ja | ja | 0.5045 | 0.4979 | 0.6982 | JA |
| ETHUSDT | 0.7353 | 0.000e+00 | ja | ja | 0.5077 | 0.5001 | 0.7095 | JA |
| SOLUSDT | 0.6648 | 0.000e+00 | ja | ja | 0.5082 | 0.4993 | 0.6417 | JA |
| BNBUSDT | 0.5929 | 5.839e-146 | ja | nein | 0.5044 | 0.4989 | 0.5987 | nein |
| XRPUSDT | 0.6416 | 0.000e+00 | ja | ja | 0.5067 | 0.5007 | 0.6324 | JA |

## Gate-Kern (gate-neutral — gate-auditor urteilt)

- **Status:** `MEASURED_GATE_NEUTRAL` — gate-neutral: WEITER/DROP urteilt ausschliesslich der gate-auditor gegen die Registry (H-16).
- **BH-Familie (fix):** 5 Zellen (5 gemessen, 0 Sentinel) · p_crit = 5.839e-146 · FDR-signifikant: 5
- **Symbol-Gates erfuellt:** 4 / 5 (Quorum >= 4)
- **Leak-Kontrolle bestanden (alle gemessenen Symbole <= 0.52):** ja

- **Ablation (nicht urteils-tragend, Pflicht-Report):** AUC auf |Imbalance| (unsigned) trennt Leverage-/Vol-Asymmetrie von Flow-Richtungs-Asymmetrie: bleibt die unsigned-AUC nahe 0.5, traegt die RICHTUNG des Flows die Zeitpfeil-Information; ist sie aehnlich hoch wie die signed-AUC, dominiert die Vol-Asymmetrie.

*Erzeugt von `c16_arrow/driver.py` (read-only Harvester-Baum). capital_free=true, gpu_required=true. WEITER verlangt (registriert, woertlich): Held-out-Day-Forward-vs-Reversed-AUC >= 0.60 MIT IAAFT-Surrogat-Null-95.-Perzentil < 0.53, bei >= 4/5 Symbolen nach BH-FDR alpha = 0.10 ueber F-ARROW, UND Leak-Kontrolle <= 0.52 (sonst methodisch invalide, KEIN Verdikt). DROP: AUC < 0.60 bei < 4/5 Symbolen. Kein Graubereich, keine nachtraegliche Skalen-/ Fenster-Anpassung. Endgueltiges Urteil: gate-auditor gegen H-16.*