# V-1-Empirie: Funding je Intervallklasse (DEC-82, deskriptiv, kein Urteil)

Union-Panel 1138 Symbole (877 + 261 delistet), 2021-01-01..2026-09-16, as_of 2026-09-28.
Totzonen-Anteil gesamt (skaliertes I): 0.5039 (329147/653261)

## DEC-82: Totzone je Intervallklasse gegen Kandidaten-I (deskriptiv, kein Urteil)
Treffer = Tagesmittel funding_sum/funding_n innerhalb tol von I(m) = 0.0001*m/480; gemessen, keine Diagonale angenommen.
- Klasse 60min: n_symbol_tage=16532 (Tagesmittel NaN: 0)
  - Treffer gegen I: I_60min=4950 (0.2994); I_120min=0 (0.0000); I_240min=0 (0.0000); I_480min=0 (0.0000)
  - haeufigste Tagesmittel: 0.0000125 n=4949 (0.2994); 0.0000018158 n=3 (0.0002); 0.0000076929 n=3 (0.0002); 0.0000104325 n=3 (0.0002); 0.0000110025 n=3 (0.0002)
- Klasse 120min: n_symbol_tage=6723 (Tagesmittel NaN: 0)
  - Treffer gegen I: I_60min=0 (0.0000); I_120min=3315 (0.4931); I_240min=0 (0.0000); I_480min=0 (0.0000)
  - haeufigste Tagesmittel: 0.000025 n=3315 (0.4931); -0.0000534375 n=2 (0.0003); -0.0000467117 n=2 (0.0003); -0.000045825 n=2 (0.0003); -0.00004451 n=2 (0.0003)
- Klasse 240min: n_symbol_tage=196427 (Tagesmittel NaN: 0)
  - Treffer gegen I: I_60min=2 (0.0000); I_120min=1 (0.0000); I_240min=104237 (0.5307); I_480min=0 (0.0000)
  - haeufigste Tagesmittel: 0.00005 n=104237 (0.5307); 0 n=168 (0.0009); 0.0000413567 n=8 (0.0000); 0.000045575 n=8 (0.0000); 0.0000253417 n=7 (0.0000)
- Klasse 480min: n_symbol_tage=431173 (Tagesmittel NaN: 0)
  - Treffer gegen I: I_60min=4 (0.0000); I_120min=2 (0.0000); I_240min=30 (0.0001); I_480min=216645 (0.5025)
  - haeufigste Tagesmittel: 0.0001 n=216645 (0.5025); 0 n=10266 (0.0238); 0.00000001 n=260 (0.0006); 0.00005 n=30 (0.0001); 0.0000996333 n=13 (0.0000)


## DEC-82: Intervallklassen-Episoden, getrennt vor/ab 2025-10-30 (deskriptiv, kein Urteil)
Datum 2025-10-30 ist [sek]-Angabe (nicht primaer belegt). Lauf = aufeinanderfolgende klassifizierte Tage derselben Klasse; Tage ohne Funding/unklassifiziert werden uebersprungen; Zuordnung nach Laufbeginn; Dauer = Kalendertage erster..letzter Tag, nur bis zum Wechsel in die naechste Klasse (am Panelende offene und durch Datenende/Delisting beendete Laeufe sind zensiert und ohne Dauer).
- 60min vor: laeufe=63 offen_am_ende=0 durch_datenende_beendet=8 | Dauer Tage (n=55): median=224.0 q10=60.4 q25=137.5 q75=272.0 q90=327.0 max=393
- 60min ab: laeufe=161 offen_am_ende=3 durch_datenende_beendet=2 | Dauer Tage (n=156): median=8.0 q10=1.0 q25=2.8 q75=49.2 q90=92.0 max=123
- 120min vor: laeufe=39 offen_am_ende=0 durch_datenende_beendet=1 | Dauer Tage (n=38): median=134.5 q10=1.0 q25=4.0 q75=335.8 q90=381.3 max=415
- 120min ab: laeufe=37 offen_am_ende=0 durch_datenende_beendet=1 | Dauer Tage (n=36): median=1.0 q10=1.0 q25=1.0 q75=1.0 q90=2.5 max=3
- 240min vor: laeufe=424 offen_am_ende=208 durch_datenende_beendet=88 | Dauer Tage (n=128): median=152.5 q10=1.0 q25=11.5 q75=315.8 q90=425.9 max=793
- 240min ab: laeufe=279 offen_am_ende=205 durch_datenende_beendet=11 | Dauer Tage (n=63): median=32.0 q10=3.0 q25=10.0 q75=69.0 q90=141.0 max=184
- 480min vor: laeufe=612 offen_am_ende=152 durch_datenende_beendet=145 | Dauer Tage (n=315): median=242.0 q10=1.0 q25=43.0 q75=463.5 q90=1023.6 max=1793
- 480min ab: laeufe=284 offen_am_ende=260 durch_datenende_beendet=5 | Dauer Tage (n=19): median=1.0 q10=1.0 q25=1.0 q75=5.5 q90=85.4 max=140
- Uebergaenge vor: 120min->240min=10; 120min->480min=1; 120min->60min=8; 240min->120min=21; 240min->480min=15; 240min->60min=29; 480min->120min=10; 480min->240min=262; 480min->60min=15; 60min->120min=5; 60min->240min=3; 60min->480min=7
- Uebergaenge ab: 120min->240min=24; 120min->480min=1; 120min->60min=30; 240min->120min=28; 240min->480min=2; 240min->60min=96; 480min->240min=15; 480min->60min=32; 60min->120min=9; 60min->240min=158; 60min->480min=29
- Symbole mit mind. einem 60min-Lauf: vor=59 ab=129

