# F-WAVE2 zweistufige BH-FDR - WAVE2_SUMMARY

- Hypothesen-Registry: `scinance2-impl/state/hypothesis_registry.md`
- Welle-2-Ueber-Familie F-WAVE2 = F-LEADLAG (H-04) U F-OFI (H-05) U F-ENTROPY (H-06)
- Stage 1: BH-FDR alpha=0.1 INNERHALB jeder Familie (Driver-intern).
- Stage 2: BH-FDR alpha=0.1 ueber alle Stage-1-Survivor GEMEINSAM.
- Eine Hypothese gilt nur als bestanden, wenn sie BEIDE Stufen ueberlebt.
- KEIN Gesamturteil hier - gate-auditor entscheidet WEITER/DROP gegen H-04/H-05/H-06.
- Run-Label: `wave2_20260617_090618`

## Driver-Praesenz

| Hypothese | Driver-Output gefunden |
|---|---|
| H-04 (F-LEADLAG) | ja |
| H-05 (F-OFI) | ja |
| H-06 (F-ENTROPY) | ja |

## Stage-1 / Stage-2 Bilanz je Hypothese

| Hypothese (Familie) | Varianten gesamt | Stage-1 Survivor | Stage-2 Survivor | in Stage-2 verloren |
|---|---|---|---|---|
| F-LEADLAG (H-04) | 22 | 12 | 12 | 0 |
| F-OFI (H-05) | 50 | 3 | 3 | 0 |
| F-ENTROPY (H-06) | 40 | 2 | 2 | 0 |

Stage-2-Input: 17 Stage-1-Survivor-p-Werte * Stage-2 p_crit (BH alpha=0.1): 0.0697

## Stage-1 Survivor mit Stage-2-Ergebnis

| Hypothese | Familie | Variante | p-Wert | Stage-1 | Stage-2 |
|---|---|---|---|---|---|
| H-04 | F-LEADLAG | `TE_BTCUSDT->ETHUSDT_lag1` | 0.0249 | ja | ja |
| H-04 | F-LEADLAG | `TE_BTCUSDT->ETHUSDT_lag2` | 0.0100 | ja | ja |
| H-04 | F-LEADLAG | `TE_BTCUSDT->ETHUSDT_lag3` | 0.0149 | ja | ja |
| H-04 | F-LEADLAG | `TE_BTCUSDT->ETHUSDT_lag5` | 0.0448 | ja | ja |
| H-04 | F-LEADLAG | `TE_ETHUSDT->BTCUSDT_lag1` | 0.0647 | ja | ja |
| H-04 | F-LEADLAG | `TE_ETHUSDT->BTCUSDT_lag2` | 0.0697 | ja | ja |
| H-04 | F-LEADLAG | `TE_ETHUSDT->BTCUSDT_lag3` | 0.0199 | ja | ja |
| H-04 | F-LEADLAG | `WCOH_BTCUSDT/ETHUSDT` | 0.0050 | ja | ja |
| H-04 | F-LEADLAG | `TE_BTCUSDT->ETHUSDT_lag1` | 0.0050 | ja | ja |
| H-04 | F-LEADLAG | `TE_BTCUSDT->ETHUSDT_lag2` | 0.0199 | ja | ja |
| H-04 | F-LEADLAG | `TE_ETHUSDT->BTCUSDT_lag1` | 0.0050 | ja | ja |
| H-04 | F-LEADLAG | `WCOH_BTCUSDT/ETHUSDT` | 0.0050 | ja | ja |
| H-05 | F-OFI | `BNBUSDT_w0_d1s` | 0.0050 | ja | ja |
| H-05 | F-OFI | `BNBUSDT_w0_d5s` | 0.0050 | ja | ja |
| H-05 | F-OFI | `ETHUSDT_w0_d1s` | 0.0050 | ja | ja |
| H-06 | F-ENTROPY | `XRPUSDT_w1_d15min` | 0.0050 | ja | ja |
| H-06 | F-ENTROPY | `XRPUSDT_w1_d60min` | 0.0050 | ja | ja |

## Gate-Kriterien je Fenster (gate-auditor-Input)

### H-04 * F-LEADLAG (C-17/C-41 Lead-Lag)

