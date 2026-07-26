# C-10 Cross-Stream-Pointer-Days + Pre-Event-Drift — H-10 Mess-Gate (KAPITALFREI)

- **Hypothese:** H-10 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-07-26T09:03:33+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw (bybit+binance publicTrade/rest.fundingRate/rest.openInterest; deribit dvol hold-out)`
- **Tagesraster:** 2026-03-27..2026-07-04 (100 Tage, Burn-in 21, nutzbar ab 2026-04-17)
- **Fenster (vorregistriert):** W1=2026-04-17..2026-05-25, W2=2026-05-26..2026-07-04
- **Detektions-Serien:** 30 (vorab fixiert) · **Hold-out-Ziel:** deribit dvol BTC+ETH (never in detection)
- **Methodik:** trailing 63-Tage-Median (min_periods=21) · Cropper 11-Tage zentriert · |C|>=1.5 · Anteil>=0.6 · n_avail>=18 · Pre-Drift [t-5,t-1] vs. [t-15,t-6]
- **Surrogate/Permutationen:** 1000 / 1000 · **Seed:** 42
- **FDR-Familie:** F-POINTER (4 Zellen) · **BH-FDR alpha:** 0.1 · **p_crit:** 0.0000
- **KAPITALFREI:** ja — reine Mess-/Existenzfrage, keine Kapital-Metriken.

> Gate-Urteil faellt der gate-auditor gegen H-10. WEITER verlangt nach BH-FDR alpha=0.10 ueber F-POINTER ALLE 4 Zellen: Stufe-1-p<=0.05 in W1 UND W2, N_pointer>=3 je Fenster (Floor NICHT absenkbar), Stufe-2-p<=0.05 (zweiseitig) in W1 UND W2. Hartes Ein-Fenster-DROP, kein GRAUBEREICH.

## F-POINTER-Zellen (Gate-Kern)

| Stufe | Fenster | N_pointer | Statistik | p | FDR-sig | N-Floor (>=3) | Zelle besteht |
|---:|---|---:|---:|---:|:---:|:---:|:---:|
| 1 | W1 | 0 | N_obs=0 (Surr-Mittel 0.00) | 1.0000 | nein | NEIN | nein |
| 1 | W2 | 0 | N_obs=0 (Surr-Mittel 0.00) | 1.0000 | nein | NEIN | nein |
| 2 | W1 | 0 | S=n/a (Null-Pool 39) | n/a | nein | NEIN | nein |
| 2 | W2 | 0 | S=n/a (Null-Pool 33) | n/a | nein | NEIN | nein |

**all_four_cells_pass (gate-neutral):** nein

## Pointer-Tage

- **W1** (2026-04-17..2026-05-25): keine
- **W2** (2026-05-26..2026-07-04): keine

## Neuwirth-Fenster-Crosscheck (mitberichtet, NICHT-urteilstragend)

> 13-Tage-Fenster (Neuwirth et al. 2007), gleiche Detrend-/Pointer-Regel. Reines Anti-Method-Shopping-Diagnostikum — geht in KEINE Zelle, KEIN p, KEINE FDR ein (Registry H-10).

- **W1**: N_pointer(Neuwirth)=0 (Ueberlapp mit Cropper: 0): keine
- **W2**: N_pointer(Neuwirth)=0 (Ueberlapp mit Cropper: 0): keine

## Abdeckung (Coverage-Audit)

- **Hold-out dvol:** BTC 90 Tage (nutzbar 69) · ETH 90 Tage (nutzbar 69) · Parse-Modus: `{'BTC': 'candidate:close', 'ETH': 'candidate:close'}`
- **Detektions-Serien nicht-leer:** 30 von 30 (finite Tage je Serie im JSON: `detection_series_finite_days`)

*Erzeugt von `c10_pointer/driver.py` (read-only Harvester-Baum). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-10.*