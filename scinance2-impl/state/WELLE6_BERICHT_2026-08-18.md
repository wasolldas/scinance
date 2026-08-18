# Welle-6-Bericht (Stand 2026-08-18; H-21 kalendarisch ausstehend)

> Orchestrator-Bericht nach Adjudikation von H-19/H-20/H-22 (GL-025/026/027).
> Welle 6 war die erste Welle unter dem Determinismus-Regime (DEC-34/35):
> alle Laeufe lasen ausschliesslich fingerprint-gepinnte, unveraenderliche
> Stores. H-21 (LIQ-TAG) bleibt bis zum Fensterschluss 2026-12-27 gesperrt.

## 1. Ergebnisse

| Hypothese | Verdikt | Kern |
|---|---|---|
| **H-19 DRIFT** | STATIONAER-GENUG (GL-025, META) | 0/15 Zellen; Regime-Splitting-Auflage NICHT ausgeloest. Deskriptiv: D3-Aktivitaets-Konzentration zeigt einen ABGESCHLOSSENEN Uebergang (2021→2024), keinen laufenden Drift. |
| **H-20 TAIL-AFTERMATH** | **DROP** (GL-026) | Reversions-Tendenz vorhanden (+5/+17 bp, Mediane +14/+20), aber Vorzeichen kippt ueber Symbole und Fenster; L-Fenster 2021-22 zeigt das GEGENTEIL (−40 bp). Kein p unter 0,17. |
| **H-21 LIQ-TAG** | GESPERRT | Fenster 2026-07-01..09-28 / 09-29..12-27; Lauf ~Ende Dezember. |
| **H-22 L2-TILT** | **DROP** (GL-027) | BTC IC +0,067/−0,011 gegen Schwelle 0,10; A-priori „DROP erwartet" bestaetigt. 2023/24-Aera zeigt bei BTC UND ETH ein schwaches +0,06-Signal knapp ueber dem Rauschboden — nicht persistent. |

**Programm-Gesamtstand: 27 Gate-Eintraege, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.** Mess-Existenzen (kapitalfrei): H-04-Lead-Lag, H-05b-OFI-Invers, H-15-Grammatik, H-16-Zeit-Asymmetrie (Envelope-Traeger). Alle Tradability-Brücken bisher PARK oder tot.

## 2. Was Welle 6 methodisch geliefert hat (dauerhaft)

1. **Reproduzierbarkeit by construction:** WP-0-Bar-Cache (10.054 Tage, 14,4 Mio Minuten, ordnungs-unabhaengige Aggregate) und WP-2-Tilt-Store (1.098 Tage, snapshot-validierte Buchrekonstruktion) — beide hash-gepinnt, beide cross-run bit-identisch belegt. Jeder Welle-6-Lauf verifizierte seine Fingerabdruecke VOR der Messung; alle vier Laeufe: 100 % Match.
2. **Geschwindigkeit:** H-19 527 s · H-20 95 s · H-22 27 s. Die gesamte Welle (drei Hypothesen ueber 2,5–6 Jahre Historie) kostete nach den Vorleistungen unter 15 Minuten Rechenzeit. Falsifikation ist billig geworden — das war der Sinn von WP-0/WP-2.
3. **Schwellen-Kalibrierung gegen den strukturellen Nulleffekt** (DEC-31/33-Pflichtzeile) hat sich dreifach bewaehrt: H-19s Rotations-Null verhinderte einen Falsch-Positiv bei |rho|=0,49 (persistente Serie!), H-20s +10-bp-Boden und H-22s 0,10-IC-Schwelle lagen jeweils ueber dem Rauschboden — die knappen Punktschaetzer (+17 bp; IC +0,067) konnten das Programm nicht in Scheinbefunde locken.
4. **Die Ereignis-/Abdeckungs-Floors** (100 Event-Tage; 85 %) waren erfuellt — kein Verdikt haengt an Datenmangel. Die DROPs sind echte Falsifikationen, keine Power-Artefakte.

## 3. Uebergreifender inhaltlicher Befund: die Aera-Abhaengigkeit

Drei unabhaengige Messungen zeigen dasselbe Muster: D3-Konzentrations-Uebergang bis ~Mitte 2024 (GL-025), Nach-Schock-Verhalten kippt von Fortsetzung (2021-22) zu schwacher Reversion (2023-25, nicht signifikant; GL-026), Tilt-IC existiert schwach in 2023/24 und verschwindet in 2024/25 (GL-027). **Der Markt der Jahre 2021–2024 war strukturell ein anderer als der von 2025.** Fuer kuenftige Wellen heisst das: Mehrjahres-Historie liefert POWER, aber Hypothesen muessen Effekte behaupten, die im JUENGSTEN Regime existieren — sonst misst man Archaeologie.

## 4. Wie weiter

1. **H-21 LIQ-TAG** laeuft Ende Dezember 2026 (Entsperrung kalendarisch); bis dahin sammelt der Collector.
2. **Reservekandidaten** (Synthese §5) nach den Welle-6-Lehren neu bewertet: IMPACT-PERSISTENZ (CPU-billig, Positivkontrolle nach GL-020-Muster) und SWEEP-PRE (nach WP-2 jetzt trivial billig) sind die naechstliegenden; beide brauchen neue Registrierung mit Rezenz-Klausel (§3-Lehre: Effekt muss im juengsten Regime behauptet werden).
3. **What-else-Phase** (vom Nutzer verschoben): H-17b-Aufloesung wartet weiter.
4. **GPU-Vertiefungen** (REACH-LADDER, DAY-BRIDGE) bleiben vertagt: DAY-BRIDGE — der einzige direkte Tradability-Versuch — setzt Tages-Skalen-Struktur voraus, die H-20/H-22 gerade NICHT belegt haben. Die Synthese-Sequenzierung („erst zeigen, dass auf Tagesskala Struktur existiert") hat sich als richtig erwiesen; die Vorbedingung ist aktuell NICHT erfuellt.

*27 s fuer die letzte Falsifikation der Welle. Die Registry-Disziplin haelt: kein Torpfosten bewegt, jede A-priori-Erwartung protokolliert, zwei davon widerlegt (H-11-PASS, H-20-Offenheit), eine bestaetigt (H-22-DROP).*
