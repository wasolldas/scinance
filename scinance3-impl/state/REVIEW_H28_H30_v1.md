# Adversarischer Review H-28/H-29/H-30 Erstfassung (Opus, 2026-09-21) - Kurzfassung

Vollstaendiger Review im Sitzungsprotokoll des Orchestrators; die bindenden Befunde sind in DEC-74 Entscheidung 2 (a)-(k) uebernommen. Verdikt des Reviewers: nicht gegen die Erstfassung bauen; Zweitfassung nach Vorlauf.

Bestaetigte Zahlen (vom Orchestrator nachgerechnet aus `state/runs/wp7_20260921/decile_degeneration_weekly.csv` und `null_ic_per_window_w52.json`):

| Fenster | Wochen | K min/Median/max | E_t[1/sqrt(K_t-1)] | IC_min bei rho=0 |
|---|---|---|---|---|
| W1 2024-07-01..2025-06-30 | 53 | 345/419/515 | 0,04849 | 0,01656 |
| W2 2025-07-01..2026-06-30 | 52 | 514/589/606 | 0,04190 | 0,01445 |
| L 2021-03-01..2024-06-30 | 174 | 5/175/340 | 0,1406 | (nicht urteilstragend) |
| Messfenster Erstfassung 2025-09-22..2026-09-14 | 52 | 546/593/719 | 0,04094 | 0,01412 |

Identitaet bestaetigt: Mittel der gemessenen sd_null 0,0411229 vs. E_t[1/sqrt(K_t-1)] 0,0411160 (51 Wochen).

Weitere Befunde (WICHTIG/KOSMETIK), nicht in DEC-74 einzeln aufgefuehrt: K-Zitate 412/538 in Teil 6/Gesamtbilanz gehoeren zum Lauf 2026-09-14 (aktueller Lauf: 546/593); `null_ic_*` und `null_ic_funding_excess_key_*` haben identische Hashes (signal-agnostische Null, DEC-70 E4, im Report zu etikettieren); B4 rechnet mit 11 bp, Etikett mit 18 bp (zwei Kostenbasen); DEC-59-Verweis fuer das Kostenkonstanten-Modul ist im Log anders belegt; Report-Artefaktpfade sind lokale Pfade.