| Fenster | Achse | Variante | Lag [ms] | Lead | obs.Stat | p | Stage-1 FDR | Stage-2 FDR |
|---|---|---|---|---|---|---|---|---|
| 0 | TE | `TE_BTCUSDT->ETHUSDT_lag1` | 1000.0000 | BTCUSDT | +0.0054 | 0.0249 | ja | ja |
| 0 | TE | `TE_ETHUSDT->BTCUSDT_lag1` | 1000.0000 | ETHUSDT | +0.0040 | 0.0647 | ja | ja |
| 0 | TE | `TE_BTCUSDT->ETHUSDT_lag2` | 2000.0000 | BTCUSDT | +0.0074 | 0.0100 | ja | ja |
| 0 | TE | `TE_ETHUSDT->BTCUSDT_lag2` | 2000.0000 | ETHUSDT | +0.0046 | 0.0697 | ja | ja |
| 0 | TE | `TE_BTCUSDT->ETHUSDT_lag3` | 3000.0000 | BTCUSDT | +0.0059 | 0.0149 | ja | ja |
| 0 | TE | `TE_ETHUSDT->BTCUSDT_lag3` | 3000.0000 | ETHUSDT | +0.0046 | 0.0199 | ja | ja |
| 0 | TE | `TE_BTCUSDT->ETHUSDT_lag5` | 5000.0000 | BTCUSDT | +0.0048 | 0.0448 | ja | ja |
| 0 | TE | `TE_ETHUSDT->BTCUSDT_lag5` | 5000.0000 | ETHUSDT | +0.0029 | 0.2786 | nein | nein |
| 0 | TE | `TE_BTCUSDT->ETHUSDT_lag10` | 10000.0000 | BTCUSDT | +0.0037 | 0.1592 | nein | nein |
| 0 | TE | `TE_ETHUSDT->BTCUSDT_lag10` | 10000.0000 | ETHUSDT | +0.0022 | 0.5124 | nein | nein |
| 0 | WCOH | `WCOH_BTCUSDT/ETHUSDT` | 1261.3452 | BTCUSDT | +0.9028 | 0.0050 | ja | ja |
| 1 | TE | `TE_BTCUSDT->ETHUSDT_lag1` | 1000.0000 | BTCUSDT | +0.0087 | 0.0050 | ja | ja |
| 1 | TE | `TE_ETHUSDT->BTCUSDT_lag1` | 1000.0000 | ETHUSDT | +0.0055 | 0.0050 | ja | ja |
| 1 | TE | `TE_BTCUSDT->ETHUSDT_lag2` | 2000.0000 | BTCUSDT | +0.0049 | 0.0199 | ja | ja |
| 1 | TE | `TE_ETHUSDT->BTCUSDT_lag2` | 2000.0000 | ETHUSDT | +0.0028 | 0.2139 | nein | nein |
| 1 | TE | `TE_BTCUSDT->ETHUSDT_lag3` | 3000.0000 | BTCUSDT | +0.0017 | 0.7214 | nein | nein |
| 1 | TE | `TE_ETHUSDT->BTCUSDT_lag3` | 3000.0000 | ETHUSDT | +0.0036 | 0.0746 | nein | nein |
| 1 | TE | `TE_BTCUSDT->ETHUSDT_lag5` | 5000.0000 | BTCUSDT | +0.0037 | 0.0796 | nein | nein |
| 1 | TE | `TE_ETHUSDT->BTCUSDT_lag5` | 5000.0000 | ETHUSDT | +0.0024 | 0.4677 | nein | nein |
| 1 | TE | `TE_BTCUSDT->ETHUSDT_lag10` | 10000.0000 | BTCUSDT | +0.0012 | 0.9104 | nein | nein |
| 1 | TE | `TE_ETHUSDT->BTCUSDT_lag10` | 10000.0000 | ETHUSDT | +0.0009 | 0.9701 | nein | nein |
| 1 | WCOH | `WCOH_BTCUSDT/ETHUSDT` | 2232.5763 | BTCUSDT | +0.9076 | 0.0050 | ja | ja |

### H-05 * F-OFI (C-01 OFI-Vorzeichen)

