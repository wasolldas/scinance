# H-20 — TAIL-AFTERMATH: Nachbewegung nach 3,5-sigma-Stunden (KAPITALFREI)

- **Hypothese:** H-20 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-08-17T09:10:22+00:00 (UTC) · Status: RUN
- **Datenbindung:** WP-0-Bar-Cache · `gate_valid=true`
- **Event:** |r_hour| >= 3.5 x sigma; sigma = 1.4826 x rolling MAD of previous <= 720 hourly returns (>= 360), strictly causal; hour candidate needs >= 45 minute bars; non-overlap 24 h, first event wins
- **Outcome:** y = -sign(r_event) x logmove(t0+2h -> t0+24h) in bp; data-quality floors: >= 660 minutes present, boundary bars within 30 min
- **Statistik:** pooled over symbols; day-clustered bootstrap (cluster = UTC event day, 1000 reps, seed 42) for H0: E[y] <= 0
- **Gate:** BEIDE OOS-Fenster gepoolt: mean >= +10 bp UND p <= 0.05 nach BH-FDR alpha=0.1 ueber F-TAIL; N-Floor 100 Event-Tage/Fenster (darunter KEIN VERDIKT). Hartes Ein-Fenster-DROP.

> A-priori (registriert): offen, ~30-40 % WEITER. bp-Groessen sind Preisbewegungs-Messgroessen; Monetarisierung waere NEUE H-20b.

## Gepoolte Zellen

| Fenster | urteilstragend | Events | Event-Tage | Floor | mean bp | median bp | >= +10 | boot-p | FDR | Zelle |
|---|:---:|---:|---:|:---:|---:|---:|:---:|---:|:---:|:---:|
| L | nein | 889 | 362 | ok | -40.47 | -6.54 | nein | 0.9311 | — | — |
| OOS1 | ja | 1044 | 403 | ok | +4.83 | +14.24 | nein | 0.3976 | nein | nein |
| OOS2 | ja | 962 | 362 | ok | +17.28 | +20.21 | ja | 0.1728 | nein | nein |

**Beide urteilstragenden Fenster PASS:** nein · **Verdikt auswertbar (N-Floor):** ja · Datenqualitaets-Drops: 0

## Per-Symbol (mitberichtet, NICHT urteilstragend)

| Symbol | Fenster | Events | mean bp |
|---|---|---:|---:|
| BTCUSDT | OOS1 | 244 | -16.48 |
| ETHUSDT | OOS1 | 236 | +31.89 |
| XRPUSDT | OOS1 | 190 | +14.76 |
| SOLUSDT | OOS1 | 176 | -49.36 |
| BNBUSDT | OOS1 | 198 | +37.46 |
| BTCUSDT | OOS2 | 225 | +36.44 |
| ETHUSDT | OOS2 | 226 | -12.25 |
| XRPUSDT | OOS2 | 186 | -21.20 |
| SOLUSDT | OOS2 | 154 | +45.73 |
| BNBUSDT | OOS2 | 171 | +47.32 |

*Erzeugt von `c20_tail/driver.py` — liest AUSSCHLIESSLICH den WP-0-Bar-Cache. capital_free=true. Gate-Urteil: gate-auditor gegen H-20.*