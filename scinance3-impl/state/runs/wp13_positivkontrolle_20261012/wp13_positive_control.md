Positivkontrolle NICHT BESTANDEN

# WP-13 Positivkontrolle in Produktionskonfiguration (DEC-89 E2)

- registrierte Datei sha256: `bd948f34516bb444f152287863e6096da6faf82712b579c6dfa211599015c299`
- Seeds: [53, 54, 55], injizierte IC: 0.06, Konvention `close_at_last`, Beta-Kontrolle `fm_neutral_8w`
- Daten-Fingerprints (V9): `{'union_range_fingerprint': 'a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a', 'delisting_dates_sha256': '852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933', 'union_range_detail': {'year_range': [2021, 2026], 'n_partitions': 6507, 'survivors_fingerprint': 'abccdbd3e0a809ac5723ac7a5d6055e55b864c72f5c2980c11dc920aedecfabc', 'delisted_fingerprint': '08be8556de8ed13227f80ff3b79f760b3c6b65ac428a38d41bf66c5746660dcd', 'n_symbols': 1138, 'as_of': '2026-09-28'}}`
- result_sha256: `b3daeea80a5426e310270d0036bd0667144cea44b3777dafc4dfd3a75814041d`, Laufzeit 8.072 s
- nicht gerechnet (report-only / eingefrorene Werte): block_permutation_p, bh_fdr, persistence_null, factor_null_replicates (frozen constants used)
- uebersprungen (gesperrt, gl012_pre_run): H-28_mom2, H-28_mom4, H-30_vol_rv, H-30_vol_max, H-30_vol_beta
- nicht abgedeckt (kein injizierbares Signal): -

## Kriterium (vorab, DEC-89 E2)

H-28_mom1 und H-29_rev_gap in allen drei Seeds PASS UND Negativkontrolle in allen drei Seeds kein PASS.

- Positivkontrolle alle PASS: False
- Negativkontrolle kein PASS: True

| Eintrag | Bedingung | Seed 53 | Seed 54 | Seed 55 |
|---|---|---|---|---|
| H-28_mom1 | positiv | DROP | PASS | DROP |
| H-28_mom1 | negativ | DROP | DROP | DROP |
| H-29_rev_gap | positiv | PASS | PASS | PASS |
| H-29_rev_gap | negativ | DROP | DROP | DROP |

## Synthetische Welten (aus der YAML abgeleitet)

| Fenster | rho_f | beta_sd | Faktoranteil | sigma_e | sigma_f | sigma_g | sigma_tot |
|---|---|---|---|---|---|---|---|
| W1 | 0.09248 | 0.77067 | 0.06422 | 0.12064 | 0.06685 | 0.04524 | 0.13877 |
| W2 | 0.08317 | 0.58333 | 0.02777 | 0.10729 | 0.05514 | 0.04024 | 0.11902 |

## Kennzahlen je Seed, Bedingung, Eintrag, Fenster

| Seed | Bedingung | Eintrag | Verdikt | Fenster | IC | CI-Grenze | IC_min | IC_res | Quantil | Decke | Bounce-IC | Fenster PASS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 53 | positive | H-28_mom1 | DROP | W1 | 0.04184 | -0.00046 | 0.01966 | 0.03250 | 0.02244 | 0.00834 | - | False |
| 53 | positive | H-28_mom1 | DROP | W2 | 0.04667 | 0.03008 | 0.01744 | 0.03997 | 0.01700 | 0.00685 | - | True |
| 53 | positive | H-29_rev_gap | PASS | W1 | -0.05337 | -0.00324 | 0.01727 | -0.03098 | -0.01666 | 0.00834 | -0.00357 | True |
| 53 | positive | H-29_rev_gap | PASS | W2 | -0.05272 | -0.02547 | 0.01531 | -0.03522 | -0.01546 | 0.00685 | 0.00309 | True |
| 53 | negative | H-28_mom1 | DROP | W1 | -0.01307 | -0.05669 | 0.01966 | -0.01123 | 0.02244 | 0.00834 | - | False |
| 53 | negative | H-28_mom1 | DROP | W2 | -0.00803 | -0.02521 | 0.01744 | -0.00586 | 0.01700 | 0.00685 | - | False |
| 53 | negative | H-29_rev_gap | DROP | W1 | 0.00144 | 0.05188 | 0.01727 | 0.01238 | -0.01666 | 0.00834 | -0.00357 | False |
| 53 | negative | H-29_rev_gap | DROP | W2 | 0.00134 | 0.02665 | 0.01531 | 0.00861 | -0.01546 | 0.00685 | 0.00309 | False |
| 54 | positive | H-28_mom1 | PASS | W1 | 0.04427 | 0.01669 | 0.01966 | 0.04054 | 0.02244 | 0.00834 | - | True |
| 54 | positive | H-28_mom1 | PASS | W2 | 0.04978 | 0.03692 | 0.01744 | 0.04499 | 0.01700 | 0.00685 | - | True |
| 54 | positive | H-29_rev_gap | PASS | W1 | -0.05366 | -0.00793 | 0.01727 | -0.04289 | -0.01666 | 0.00834 | -0.00357 | True |
| 54 | positive | H-29_rev_gap | PASS | W2 | -0.05264 | -0.02177 | 0.01531 | -0.03527 | -0.01546 | 0.00685 | 0.00309 | True |
| 54 | negative | H-28_mom1 | DROP | W1 | -0.01192 | -0.04123 | 0.01966 | -0.00422 | 0.02244 | 0.00834 | - | False |
| 54 | negative | H-28_mom1 | DROP | W2 | -0.00504 | -0.01911 | 0.01744 | 0.00024 | 0.01700 | 0.00685 | - | False |
| 54 | negative | H-29_rev_gap | DROP | W1 | 0.00076 | 0.04459 | 0.01727 | 0.00176 | -0.01666 | 0.00834 | -0.00357 | False |
| 54 | negative | H-29_rev_gap | DROP | W2 | 0.00019 | 0.03078 | 0.01531 | 0.00793 | -0.01546 | 0.00685 | 0.00309 | False |
| 55 | positive | H-28_mom1 | DROP | W1 | 0.04785 | 0.00678 | 0.01966 | 0.02785 | 0.02244 | 0.00834 | - | False |
| 55 | positive | H-28_mom1 | DROP | W2 | 0.05825 | 0.03538 | 0.01744 | 0.04135 | 0.01700 | 0.00685 | - | True |
| 55 | positive | H-29_rev_gap | PASS | W1 | -0.05825 | -0.02447 | 0.01727 | -0.04055 | -0.01666 | 0.00834 | -0.00357 | True |
| 55 | positive | H-29_rev_gap | PASS | W2 | -0.06197 | -0.03374 | 0.01531 | -0.05766 | -0.01546 | 0.00685 | 0.00309 | True |
| 55 | negative | H-28_mom1 | DROP | W1 | -0.00547 | -0.04852 | 0.01966 | -0.01754 | 0.02244 | 0.00834 | - | False |
| 55 | negative | H-28_mom1 | DROP | W2 | 0.00465 | -0.01965 | 0.01744 | -0.00295 | 0.01700 | 0.00685 | - | False |
| 55 | negative | H-29_rev_gap | DROP | W1 | -0.00689 | 0.02876 | 0.01727 | 0.00144 | -0.01666 | 0.00834 | -0.00357 | False |
| 55 | negative | H-29_rev_gap | DROP | W2 | -0.00833 | 0.01960 | 0.01531 | -0.01155 | -0.01546 | 0.00685 | 0.00309 | False |