| Symbol | Fenster | delta [s] | sign | |corr| | hit_rate | p | Stage-1 FDR | inverse_sig | Stage-2 FDR |
|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 0 | 1.0000 | - | +0.0101 | +0.4953 | 0.5075 | nein | nein | nein |
| BTCUSDT | 0 | 5.0000 | - | +0.0355 | +0.4802 | 0.0249 | nein | nein | nein |
| BTCUSDT | 0 | 15.0000 | - | +0.0287 | +0.4974 | 0.0896 | nein | nein | nein |
| BTCUSDT | 0 | 60.0000 | - | +0.0235 | +0.4951 | 0.1144 | nein | nein | nein |
| BTCUSDT | 0 | 300.0000 | + | +0.0008 | +0.5006 | 0.9701 | nein | nein | nein |
| BTCUSDT | 1 | 1.0000 | + | +0.0072 | +0.5368 | 0.5871 | nein | nein | nein |
| BTCUSDT | 1 | 5.0000 | + | +0.0044 | +0.5249 | 0.7662 | nein | nein | nein |
| BTCUSDT | 1 | 15.0000 | + | +0.0134 | +0.5102 | 0.3881 | nein | nein | nein |
| BTCUSDT | 1 | 60.0000 | + | +0.0011 | +0.5005 | 0.9403 | nein | nein | nein |
| BTCUSDT | 1 | 300.0000 | - | +0.0098 | +0.5144 | 0.4826 | nein | nein | nein |
| ETHUSDT | 0 | 1.0000 | - | +0.0550 | +0.4901 | 0.0050 | ja | ja | ja |
| ETHUSDT | 0 | 5.0000 | - | +0.0291 | +0.4917 | 0.0597 | nein | nein | nein |
| ETHUSDT | 0 | 15.0000 | - | +0.0366 | +0.4977 | 0.0199 | nein | nein | nein |
| ETHUSDT | 0 | 60.0000 | - | +0.0306 | +0.5163 | 0.0547 | nein | nein | nein |
| ETHUSDT | 0 | 300.0000 | - | +0.0125 | +0.5202 | 0.4129 | nein | nein | nein |
| ETHUSDT | 1 | 1.0000 | - | +0.0299 | +0.5454 | 0.0448 | nein | nein | nein |
| ETHUSDT | 1 | 5.0000 | - | +0.0305 | +0.5014 | 0.0697 | nein | nein | nein |
| ETHUSDT | 1 | 15.0000 | - | +0.0196 | +0.4985 | 0.2139 | nein | nein | nein |
| ETHUSDT | 1 | 60.0000 | - | +0.0053 | +0.4968 | 0.7413 | nein | nein | nein |
| ETHUSDT | 1 | 300.0000 | - | +0.0398 | +0.4881 | 0.0249 | nein | nein | nein |
| SOLUSDT | 0 | 1.0000 | + | +0.0160 | +0.5107 | 0.0249 | nein | nein | nein |
| SOLUSDT | 0 | 5.0000 | + | +0.0093 | +0.4958 | 0.1393 | nein | nein | nein |
| SOLUSDT | 0 | 15.0000 | - | +0.0110 | +0.4961 | 0.1343 | nein | nein | nein |
| SOLUSDT | 0 | 60.0000 | + | +0.0018 | +0.4908 | 0.7711 | nein | nein | nein |
| SOLUSDT | 0 | 300.0000 | - | +0.0162 | +0.5041 | 0.0348 | nein | nein | nein |
| SOLUSDT | 1 | 1.0000 | - | +0.0081 | +0.5081 | 0.2139 | nein | nein | nein |
| SOLUSDT | 1 | 5.0000 | - | +0.0054 | +0.4967 | 0.4677 | nein | nein | nein |
| SOLUSDT | 1 | 15.0000 | - | +0.0089 | +0.4845 | 0.2239 | nein | nein | nein |
| SOLUSDT | 1 | 60.0000 | - | +0.0022 | +0.4886 | 0.7363 | nein | nein | nein |
| SOLUSDT | 1 | 300.0000 | - | +0.0005 | +0.5027 | 0.9552 | nein | nein | nein |
| BNBUSDT | 0 | 1.0000 | + | +0.0441 | +0.6014 | 0.0050 | ja | nein | ja |
| BNBUSDT | 0 | 5.0000 | + | +0.0204 | +0.5556 | 0.0050 | ja | nein | ja |
| BNBUSDT | 0 | 15.0000 | + | +0.0051 | +0.5243 | 0.2289 | nein | nein | nein |
| BNBUSDT | 0 | 60.0000 | + | +0.0000 | +0.5098 | 1.0000 | nein | nein | nein |
| BNBUSDT | 0 | 300.0000 | - | +0.0031 | +0.5019 | 0.3980 | nein | nein | nein |
| BNBUSDT | 1 | 1.0000 | + | +0.0075 | +0.6625 | 0.0597 | nein | nein | nein |
| BNBUSDT | 1 | 5.0000 | - | +0.0066 | +0.5907 | 0.1393 | nein | nein | nein |
| BNBUSDT | 1 | 15.0000 | - | +0.0095 | +0.5442 | 0.0398 | nein | nein | nein |
| BNBUSDT | 1 | 60.0000 | - | +0.0016 | +0.5285 | 0.7164 | nein | nein | nein |
| BNBUSDT | 1 | 300.0000 | + | +0.0026 | +0.5088 | 0.5124 | nein | nein | nein |
| XRPUSDT | 0 | 1.0000 | - | +0.0009 | +0.5094 | 0.9154 | nein | nein | nein |
| XRPUSDT | 0 | 5.0000 | + | +0.0039 | +0.5043 | 0.5423 | nein | nein | nein |
| XRPUSDT | 0 | 15.0000 | - | +0.0067 | +0.4982 | 0.3134 | nein | nein | nein |
| XRPUSDT | 0 | 60.0000 | + | +0.0111 | +0.5021 | 0.1194 | nein | nein | nein |
| XRPUSDT | 0 | 300.0000 | + | +0.0078 | +0.5051 | 0.2836 | nein | nein | nein |
| XRPUSDT | 1 | 1.0000 | - | +0.0065 | +0.5015 | 0.2886 | nein | nein | nein |
| XRPUSDT | 1 | 5.0000 | - | +0.0062 | +0.5019 | 0.3881 | nein | nein | nein |
| XRPUSDT | 1 | 15.0000 | - | +0.0043 | +0.5097 | 0.5522 | nein | nein | nein |
| XRPUSDT | 1 | 60.0000 | + | +0.0017 | +0.5066 | 0.8259 | nein | nein | nein |
| XRPUSDT | 1 | 300.0000 | + | +0.0072 | +0.5129 | 0.2537 | nein | nein | nein |

