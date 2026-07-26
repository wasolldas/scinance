# F-XDOM1 zweistufige BH-FDR - WAVE4_SUMMARY

- Hypothesen-Registry: `scinance2-impl/state/hypothesis_registry.md` (F-XDOM1-Eintrag, DEC-22)
- Welle-4-Ueber-Familie F-XDOM1 = F-BUNCH (H-09) U F-POINTER (H-10) U F-FRAG (H-12)
- Stage 1: BH-FDR alpha=0.1 INNERHALB jeder Familie (Driver-intern).
- Stage 2: BH-FDR alpha=0.1 ueber alle Stage-1-Survivor GEMEINSAM.
- Eine Hypothese gilt im Kohorten-Lauf nur als bestanden, wenn sie BEIDE Stufen ueberlebt.
- H-11/H-13 sind data-gated und NICHT Teil von F-XDOM1 (Entsperr-Check ist kein Test).
- KEIN Gesamturteil hier - gate-auditor entscheidet WEITER/DROP gegen H-09/H-10/H-12.
- Run-Label: `wave4_20260726_084312`

## Driver-Praesenz

| Hypothese | Driver-Output gefunden |
|---|---|
| H-09 (F-BUNCH) | ja |
| H-10 (F-POINTER) | ja |
| H-12 (F-FRAG) | ja |

## Stage-1 / Stage-2 Bilanz je Hypothese

| Hypothese (Familie) | Zellen gesamt | Stage-1 Survivor | Stage-2 Survivor | in Stage-2 verloren |
|---|---|---|---|---|
| F-BUNCH (H-09) | 10 | 0 | 0 | 0 |
| F-POINTER (H-10) | 4 | 0 | 0 | 0 |
| F-FRAG (H-12) | 78 | 62 | 62 | 0 |

Stage-2-Input: 62 Stage-1-Survivor-p-Werte * Stage-2 p_crit (BH alpha=0.1): 0.0410

## Stage-1 Survivor mit Stage-2-Ergebnis

| Hypothese | Familie | Zelle | p-Wert | Stage-1 | Stage-2 (F-XDOM1) |
|---|---|---|---|---|---|
| H-12 | F-FRAG | `W1/2026-03-27` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-03-28` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-03-30` | 0.0060 | ja | ja |
| H-12 | F-FRAG | `W1/2026-03-31` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-01` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-02` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-03` | 0.0090 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-05` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-06` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-07` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-08` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-10` | 0.0020 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-11` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-12` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-13` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-14` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-17` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-18` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-19` | 0.0270 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-20` | 0.0020 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-21` | 0.0150 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-22` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-23` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-24` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-26` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-27` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-28` | 0.0030 | ja | ja |
| H-12 | F-FRAG | `W1/2026-04-29` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-01` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-03` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-04` | 0.0100 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-05` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-06` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-07` | 0.0020 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-08` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-09` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-10` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-11` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-12` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-13` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-14` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W1/2026-05-15` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-16` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-17` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-18` | 0.0410 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-23` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-26` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-27` | 0.0090 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-28` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-29` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-30` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-05-31` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-01` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-02` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-03` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-05` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-07` | 0.0050 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-08` | 0.0140 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-11` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-13` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-15` | 0.0010 | ja | ja |
| H-12 | F-FRAG | `W2/2026-06-26` | 0.0020 | ja | ja |

## Gate-Kriterien je Zelle (gate-auditor-Input)

### H-09 * F-BUNCH (Risk-Limit-Tier-Bunching)

