# H-18 · GL-006/H-04 Lead-Lag High-N-Surrogat-Aufloesungs-Audit

> **AUFLOESUNGS-AUDIT, KEINE NEU-ADJUDIKATION.** H-18 ist KEINE neue empirische Hypothese, sondern ein Aufloesungs-Audit der bereits adjudizierten GL-006/H-04-Pipeline (n_surrogates 200 -> 100.000). Das GL-006-Verdikt (WEITER, Mess-Existenz; Kapital-Status PARK) bleibt append-only UNVERAENDERT stehen. Ein abdriftender Stage-1-Survivor faelsifiziert NICHT GL-006 selbst — er markiert das stehende Messungen-WEITER als aufloesungsbedingt fragil (Audit-Finding). Dieses Modul schreibt NICHT gate_log.md; ein neuer, eigener GL-Eintrag (GL-014ff.) wird SPAETER manuell aus diesem Payload erstellt.

- **Registry:** `scinance2-impl/state/hypothesis_registry.md` (H-18) · Basis-Gate `GL-006` (H-04)
- **Erzeugt:** 2026-07-17T16:07:35+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\bybit_edge.duckdb::trades` (Paar `BTCUSDT`/`ETHUSDT`)
- **Fenster:** 2 · **Surrogates:** 100000 (GL-006: 200) · **Seed:** 42 (vorregistriert: 42, seed_matches_registered: ja) · **BH-FDR alpha:** 0.1
- **Backend:** angefordert `cuda` -> aufgeloest `torch-cuda`
- **Modus:** `resolution_audit` · **verdict_carrying:** ja — voller 100k-Surrogat-Lauf auf echtem CUDA-Device.
- **KAPITALFREI:** ja — identisch GL-006.

## T1 — Stage-1-FDR-Survivor-Reproduktion

T1: alle 12 GL-006-Stage-1-FDR-Survivor messen bei p <= 1e-3 neu und bleiben unter dem neu berechneten BH-Step-up signifikant

**t1_holds:** nein · Haltend: 4/12

| Fenster | Variante | p (GL-006) | p (neu) | p<=1e-3 | FDR-sig (neu) | haelt |
|---:|---|---:|---:|---|---|---|
| 0 | `TE_BTCUSDT->ETHUSDT_lag1` | 0.02488 | 0.012420 | nein | ja | nein |
| 0 | `TE_ETHUSDT->BTCUSDT_lag1` | 0.06468 | 0.068989 | nein | ja | nein |
| 0 | `TE_BTCUSDT->ETHUSDT_lag2` | 0.00995 | 0.000560 | ja | ja | ja |
| 0 | `TE_ETHUSDT->BTCUSDT_lag2` | 0.06965 | 0.028150 | nein | ja | nein |
| 0 | `TE_BTCUSDT->ETHUSDT_lag3` | 0.01493 | 0.004500 | nein | ja | nein |
| 0 | `TE_ETHUSDT->BTCUSDT_lag3` | 0.01990 | 0.030420 | nein | ja | nein |
| 0 | `TE_BTCUSDT->ETHUSDT_lag5` | 0.04478 | 0.025570 | nein | ja | nein |
| 0 | `WCOH_BTCUSDT/ETHUSDT` | 0.00498 | 0.000010 | ja | ja | ja |
| 1 | `TE_BTCUSDT->ETHUSDT_lag1` | 0.00498 | 0.000010 | ja | ja | ja |
| 1 | `TE_ETHUSDT->BTCUSDT_lag1` | 0.00498 | 0.003650 | nein | ja | nein |
| 1 | `TE_BTCUSDT->ETHUSDT_lag2` | 0.01990 | 0.012320 | nein | ja | nein |
| 1 | `WCOH_BTCUSDT/ETHUSDT` | 0.00498 | 0.000010 | ja | ja | ja |

## T2 — Lesart-Entscheidungszellen (ETH->BTC F0 Lag1/Lag2)

T2: die zwei Lesart-Entscheidungszellen ETH->BTC F0 Lag1/Lag2 loesen sich mit > 5 MC-SE Abstand von p_crit auf eine Seite auf

**t2_holds:** nein

| Fenster | Variante | p (neu) | p_crit (neu) | MC-SE | Distanz (SE) | aufgeloest |
|---:|---|---:|---:|---:|---:|---|
| 0 | `TE_ETHUSDT->BTCUSDT_lag1` | 0.068989 | 0.068989 | 0.000801 | 0.00 | nein |
| 0 | `TE_ETHUSDT->BTCUSDT_lag2` | 0.028150 | 0.068989 | 0.000523 | 78.08 | ja |

## Datenbindung vs. GL-006 (archivierte Fenster F0/F1)

Datenbindung: identisch GL-006 (archivierte Fenster F0/F1). Observed-Statistiken haengen NICHT von n_surrogates ab und muessen daher exakt reproduzieren, wenn die Fenster stimmen.
- **all_windows_match_gl006:** nein

## Fenster 0 — 3874 gemeinsame Bars
- Zeitspanne: 1780611314526 .. 1780615189170 ms
- Beste Variante: `WCOH_BTCUSDT/ETHUSDT` · BH-FDR p_crit: 0.068989 · FDR-sig: 8

| Variante | Achse | Quelle->Ziel | Lag (ms) | Statistik | Surrogate p | FDR sig |
|---|---|---|---:|---:|---:|---|
| `TE_BTCUSDT->ETHUSDT_lag1` | TE | BTCUSDT->ETHUSDT | 1000.0 | 0.0054 | 0.012420 | ja |
| `TE_ETHUSDT->BTCUSDT_lag1` | TE | ETHUSDT->BTCUSDT | 1000.0 | 0.0040 | 0.068989 | ja |
| `TE_BTCUSDT->ETHUSDT_lag2` | TE | BTCUSDT->ETHUSDT | 2000.0 | 0.0074 | 0.000560 | ja |
| `TE_ETHUSDT->BTCUSDT_lag2` | TE | ETHUSDT->BTCUSDT | 2000.0 | 0.0046 | 0.028150 | ja |
| `TE_BTCUSDT->ETHUSDT_lag3` | TE | BTCUSDT->ETHUSDT | 3000.0 | 0.0059 | 0.004500 | ja |
| `TE_ETHUSDT->BTCUSDT_lag3` | TE | ETHUSDT->BTCUSDT | 3000.0 | 0.0046 | 0.030420 | ja |
| `TE_BTCUSDT->ETHUSDT_lag5` | TE | BTCUSDT->ETHUSDT | 5000.0 | 0.0048 | 0.025570 | ja |
| `TE_ETHUSDT->BTCUSDT_lag5` | TE | ETHUSDT->BTCUSDT | 5000.0 | 0.0029 | 0.281767 | nein |
| `TE_BTCUSDT->ETHUSDT_lag10` | TE | BTCUSDT->ETHUSDT | 10000.0 | 0.0037 | 0.119109 | nein |
| `TE_ETHUSDT->BTCUSDT_lag10` | TE | ETHUSDT->BTCUSDT | 10000.0 | 0.0022 | 0.536265 | nein |
| `WCOH_BTCUSDT/ETHUSDT` | WCOH | BTCUSDT->ETHUSDT | 1261.3 | 0.9028 | 0.000010 | ja |

## Fenster 1 — 3875 gemeinsame Bars
- Zeitspanne: 1780615190990 .. 1780619066816 ms
- Beste Variante: `WCOH_BTCUSDT/ETHUSDT` · BH-FDR p_crit: 0.012320 · FDR-sig: 4

| Variante | Achse | Quelle->Ziel | Lag (ms) | Statistik | Surrogate p | FDR sig |
|---|---|---|---:|---:|---:|---|
| `TE_BTCUSDT->ETHUSDT_lag1` | TE | BTCUSDT->ETHUSDT | 1000.0 | 0.0087 | 0.000010 | ja |
| `TE_ETHUSDT->BTCUSDT_lag1` | TE | ETHUSDT->BTCUSDT | 1000.0 | 0.0055 | 0.003650 | ja |
| `TE_BTCUSDT->ETHUSDT_lag2` | TE | BTCUSDT->ETHUSDT | 2000.0 | 0.0049 | 0.012320 | ja |
| `TE_ETHUSDT->BTCUSDT_lag2` | TE | ETHUSDT->BTCUSDT | 2000.0 | 0.0028 | 0.267647 | nein |
| `TE_BTCUSDT->ETHUSDT_lag3` | TE | BTCUSDT->ETHUSDT | 3000.0 | 0.0017 | 0.716883 | nein |
| `TE_ETHUSDT->BTCUSDT_lag3` | TE | ETHUSDT->BTCUSDT | 3000.0 | 0.0036 | 0.090039 | nein |
| `TE_BTCUSDT->ETHUSDT_lag5` | TE | BTCUSDT->ETHUSDT | 5000.0 | 0.0037 | 0.075419 | nein |
| `TE_ETHUSDT->BTCUSDT_lag5` | TE | ETHUSDT->BTCUSDT | 5000.0 | 0.0024 | 0.403026 | nein |
| `TE_BTCUSDT->ETHUSDT_lag10` | TE | BTCUSDT->ETHUSDT | 10000.0 | 0.0012 | 0.897251 | nein |
| `TE_ETHUSDT->BTCUSDT_lag10` | TE | ETHUSDT->BTCUSDT | 10000.0 | 0.0009 | 0.962510 | nein |
| `WCOH_BTCUSDT/ETHUSDT` | WCOH | BTCUSDT->ETHUSDT | 2232.6 | 0.9076 | 0.000010 | ja |

---
*Erzeugt von `scripts/c18_leadlag_audit.py` (Welle-5-WP, read-only Driver). KAPITALFREI. scinance2-impl/state/gate_log.md wird von diesem Modul NICHT geschrieben — neuer GL-Eintrag ist Orchestrator-/gate-auditor-Arbeit.*
