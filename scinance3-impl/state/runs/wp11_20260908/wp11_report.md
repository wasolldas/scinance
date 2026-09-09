# WP-11 -- Relaxationsrate nach Schockstunden (deskriptiv, KEIN VERDIKT)

- **Paket:** WP-11 -- `PRD_SCINANCE3.md 11.3 (DEC-58); Exkurs X-OEKO-1 Arm (a)`
- **Erzeugt:** 2026-09-08T13:53:27+00:00 (UTC) - Status: RUN
- **Semantik:** DESKRIPTIV (Arm (a), PRD 11.3): kein PASS/FAIL, keine Schwelle -- Halbwertszeit ist Deskriptor
- **Datenbindung:** WP-0-Bar-Cache - `gate_valid=true`
- **Ereignisse:** 3570 real, 3570 gematchter Pseudo-Null, 1468 Ereignistage gesamt
- **Event-Definition:** WOERTLICH aus H-20 geerbt (c20_tail.driver), kein neuer Parameter
- **Fit:** AR(1)-aequivalenter Zerfall der Ueberschussreihe (5-Min-Buckets, 24h post-shock), lambda = -ln(phi)/dt_h, half_life = ln2/lambda
- **Time-to-Return:** erste Stunde mit |excess| <= 10% des Schock-Excess; rechts-zensiert bei 24h

## (i) Median-Halbwertszeit je Symbol (gepoolt ueber Aera/Regime)

| Symbol | Variable | Events | Tage | KEIN BEFUND | median T_half (h) | KI90 |
|---|---|---:|---:|:---:|---:|---|
| BTCUSDT | activity_volume | 927 | 927 | nein | 0.165 | [0.160, 0.170] |
| BTCUSDT | activity_ntrades | 927 | 927 | nein | 0.204 | [0.196, 0.211] |
| BTCUSDT | realized_vol | 927 | 927 | nein | 0.081 | [0.078, 0.083] |
| ETHUSDT | activity_volume | 829 | 829 | nein | 0.145 | [0.141, 0.149] |
| ETHUSDT | activity_ntrades | 829 | 829 | nein | 0.206 | [0.199, 0.213] |
| ETHUSDT | realized_vol | 829 | 829 | nein | 0.072 | [0.070, 0.074] |
| XRPUSDT | activity_volume | 644 | 644 | nein | 0.139 | [0.133, 0.145] |
| XRPUSDT | activity_ntrades | 644 | 644 | nein | 0.179 | [0.168, 0.188] |
| XRPUSDT | realized_vol | 644 | 644 | nein | 0.072 | [0.069, 0.076] |
| SOLUSDT | activity_volume | 565 | 565 | nein | 0.140 | [0.134, 0.144] |
| SOLUSDT | activity_ntrades | 565 | 565 | nein | 0.190 | [0.183, 0.199] |
| SOLUSDT | realized_vol | 565 | 565 | nein | 0.063 | [0.062, 0.066] |
| BNBUSDT | activity_volume | 604 | 604 | nein | 0.106 | [0.102, 0.110] |
| BNBUSDT | activity_ntrades | 604 | 604 | nein | 0.157 | [0.153, 0.166] |
| BNBUSDT | realized_vol | 604 | 604 | nein | 0.067 | [0.065, 0.071] |

## (ii) RECOVERY_H_P90 (STRESS_ABS, Kostenmodell-Konstante)

| Variable | Events | Tage | KEIN BEFUND | P90 (h) | zensiert | KI90 |
|---|---:|---:|:---:|---:|:---:|---|
| activity_volume | 84 | 27 | **JA** | - | - | - |
| activity_ntrades | 84 | 27 | **JA** | - | - | - |
| realized_vol | 84 | 27 | **JA** | - | - | - |

## (iii) Aera-Vergleich -- "ist der H-20-Aera-invariant?" (deskriptiv, KEIN Gate)