### H-06 * F-ENTROPY (C-07 Permutation Entropy) - Haupt-Gate-Varianten

| Symbol | Fenster | delta [min] | MI | AUC-Lift | n_g1 | p | Stage-1 FDR | Stage-2 FDR |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 0 | 1.0000 | +0.0005 | -0.0085 | 6457 | 0.7214 | nein | nein |
| BTCUSDT | 0 | 5.0000 | +0.0036 | -0.0077 | 6421 | 0.1841 | nein | nein |
| BTCUSDT | 0 | 15.0000 | +0.0047 | -0.0077 | 6429 | 0.2786 | nein | nein |
| BTCUSDT | 0 | 60.0000 | +0.0062 | -0.0083 | 6438 | 0.3085 | nein | nein |
| BTCUSDT | 1 | 1.0000 | +0.0005 | -0.0021 | 6440 | 0.6368 | nein | nein |
| BTCUSDT | 1 | 5.0000 | +0.0030 | -0.0010 | 6427 | 0.2488 | nein | nein |
| BTCUSDT | 1 | 15.0000 | +0.0067 | -0.0015 | 6431 | 0.1592 | nein | nein |
| BTCUSDT | 1 | 60.0000 | +0.0053 | -0.0011 | 6426 | 0.5771 | nein | nein |
| ETHUSDT | 0 | 1.0000 | +0.0010 | -0.0014 | 6432 | 0.4826 | nein | nein |
| ETHUSDT | 0 | 5.0000 | +0.0031 | -0.0014 | 6442 | 0.5522 | nein | nein |
| ETHUSDT | 0 | 15.0000 | +0.0040 | -0.0017 | 6427 | 0.5871 | nein | nein |
| ETHUSDT | 0 | 60.0000 | +0.0109 | -0.0014 | 6470 | 0.2338 | nein | nein |
| ETHUSDT | 1 | 1.0000 | +0.0004 | -0.0071 | 6433 | 0.6915 | nein | nein |
| ETHUSDT | 1 | 5.0000 | +0.0015 | -0.0066 | 6423 | 0.6866 | nein | nein |
| ETHUSDT | 1 | 15.0000 | +0.0035 | -0.0071 | 6431 | 0.4428 | nein | nein |
| ETHUSDT | 1 | 60.0000 | +0.0059 | -0.0072 | 6414 | 0.4577 | nein | nein |
| SOLUSDT | 0 | 1.0000 | +0.0003 | -0.0039 | 6443 | 0.7662 | nein | nein |
| SOLUSDT | 0 | 5.0000 | +0.0011 | -0.0041 | 6445 | 0.7065 | nein | nein |
| SOLUSDT | 0 | 15.0000 | +0.0026 | -0.0040 | 6433 | 0.6567 | nein | nein |
| SOLUSDT | 0 | 60.0000 | +0.0073 | -0.0030 | 6462 | 0.2139 | nein | nein |
| SOLUSDT | 1 | 1.0000 | +0.0007 | +0.0088 | 6433 | 0.2438 | nein | nein |
| SOLUSDT | 1 | 5.0000 | +0.0024 | +0.0089 | 6439 | 0.2239 | nein | nein |
| SOLUSDT | 1 | 15.0000 | +0.0034 | +0.0093 | 6468 | 0.3731 | nein | nein |
| SOLUSDT | 1 | 60.0000 | +0.0071 | +0.0088 | 6445 | 0.1791 | nein | nein |
| BNBUSDT | 0 | 1.0000 | +0.0006 | -0.0078 | 6436 | 0.4627 | nein | nein |
| BNBUSDT | 0 | 5.0000 | +0.0023 | -0.0088 | 6426 | 0.3234 | nein | nein |
| BNBUSDT | 0 | 15.0000 | +0.0049 | -0.0071 | 6448 | 0.1244 | nein | nein |
| BNBUSDT | 0 | 60.0000 | +0.0047 | -0.0076 | 6433 | 0.5274 | nein | nein |
| BNBUSDT | 1 | 1.0000 | +0.0009 | +0.0010 | 6406 | 0.3035 | nein | nein |
| BNBUSDT | 1 | 5.0000 | +0.0028 | +0.0010 | 6426 | 0.1990 | nein | nein |
| BNBUSDT | 1 | 15.0000 | +0.0060 | +0.0011 | 6410 | 0.1343 | nein | nein |
| BNBUSDT | 1 | 60.0000 | +0.0123 | +0.0005 | 6439 | 0.0846 | nein | nein |
| XRPUSDT | 0 | 1.0000 | +0.0009 | +0.0028 | 6453 | 0.3731 | nein | nein |
| XRPUSDT | 0 | 5.0000 | +0.0037 | +0.0027 | 6423 | 0.2587 | nein | nein |
| XRPUSDT | 0 | 15.0000 | +0.0055 | +0.0030 | 6455 | 0.2736 | nein | nein |
| XRPUSDT | 0 | 60.0000 | +0.0093 | +0.0027 | 6466 | 0.1841 | nein | nein |
| XRPUSDT | 1 | 1.0000 | +0.0022 | +0.0075 | 6420 | 0.0149 | nein | nein |
| XRPUSDT | 1 | 5.0000 | +0.0074 | +0.0081 | 6404 | 0.0100 | nein | nein |
| XRPUSDT | 1 | 15.0000 | +0.0138 | +0.0072 | 6440 | 0.0050 | ja | ja |
| XRPUSDT | 1 | 60.0000 | +0.0195 | +0.0072 | 6451 | 0.0050 | ja | ja |

