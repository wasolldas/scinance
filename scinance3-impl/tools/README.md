# tools - Hilfswerkzeuge

`channel_scan.py <datei.json>`: Struktur-Scan einer Nuisance-JSON nach DEC-103 N1 (2c). Sucht Eintraege mit Zaehlung n
und Streuung, gruppiert sie nach "ein Pfadsegment als Platzhalter" und meldet Gruppen, in denen eine Klassenzaehlung
die Summe von zwei oder drei anderen ist (Verschachtelung: eine Varianzzerlegung wuerde einen Mittelwertunterschied
verraten); listet Union-/Shift-aehnliche Schluessel mit Zahlenwert. Kombiniert nie Werte. Aufruf:
`python3 -I scinance3-impl/tools/channel_scan.py <datei.json>`. Geplant (F0/F1): als Test ueber alle JSON unter `state/`
vor jedem Commit (Ausgabe ist ein Zaehl-/Strukturbericht, kein Werteabzug). Erwartete Treffer auf `a2_vorarbeit.json`:
geschachtelte Gruppen (Review B-2, C.17-Vermerk); auf `a2_teilC.json`: kein Tripel derselben Reihe.