## Etiketten (je Seed, Bedingung, Eintrag)

- Seed 53 positive H-28_mom1: C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3)/(5) nicht / Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.198, W2=-0.438 IC_min-Einheiten -- Verdikt unveraendert
- Seed 53 positive H-29_rev_gap: Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.189, W2=-0.579 IC_min-Einheiten -- Verdikt unveraendert
- Seed 53 negative H-28_mom1: C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3)/(5) nicht / Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.198, W2=-0.438 IC_min-Einheiten -- Verdikt unveraendert
- Seed 53 negative H-29_rev_gap: Artefakt Bounce in W1: |IC_bounce|=0.00357 >= |IC|=0.00144 -- KEIN PASS (DEC-75 (5), DEC-87 (I)) / Artefakt Bounce in W2: |IC_bounce|=0.00309 >= |IC|=0.00134 -- KEIN PASS (DEC-75 (5), DEC-87 (I)) / C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3)/(5) nicht / Illiquiditaets-Artefakt (H-16-Muster) in W1: IC_ohne_D1=0.00291 nicht jenseits -0.5*IC_min=-0.00863 -- Verdikt steht, Lesart eingeschraenkt / Illiquiditaets-Artefakt (H-16-Muster) in W2: IC_ohne_D1=-0.00099 nicht jenseits -0.5*IC_min=-0.00766 -- Verdikt steht, Lesart eingeschraenkt / Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.189, W2=-0.579 IC_min-Einheiten -- Verdikt unveraendert
- Seed 54 positive H-28_mom1: Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.198, W2=-0.438 IC_min-Einheiten -- Verdikt unveraendert
- Seed 54 positive H-29_rev_gap: Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.189, W2=-0.579 IC_min-Einheiten -- Verdikt unveraendert
- Seed 54 negative H-28_mom1: C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3)/(5) nicht / Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.198, W2=-0.438 IC_min-Einheiten -- Verdikt unveraendert
- Seed 54 negative H-29_rev_gap: Artefakt Bounce in W1: |IC_bounce|=0.00357 >= |IC|=0.00076 -- KEIN PASS (DEC-75 (5), DEC-87 (I)) / Artefakt Bounce in W2: |IC_bounce|=0.00309 >= |IC|=0.00019 -- KEIN PASS (DEC-75 (5), DEC-87 (I)) / C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3)/(5) nicht / Illiquiditaets-Artefakt (H-16-Muster) in W1: IC_ohne_D1=0.00610 nicht jenseits -0.5*IC_min=-0.00863 -- Verdikt steht, Lesart eingeschraenkt / Illiquiditaets-Artefakt (H-16-Muster) in W2: IC_ohne_D1=0.00008 nicht jenseits -0.5*IC_min=-0.00766 -- Verdikt steht, Lesart eingeschraenkt / Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.189, W2=-0.579 IC_min-Einheiten -- Verdikt unveraendert
- Seed 55 positive H-28_mom1: C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3)/(5) nicht / Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.198, W2=-0.438 IC_min-Einheiten -- Verdikt unveraendert
- Seed 55 positive H-29_rev_gap: Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.189, W2=-0.579 IC_min-Einheiten -- Verdikt unveraendert
- Seed 55 negative H-28_mom1: C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3)/(5) nicht / Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.198, W2=-0.438 IC_min-Einheiten -- Verdikt unveraendert
- Seed 55 negative H-29_rev_gap: C.10 hart: mindestens ein Fenster erfuellt Gate (1)/(3)/(5) nicht / Survivorship-Etikett (report-only, nie Gate; DEC-76/DEC-89): Differenz 'Beobachtung verworfen' minus 'zum letzten Schlusskurs geschlossen' auf dem signalfreien Drawdown-Fixture = W1=-0.189, W2=-0.579 IC_min-Einheiten -- Verdikt unveraendert

Positivkontrolle NICHT BESTANDEN