## H-06 PRE-Gate (rho >= 0.30) - separat, NICHT in F-WAVE2

Das PRE-Gate ist ein Korrelations-Floor, KEIN p-Wert-Test. Es zaehlt nicht in die Welle-2-Ueber-Familie. Ein-Fenster-DROP-Kriterium (PRD sec. 8.5): rho < 0.30 in EINEM Fenster -> H-06 DROP, unabhaengig von Stage 2.

| Symbol | Fenster | rho | n_pairs | rho >= 0.30 |
|---|---|---|---|---|
| BTCUSDT | 0 | +0.0044 | 25744 | nein |
| BTCUSDT | 1 | -0.0059 | 25744 | nein |
| ETHUSDT | 0 | +0.0111 | 25744 | nein |
| ETHUSDT | 1 | +0.0025 | 25744 | nein |
| SOLUSDT | 0 | -0.0001 | 25744 | nein |
| SOLUSDT | 1 | -0.0004 | 25744 | nein |
| BNBUSDT | 0 | -0.0002 | 25744 | nein |
| BNBUSDT | 1 | +0.0145 | 25744 | nein |
| XRPUSDT | 0 | -0.0006 | 25744 | nein |
| XRPUSDT | 1 | +0.0081 | 25744 | nein |

## H-05 inverse_significant je Symbol/delta (H-05b-Trigger-Erkennung)

Ein signifikant INVERSES OFI-Vorzeichen ist KEIN H-05-Bestehen, sondern Ausloeser fuer eine NEUE H-05b-Pre-Registration (MM-Replenishment-Lesart). Registry-Disziplin sec. 2: kein Verschieben der Torpfosten.

| Symbol | Fenster | delta [s] | corr | p |
|---|---|---|---|---|
| ETHUSDT | 0 | 1.0000 | -0.0550 | 0.0050 |

