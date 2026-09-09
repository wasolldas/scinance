# WP-11 -- Relaxationsrate nach Schockstunden (deskriptiv, KEIN VERDIKT)

- **Paket:** WP-11 -- `PRD_SCINANCE3.md 11.3 (DEC-58); Exkurs X-OEKO-1 Arm (a)`
- **Erzeugt:** 2026-09-09T12:26:15+00:00 (UTC) - Status: RUN
- **Semantik:** DESKRIPTIV (Arm (a), PRD 11.3): kein PASS/FAIL, keine Schwelle -- Halbwertszeit ist Deskriptor
- **Datenbindung:** WP-0-Bar-Cache - `gate_valid=true`
- **Ereignisse:** 3570 real, 3570 gematchter Pseudo-Null, 1468 Ereignistage gesamt
- **Event-Definition:** WOERTLICH aus H-20 geerbt (c20_tail.driver), kein neuer Parameter
- **v2 Profil-Fit (urteilstragend):** v2: Superposed-Epoch-Profil (Mittel/Median) je Gruppe in Ereigniszeit, Cluster-Bootstrap (Kalendertag), Differenzprofil real minus gematchte Pseudo-Null (struktureller Selektions-Bump wird gemessen und abgezogen); Exponential- UND Potenz-gesetz-Fit (Omori-artig) auf dem Differenzprofil-Mittel, geschlossene log-lineare Regression mit gebatchtem Bootstrap-Parameter-KI
- **v1 AR(1) (Diagnostik, NICHT urteilstragend):** AR(1)-aequivalenter Zerfall der Ueberschussreihe (5-Min-Buckets, 24h post-shock), lambda = -ln(phi)/dt_h, half_life = ln2/lambda -- PER-EVENT DIAGNOSTIC ONLY (v2, Orchestrator-Abnahme 2026-09-08); siehe 'profile_fit' fuer die urteilstragende Groesse
- **Time-to-Return:** erste Stunde mit |excess| <= 10% des Schock-Excess; rechts-zensiert bei 24h (per-Ereignis, Diagnostik) bzw. je Bootstrap-Replikat-Profil (v2, RECOVERY_H_P90)

> **Orchestrator-Abnahme 2026-09-08 (Echtlauf, 3.570 Ereignisse):** die per-Ereignis-AR(1)-Halbwertszeit war fuer die Frage uninformativ (gematchte Pseudo-Null praktisch identisch mit den realen Medianen). v2 ersetzt (i)-(iii) und RECOVERY_H_P90 durch die Superposed-Epoch-Profilgroessen unten; die alten AR(1)-Tabellen bleiben als Diagnostik erhalten (nicht geloescht).

## (i) Halbwertszeit des Differenzprofils je Symbol (v2, urteilstragend)

| Symbol | Variable | Events | Tage | KEIN BEFUND | T_half (h) | KI90 | R^2 (exp) | p (Potenzgesetz) |
|---|---|---:|---:|:---:|---:|---|---:|---:|
| BTCUSDT | 927 | 927 | nein | 24.644 | [18.234, 34.562] | 0.343 | 0.271 |
| BTCUSDT | 927 | 927 | nein | 23.629 | [17.294, 33.645] | 0.373 | 0.279 |
| BTCUSDT | 927 | 927 | nein | 30.849 | [21.609, 45.001] | 0.297 | 0.229 |
| ETHUSDT | 829 | 829 | nein | 22.143 | [16.104, 31.067] | 0.288 | 0.312 |
| ETHUSDT | 829 | 829 | nein | 22.124 | [16.143, 31.469] | 0.293 | 0.320 |
| ETHUSDT | 829 | 829 | nein | 29.802 | [20.922, 44.048] | 0.237 | 0.254 |
| XRPUSDT | 644 | 644 | nein | 13.629 | [11.030, 16.690] | 0.324 | 0.358 |
| XRPUSDT | 644 | 644 | nein | 7.246 | [5.907, 8.601] | 0.441 | 0.397 |
| XRPUSDT | 644 | 644 | nein | 15.681 | [12.450, 20.001] | 0.309 | 0.316 |
| SOLUSDT | 565 | 565 | nein | 2.481 | [2.085, 2.926] | 0.830 | 0.422 |
| SOLUSDT | 565 | 565 | nein | 11.723 | [9.351, 14.374] | 0.270 | 0.391 |
| SOLUSDT | 565 | 565 | nein | 21.185 | [15.388, 30.105] | 0.257 | 0.273 |
| BNBUSDT | 604 | 604 | nein | 13.392 | [9.990, 17.517] | 0.196 | 0.347 |
| BNBUSDT | 604 | 604 | nein | 15.579 | [11.579, 20.751] | 0.217 | 0.353 |
| BNBUSDT | 604 | 604 | nein | 19.951 | [14.210, 29.065] | 0.182 | 0.292 |

