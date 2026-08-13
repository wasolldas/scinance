# H-11c — AnEn gegen dispersions-gematchte HAR (Dressed-HAR), KAPITALFREI

- **Hypothese:** H-11c — `scinance2-impl/state/hypothesis_registry.md` (Folge-Auflage aus GL-022)
- **Erzeugt:** 2026-08-13T11:04:46+00:00 (UTC) · Status: RUN
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/bybit/{publicTrade,rest.fundingRate}` (Symbole: BTCUSDT, ETHUSDT)
- **Gewichte (eingefroren, KEIN Re-Tuning):** BTCUSDT=[2.0, 2.0, 0.5, 0.0, 0.0] · ETHUSDT=[2.0, 0.5, 0.0, 0.0, 0.0]
- **Baseline:** HAR-RV point forecast UNCHANGED, dressed with a k-member quantile sample of the empirical IN-FIT residuals of the same monthly refit (plotting positions (j-0.5)/k, mean-centred); no look-ahead, no distributional assumption, no RNG
- **Bewertung:** BOTH sides scored with the SAME registered ensemble CRPS (1/k)sum|x_i-y| - (1/(2k^2))sum sum|x_i-x_j|
- **FDR-Familie:** F-ANEN-C · BH-FDR alpha=0.1 · p_crit=0.000000
- **AnEn-Seite reproduziert GL-022:** JA · `gate_valid=true`

> Gate-Urteil faellt der gate-auditor gegen H-11c. WEITER verlangt: fuer >=1 Symbol in {BTC,ETH} in BEIDEN Fenstern CRPSS_dressed>=0.05 UND Bootstrap-p<=0.05 nach BH-FDR alpha=0.10 ueber F-ANEN-C. Hartes Ein-Fenster-DROP, kein GRAUBEREICH, keine Nachsuche. A-priori: DROP erwartet.

## Zellen (F-ANEN-C: Symbol x Fenster)

| Symbol | Fenster | n | CRPS AnEn | CRPS Dressed-HAR | **CRPSS_dressed** | >=0.05 | boot-p | FDR-sig | Zelle | (CRPSS alte Dirac-Regel) |
|---|---|---:|---:|---:|---:|:---:|---:|:---:|:---:|---:|
| BTCUSDT | W1 | 177 | 0.1504 | 0.1528 | **0.0154** | nein | 0.2917 | nein | nein | 0.2917 |
| BTCUSDT | W2 | 96 | 0.1296 | 0.1258 | **-0.0305** | nein | 0.7602 | nein | nein | 0.2401 |
| ETHUSDT | W1 | 177 | 0.1650 | 0.1582 | **-0.0435** | nein | 0.9401 | nein | nein | 0.2475 |
| ETHUSDT | W2 | 96 | 0.1563 | 0.1475 | **-0.0594** | nein | 0.9161 | nein | nein | 0.2615 |

## Kontinuitaets-Nachweis der AnEn-Seite (Vorbedingung)

*Materialitaets-Schranke 1e-04 (registry H-11c Nachtrag 2 / DEC-32) — aus der GATE-ARITHMETIK hergeleitet, nicht aus einer Beobachtung: eine relative Stoerung eps auf den CRPS-Summen bewegt den CRPSS um hoechstens ~2*eps, also <=2e-4 bei eps<=1e-4 — das 250-Fache unter der 0,05-Schwelle. KEINE Bit-Identitaet: der Harvest-Speicher ist LIVE und darf historische Partitionen neu schreiben.*

| Symbol | Fenster | Summe CRPS AnEn (GL-022) | beobachtet | rel. Abw. | H-11-CRPSS (GL-022) | beobachtet | rel. Abw. | im Rahmen |
|---|---|---:|---:|---:|---:|---:|---:|:---:|
| BTCUSDT | W1 | 26.623978 | 26.623978 | 2.67e-16 | 0.291740 | 0.291740 | 3.81e-16 | JA |
| BTCUSDT | W2 | 12.442607 | 12.442607 | 2.86e-16 | 0.240077 | 0.240077 | 1.39e-15 | JA |
| ETHUSDT | W1 | 29.212400 | 29.212400 | 3.81e-09 | 0.247545 | 0.247545 | 8.30e-09 | JA |
| ETHUSDT | W2 | 15.005176 | 15.005176 | 1.18e-16 | 0.261457 | 0.261457 | 3.29e-10 | JA |

### Panel-Fingerabdruck (forensisch, nicht urteilstragend)

*SHA-256 ueber die exakten Float-Bytes des Tagespanels. Weicht er zwischen zwei Laeufen ab, hat sich der Harvest-Schnappschuss bewegt — die Frage, die nach dem 2026-08-12-Lauf offenblieb, ist damit kuenftig beantwortbar.*

| Symbol | Tage | von | bis | sha256(rv_daily) | sha256(funding_daily) |
|---|---:|---|---|---|---|
| BTCUSDT | 829 | 2024-03-27 | 2026-07-03 | `d0b7f1a00066e97e…` | `275b7cf6d0a18789…` |
| ETHUSDT | 829 | 2024-03-27 | 2026-07-03 | `98068d794b7e7bd1…` | `5ffa87aec3e88047…` |

## Pflicht-Diagnostik (NICHT urteilstragend)

*Registriert als nicht-urteilstragend, damit sie ehrlich berichtet werden muss, ohne das Gate bewegen zu koennen. (a) schliesst die in GL-022 offengelegte Funktional-Luecke: MAE wird vom MEDIAN minimiert, nicht vom Mittel.*

| Symbol | Fenster | MAE AnEn-Median | MAE HAR-Punkt | Diff (HAR-Median) | 2-seitig p | Disp.-Ratio AnEn | Disp.-Ratio Dressed | PIT chi2 AnEn (p) | PIT chi2 Dressed (p) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | W1 | 0.2097 | 0.2124 | +0.00267 | 0.7173 | 0.9875 | 0.9877 | 23.86 (0.2484) | 30.75 (0.0586) |
| BTCUSDT | W2 | 0.1628 | 0.1706 | +0.00777 | 0.4326 | 1.2570 | 1.1731 | 35.69 (0.0167) | 26.06 (0.1638) |
| ETHUSDT | W1 | 0.2282 | 0.2193 | -0.00887 | 0.2687 | 0.9725 | 0.9509 | 20.78 (0.4102) | 30.75 (0.0586) |
| ETHUSDT | W2 | 0.2143 | 0.2116 | -0.00267 | 0.7942 | 1.0900 | 1.1363 | 31.31 (0.0512) | 30.00 (0.0699) |

## Symbol-Rollup (Gate-Kern, gate-neutral)

| Symbol | Fenster gemessen | Fenster PASS | BEIDE Fenster PASS |
|---|---:|---:|:---:|
| BTCUSDT | 2 | 0 | nein |
| ETHUSDT | 2 | 0 | nein |

**Mindestens ein Symbol mit beiden Fenstern PASS:** nein

*Erzeugt von `c11_anen/driver_c.py` (read-only Harvester-Baum). capital_free=true — die 25-75x-Friktionsnotiz aus H-11 bleibt nach GL-022 E5 ENTKOPPELT. Endgueltiges Gate-Urteil: gate-auditor gegen H-11c.*