| Aera | Variable | Events | Tage | KEIN BEFUND | median T_half (h) | KI90 |
|---|---|---:|---:|:---:|---:|---|
| L | activity_volume | 889 | 365 | nein | 0.125 | [0.119, 0.131] |
| L | activity_ntrades | 889 | 365 | nein | 0.163 | [0.155, 0.170] |
| L | realized_vol | 889 | 365 | nein | 0.067 | [0.065, 0.070] |
| OOS1 | activity_volume | 1044 | 403 | nein | 0.146 | [0.142, 0.151] |
| OOS1 | activity_ntrades | 1044 | 403 | nein | 0.186 | [0.180, 0.192] |
| OOS1 | realized_vol | 1044 | 403 | nein | 0.077 | [0.074, 0.081] |
| OOS2 | activity_volume | 962 | 362 | nein | 0.169 | [0.163, 0.178] |
| OOS2 | activity_ntrades | 962 | 362 | nein | 0.232 | [0.220, 0.245] |
| OOS2 | realized_vol | 962 | 362 | nein | 0.077 | [0.073, 0.081] |
| OTHER | activity_volume | 674 | 337 | nein | 0.118 | [0.111, 0.124] |
| OTHER | activity_ntrades | 674 | 337 | nein | 0.171 | [0.159, 0.186] |
| OTHER | realized_vol | 674 | 337 | nein | 0.064 | [0.061, 0.067] |

*(iii) ist rein deskriptiv: KEIN PASS/FAIL, KEINE Schwelle -- Auflage PRD 11.3.*

## Struktureller-Nulleffekt-Diagnostik (gematchter Pseudo-Zufalls-Null)

| Symbol | Variable | n_obs | n_null | Var(lambda_obs) | Var(lambda_null) | Verhaeltnis |
|---|---|---:|---:|---:|---:|---:|
| BTCUSDT | activity_volume | 927 | 928 | 6.62163 | 7.62961 | 0.87 |
| BTCUSDT | activity_ntrades | 927 | 928 | 5.33833 | 6.43309 | 0.83 |
| BTCUSDT | realized_vol | 927 | 928 | 19.03882 | 19.43745 | 0.98 |
| ETHUSDT | activity_volume | 829 | 828 | 5.45760 | 6.58151 | 0.83 |
| ETHUSDT | activity_ntrades | 829 | 828 | 3.49502 | 4.59679 | 0.76 |
| ETHUSDT | realized_vol | 829 | 828 | 17.80797 | 17.58308 | 1.01 |
| XRPUSDT | activity_volume | 644 | 644 | 7.72547 | 9.01500 | 0.86 |
| XRPUSDT | activity_ntrades | 644 | 644 | 5.22599 | 6.09265 | 0.86 |
| XRPUSDT | realized_vol | 644 | 644 | 23.23052 | 22.65000 | 1.03 |
| SOLUSDT | activity_volume | 565 | 565 | 6.11141 | 5.70765 | 1.07 |
| SOLUSDT | activity_ntrades | 565 | 565 | 4.43858 | 4.60514 | 0.96 |
| SOLUSDT | realized_vol | 565 | 565 | 23.66962 | 23.89814 | 0.99 |
| BNBUSDT | activity_volume | 604 | 604 | 11.88076 | 12.75395 | 0.93 |
| BNBUSDT | activity_ntrades | 604 | 604 | 6.69518 | 8.02217 | 0.83 |
| BNBUSDT | realized_vol | 603 | 604 | 22.69173 | 19.40969 | 1.17 |

*Diagnostik, KEIN Gate: ein Verhaeltnis nahe 1 spricht gegen einen Selektionsartefakt der Ereignis-Extremwertauswahl; Arm (a) faellt kein Urteil darauf (PRD 11.3, Exkurs X-OEKO-1 Arm (b) waere die getrennt zu registrierende Folgehypothese).*

## DEC-53-Artefakte
- real: E:\Claude\Projects\scinance\scinance3-impl\state\wp11_20260908\wp11_real_events.csv (n=10710, sha256=76344208fda31b30...)
- pseudo_null: E:\Claude\Projects\scinance\scinance3-impl\state\wp11_20260908\wp11_pseudo_null_events.csv (n=10710, sha256=989879d59aac69d6...)
- Bootstrap-Fingerprint: E:\Claude\Projects\scinance\scinance3-impl\state\wp11_20260908\wp11_bootstrap_fingerprint.json (sha256=d040da7a970f3c51...)

(Seed dieses Laufs: 42. WP-11 ist deskriptiv -- kein PASS/FAIL, keine Halbwertszeit-Schwelle.)