| Symbol | Fenster | b- | Asym (b- - b+) | Placebo-Max | p | Zelle gueltig | Sentinel | Stage-1 FDR | Gate-Zelle bestanden | Stage-2 FDR |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 0 | 1.0538 | +0.3516 | 14.0977 | 0.3573 | ja | nein | nein | nein | nein |
| BTCUSDT | 1 | 10.1985 | 4.4359 | 13.2795 | 0.1776 | ja | nein | nein | nein | nein |
| ETHUSDT | 0 | +0.0000 | +0.0000 | +0.3338 | 0.9042 | nein | nein | nein | nein | nein |
| ETHUSDT | 1 | -1.4051 | -0.1933 | +0.9895 | 0.7265 | ja | nein | nein | nein | nein |
| SOLUSDT | 0 | 3.3289 | -3.5814 | -1.7485 | 0.0559 | ja | nein | nein | nein | nein |
| SOLUSDT | 1 | -2.2568 | -3.3903 | 3.2001 | 0.9980 | ja | nein | nein | nein | nein |
| BNBUSDT | 0 | +0.0000 | +0.0000 | 1.0013 | 0.6627 | nein | nein | nein | nein | nein |
| BNBUSDT | 1 | +0.0000 | +0.0000 | -0.9942 | 0.7804 | nein | nein | nein | nein | nein |
| XRPUSDT | 0 | -3.4924 | -0.3761 | -1.5248 | 0.9980 | ja | nein | nein | nein | nein |
| XRPUSDT | 1 | 1.7649 | 1.6886 | -0.3955 | 0.3253 | ja | nein | nein | nein | nein |

Anti-Gaming/Validitaet (NICHT in F-XDOM1): gate_valid_assumptions=ja * family_size_deviation=nein * n_sentinel_cells=0 * any_window_truncated=nein * K_s-Platzhalter=['ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'] * placeholder_driven_pass_only=nein * Stage-1 p_crit=0.0000

### H-10 * F-POINTER (Cross-Stream-Pointer-Days + Pre-Event-Drift)

| Stufe | Fenster | N_pointer | N-Floor (>=3) | p (p_for_fdr) | Stage-1 FDR | Gate-Zelle bestanden | Stage-2 FDR |
|---|---|---|---|---|---|---|---|
| 1 | W1 | 0 | nein | 1.0000 | nein | nein | nein |
| 1 | W2 | 0 | nein | 1.0000 | nein | nein | nein |
| 2 | W1 | 0 | nein | 1.0000 | nein | nein | nein |
| 2 | W2 | 0 | nein | 1.0000 | nein | nein | nein |

Familien-Beobachtung (gate-neutral): all_four_cells_pass=nein * Stage-1 p_crit=0.0000 * Hinweis: der N_pointer-Floor ist KEIN p-Test und NICHT in F-XDOM1.

### H-12 * F-FRAG (Cross-Exchange-Fragmentierungsmatrix) - je Fenster

| Fenster | gueltige Tage | Stage-1 FDR-sig Tage | Stage-2 FDR-sig Tage | (a) Anteil | (a) | (b) Median-IPR(v2) | (b) | (c) dominante Boerse (Anteil) | (c) | Fenster gueltig |
|---|---|---|---|---|---|---|---|---|---|---|
| W1 | 47 | 42 | 42 | +0.8936 | ja | +0.1695 | nein | deribit (+0.9524) | ja | ja |
| W2 | 31 | 20 | 20 | +0.6452 | ja | +0.1698 | nein | deribit (+0.9500) | ja | nein |

Validitaets-Status (NICHT in F-XDOM1, Vorbedingung vor dem Gate): **UNGUELTIG** * all_windows_valid=nein * all_criteria_met_all_windows=nein * Stage-1 Familie: 78 Tages-Tests, p_crit=0.0410

## Nicht-p-Wert-Gate-Bestandteile - separat, NICHT in F-XDOM1

F-XDOM1 korrigiert ausschliesslich die p-Wert-Tests der drei Familien. Die uebrigen registrierten Gate-/Validitaets-Bestandteile bleiben unveraendert in Kraft und werden vom gate-auditor separat geprueft: H-09 b->=1,0 / Asymmetrie>=0,5 / Placebo-Dominanz / N-Floor / Anti-Gaming (gate_valid_assumptions); H-10 N_pointer>=3 je Fenster (Floor NICHT absenkbar); H-12 Validitaets-Vorbedingung (IPR(v1), 35-Tage-Floor - verfehlt -> Lauf UNGUELTIG, KEIN Verdikt) und Kriterien (b)/(c). Hartes Ein-Fenster-DROP-Kriterium je Hypothese wie registriert; kein GRAUBEREICH.

