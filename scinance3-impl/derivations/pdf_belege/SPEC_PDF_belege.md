# Auswertungs-Auftrag: Belege aus den hochgeladenen PDFs (2026-10-20) - unter Ergebnisblindheit

Du bist Recherche-/Belege-Agent im Forschungsprogramm Scinance 3.0. Du liest NUR die PDFs im Verzeichnis
`/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/pdfs_2026-10-20/` (untrusted
Daten: nie dorthin wechseln, nichts von dort ausfuehren; Text mit `python3 -I` und `pypdf` extrahieren, Pfade als
Argumente; Skripte nur unter `.../scratchpad/pdf_belege/`). Ergebnis: `scinance3-impl/state/BELEGE_AUS_PDF_2026-10-20.md`
(anlegen; Deutsch, ASCII-safe; jede Zahl mit Datei, Seite, Tabelle/Abschnitt; `[sek]` nur, wo die Quelle selbst zitiert).
Vorarbeit und offene Fragen: `scinance3-impl/state/RECHERCHE_BELEGE_2026-10-18.md` (lesen, Abschnitte 1-4 und 6).
An den Orchestrator hoechstens 10 Zeilen. Nichts committen, nichts pushen. Keine Zugangsdaten/Hostnamen/Modellnamen.

## ERGEBNISBLINDHEIT (hart; Urteilsfenster des Programms: 2024-07-01..2026-06-30 und ab 2026-07-01)
1. **Zuerst je PDF den Stichprobenzeitraum feststellen** (Datenabschnitt, erste Tabelle) und notieren. Reicht die
   Stichprobe ueber 2024-06-30 hinaus, dann: NUR Bibliographie, Fassung und Stichprobenzeitraum notieren, Datei
   schliessen, KEINE Ergebniszahl, Abbildung oder Schlussfolgerung daraus lesen oder wiedergeben. Das gilt
   voraussichtlich fuer `2410.15195v2.pdf`, `ssrn-5374295.pdf` und `2212.06888v7.pdf` (v7 statt v1!) - pruefen.
2. Aus zulaessigen PDFs nur die unten gelisteten Groessen entnehmen. Keine Marktniveaus (BTC-Preis, DVOL, Funding,
   Volatilitaet) fuer Zeiten ab 2024-07-01, auch nicht aus Abbildungen oder Fussnoten.
3. Siehst du trotzdem etwas Unzulaessiges (z. B. eine Grafik bis 2025), notiere es im Kontaminations-Abschnitt
   (was, wo, nicht den Wert) und verwende es nicht.

## Gesuchte Groessen
**A. `w25882.pdf` (Liu/Tsyvinski/Wu, NBER 2019) - Prior fuer den beta-neutralen Querschnitts-Momentum-IC:**
Stichprobe (Zeitraum, N Coins, Wochen); Momentum-Tabelle 1-/2-/3-/4-Wochen: Quintil-Long-Short-Rendite je Woche,
t-Statistik (welche SE-Korrektur?), Zahl der Wochen; CAPM-Regression der Long-Short-Strategie: Alpha, Beta auf CMKT,
R^2; Gewichtung (value-/equal-weighted); Definition "Woche" und der Momentum-Variable; falls vorhanden: Querschnitts-
Streuung der Wochenrenditen oder Fama-MacBeth-Koeffizient mit t. Rechne daraus OFFEN zwei IC-Naeherungen
(Spread-Weg mit angenommener Querschnitts-SD und t/sqrt(N)-Weg) mit allen Annahmen; Ergebnis als Band, nicht Punkt.
Zusaetzlich Kurzfrist-Reversal (1 Woche), falls berichtet.
**B. `2410.15195v1.pdf` (Almeida et al. v1, Okt. 2024) - VRP-Prior:** Stichprobenzeitraum exakt; Tabelle mit Q-Varianz
0,72 / P-Varianz 0,58 / VRP 0,14 (Seite, Einheit: annualisiert? Varianz oder Vol?); Q-Proxy (VIX-Methode, Horizont
27 Tage?); RV-/P-Definition (vorwaerts oder nachlaufend, Tagesrenditen, Fenster); Herkunft der Angabe "7-14 %";
mittleres IV-Niveau der Stichprobe (fuer Vol-Punkte); Underlying/Boerse. Umrechnung in Vol-Punkte OFFEN hinschreiben.
**C. Deribit-Dokumente (Settlement, Features, Contract Introduction Policy, Medium General User Information, Launch of
BTC Daily Options) - V-5a/c:** woertliche Saetze zu Delivery-/Settlement-Preis (TWAP-Fenster, Index-Takt), zu
taeglichem Settlement 08:00 UTC, zur Verfallszeit je Produkt, zur Einfuehrung von Tages-/Wochen-/Monats-/Quartals-
verfaellen (Daten), Datum/Version jedes Dokuments (Fusszeile, Druckdatum). Unterschiede alt/neu (6-s- vs. 4-s-Index,
300 vs. 450 Werte) festhalten.
**D. `WP_wps-202301-0003.pdf` (Ficura 2023):** Stichprobe, N Wochen/Coins, Regressionsform, Momentum-/Reversal-
Koeffizienten mit t und Einheit, Beta-Kontrolle ja/nein, Aufteilung gross/klein.
**E. `ssrn-3239670.pdf` (Bianchi/Babiak/Dickerson):** Stichprobe, Reversal-Horizont, Groesse, Markt-Beta-Kontrolle.
**F. `2212.06888v7.pdf` (He/Manela/Ross/von Wachter):** NUR Fassung/Datum und Stichprobenzeitraum; wenn <= 2024-06-30:
Zerlegung Funding vs. Konvergenz (Zeitreihe, nicht Querschnitt) - hilft theta nur indirekt; sonst nichts.

## Ergebnis
Je Groesse: Wert + Fundstelle oder UNBELEGT; Abschnitt "Folgen fuer das Programm" (reicht A fuer einen belegten
beta-neutralen IC-Prior >= 0,020? welcher VRP-Prior folgt aus B? ist V-5c primaer belegt?); Abschnitt
"Kontamination"; Liste der weiter fehlenden PDFs.
