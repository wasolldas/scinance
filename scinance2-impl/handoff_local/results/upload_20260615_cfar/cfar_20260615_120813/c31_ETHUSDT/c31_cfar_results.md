# C-31 CFAR-Auswertung (H-03 · Cyclostationary Footprint)

- **Hypothese:** H-03 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-15T12:31:07+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\bybit_edge.duckdb::trades` (Symbol `ETHUSDT`)
- **Fenster:** 2 · **Surrogates:** 200 · **Seed:** 42 · **BH-FDR alpha:** 0.1
- **F-CFAR-Familie:** dt10ms_T6, dt50ms_T6, dt100ms_T6

> Der Report liefert jedes Gate-Kriterium einzeln je Fenster. Das GATE-URTEIL (WEITER/DROP) faellt der gate-auditor gegen H-03 — hartes Ein-Fenster-Kriterium (PRD §8.5).

**Alle Fenster bestehen alle Kriterien:** nein

## Fenster 0 — 150000 Ticks
- Zeitspanne: 1780611314512 .. 1780614506435 ms
- Beste Variante (F-CFAR): `dt50ms_T6`

| Kriterium | Registry-Text | Messwert | Schwelle | Bestanden |
|---|---|---:|---:|---|
| Surrogate p | Surrogate p <= 0.05 (FDR-korrigiert, F-CFAR) | 0.965 | <= 0.05 | nein (FDR sig: nein) |
| Lead | Lead-Zeit > 50 ms (ueber Retail-Latenz) | 100.0 ms | > 50.0 | ja |
| Edge | Edge > 11 bps (ueber der Friction-Wand) | 0.04 bps | > 11.0 | nein |

- BH-FDR p_crit: 0.000
- Top-alpha: 0.079 Hz (Periode 12600.0 ms), n_events=146302, best bucket 0.04 bps

## Fenster 1 — 150000 Ticks
- Zeitspanne: 1780614506435 .. 1780619066873 ms
- Beste Variante (F-CFAR): `dt100ms_T6`

| Kriterium | Registry-Text | Messwert | Schwelle | Bestanden |
|---|---|---:|---:|---|
| Surrogate p | Surrogate p <= 0.05 (FDR-korrigiert, F-CFAR) | 0.801 | <= 0.05 | nein (FDR sig: nein) |
| Lead | Lead-Zeit > 50 ms (ueber Retail-Latenz) | 100.0 ms | > 50.0 | ja |
| Edge | Edge > 11 bps (ueber der Friction-Wand) | 0.01 bps | > 11.0 | nein |

- BH-FDR p_crit: 0.000
- Top-alpha: 0.040 Hz (Periode 25200.0 ms), n_events=145682, best bucket -0.01 bps

---
*Erzeugt von `scripts/c31_cfar.py` (WP-3, read-only Driver, DEC-03). Endgueltiges Gate-Urteil: gate-auditor gegen H-03.*