## (ii) RECOVERY_H_P90 (STRESS_ABS, Kostenmodell-Konstante, v2: Profil-Replikate)

| Variable | Events | Tage | KEIN BEFUND | P90 (h) | zensiert | n_Replikate |
|---|---:|---:|:---:|---:|:---:|---:|
| activity_volume | 84 | 27 | **JA** | - | - | - |
| activity_ntrades | 84 | 27 | **JA** | - | - | - |
| realized_vol | 84 | 27 | **JA** | - | - | - |

## (iii) Aera-Vergleich -- "ist der H-20-Aera-invariant?" (v2, deskriptiv, KEIN Gate)

| Aera | Variable | Events | Tage | KEIN BEFUND | T_half (h) | KI90 | R^2 (exp) | p (Potenzgesetz) |
|---|---|---:|---:|:---:|---:|---|---:|---:|
| L | 889 | 365 | nein | 10.864 | [8.291, 13.512] | 0.256 | 0.371 |
| L | 889 | 365 | nein | 2.701 | [2.213, 3.212] | 0.798 | 0.407 |
| L | 889 | 365 | nein | 19.011 | [14.405, 25.807] | 0.255 | 0.263 |
| OOS1 | 1044 | 403 | nein | 22.092 | [15.866, 31.307] | 0.388 | 0.278 |
| OOS1 | 1044 | 403 | nein | 23.692 | [16.587, 33.931] | 0.353 | 0.271 |
| OOS1 | 1044 | 403 | nein | 27.148 | [18.756, 39.847] | 0.312 | 0.245 |
| OOS2 | 962 | 362 | nein | 17.324 | [12.579, 23.564] | 0.312 | 0.324 |
| OOS2 | 962 | 362 | nein | 19.167 | [13.966, 26.557] | 0.297 | 0.317 |
| OOS2 | 962 | 362 | nein | 25.354 | [17.892, 36.917] | 0.260 | 0.253 |
| OTHER | 674 | 337 | nein | 2.381 | [1.914, 2.919] | 0.808 | 0.358 |
| OTHER | 674 | 337 | nein | 20.923 | [14.234, 31.103] | 0.221 | 0.297 |
| OTHER | 674 | 337 | nein | 28.770 | [18.944, 45.660] | 0.347 | 0.205 |

*(iii) ist rein deskriptiv: KEIN PASS/FAIL, KEINE Schwelle -- Auflage PRD 11.3.*

## Diagnostik: per-Ereignis-AR(1) (v1, NICHT urteilstragend, unveraendert)

*PER-EVENT AR(1)-Diagnostik, NICHT urteilstragend (Orchestrator-Abnahme 2026-09-08): misst das generische Kurzgedaechtnis der 5-Min-Excess-Reihe, nicht die Schock-Relaxation -- siehe 'profile' fuer die Superposed-Epoch-Analyse, die diese Frage tatsaechlich beantwortet.*

| Symbol | Variable | Events | Tage | KEIN BEFUND | median T_half (h, AR1) | KI90 |
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
- profile_matrix (v2, urteilstragend): E:\Claude\Projects\scinance\scinance3-impl\state\wp11_20260909\wp11_profile_matrix.csv (n_groups=27, n_rows=7776, sha256=362b12f56339d566...)
- real_events (v1, Diagnostik): E:\Claude\Projects\scinance\scinance3-impl\state\wp11_20260909\wp11_real_events.csv (n=10710, sha256=76344208fda31b30...)
- pseudo_null_events (v1, Diagnostik): E:\Claude\Projects\scinance\scinance3-impl\state\wp11_20260909\wp11_pseudo_null_events.csv (n=10710, sha256=989879d59aac69d6...)
- Bootstrap-Fingerprint: E:\Claude\Projects\scinance\scinance3-impl\state\wp11_20260909\wp11_bootstrap_fingerprint.json (sha256=db3fef0660231c71...)

(Seed dieses Laufs: 42. WP-11 ist deskriptiv -- kein PASS/FAIL, keine Halbwertszeit-Schwelle.)
