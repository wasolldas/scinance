# Gemeinsamer Recherche-Auftrag (Phase 3, Scinance 3.0)

## Kontext (Pflichtlektuere VOR jeder Recherche)
1. /home/user/scinance/scinance3-impl/survey/ERKENNTNIS_KOMPENDIUM.md  — VOLLSTAENDIG lesen.
   Abschnitt D (verworfene Ansaetze) und C (Methoden-Lehren) sind bindend:
   kein Vorschlag darf einen dort als tot markierten Ansatz ohne NACHWEISLICH
   neues Signal wiederholen. Abschnitt F ist der Datenbestand.
2. /home/user/scinance/scinance3-impl/survey/INFRA_OPS_MAP.md — Abschnitte 1, 2, 6.
3. Die 2.0-Verfassung liegt unter /home/user/scinance/FINAL_PRD.md ODER (falls
   gerade verschoben) /home/user/scinance/scinance2-impl/FINAL_PRD_SCINANCE2.md —
   Abschnitte 1, 2, 5 (PARK-Register), 8 (Multiple-Testing) lesen.

## Programm-Bilanz, die den Auftrag motiviert
31 Gate-Eintraege, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten. ALLE
gemessenen Rohkanten auf Sekunden-/Minuten-Skala liegen 80-500x unter der
Round-Trip-Friktionswand (11 bps Taker, ~15 bps inkl. Slippage; Maker 4 bps,
aber Top-of-Book ist exakt ein Tick, Spread-Capture tot). Minuten-Impact ist
permanent (Forward-IC negativ, stabil ueber 10 Halbjahre). Der einzige lebende
Pfad ist Praemien-Ernte auf Optionen (H-26 VRP, gesperrt bis Mitte November).
Konsequenz: 3.0 sucht dort, wo die Wand irrelevant wird — Risikopraemien und
Tages- bis Wochen-Horizonte — oder wo die Ertragsquelle keine Prognose braucht.

## Harte Randbedingungen fuer JEDEN Vorschlag
- Einzelner Retail-Betreiber auf Bybit (Perps, Spot, USDT/USDC-Optionen);
  Deribit nur als DATENquelle (Messbasis), nicht als Handelsplatz-Annahme.
- Kein Live-Order-Code im Programm; Ziel sind FALSIFIZIERBARE, kapitalfreie
  Mess-Hypothesen mit vorab fixierten Gates, dann separate Tradability-Gates.
- Hardware: PC mit RTX 5060 Ti (16 GB VRAM), 82 GB RAM, Windows; plus ein
  Thin-Client (Datensammler, keine Analyse). Jede Analyse muss auf dem PC
  laufen, GPU-Laeufe ueber Nacht mit Checkpoint/Resume.
- Datenzugang: der vorhandene Harvest-Baum (Kompendium F.1) plus alles, was
  OEFFENTLICHE Bybit-v5-/Deribit-/Binance-Endpunkte ohne Keys liefern
  (z. B. Klines fuer hunderte Symbole, Funding-Historie, OI-Historie).
  Keine bezahlten Datenquellen annehmen, ohne Preis und Notwendigkeit zu nennen.
- Registry-Disziplin: fuer jeden Kandidaten ist zu benennen, WAS ihn vorab
  toeten wuerde (Feasibility-Check nach GL-012: ist die Schwelle auf den
  Daten ueberhaupt erreichbar?), welcher strukturelle Nulleffekt der Metrik
  vorab auszurechnen ist (DEC-31/33), und welches positive + negative
  synthetische Fixture ihn pruefen wuerde (DEC-39).

## Ausgabeformat (Deutsch, ASCII-safe ae/oe/ue/ss, Markdown)
Pro Kandidat GENAU dieser Block:
### K-<nn> <Kurztitel>
- **Ertragsquelle:** (Praemie / Prognose / Struktur / Ereignis) — in einem Satz, warum sie existieren SOLLTE (oekonomischer Mechanismus, wer zahlt und warum)
- **Horizont & Instrument:** 
- **Literatur/Evidenz:** konkrete Quellen (Autor, Jahr, Kernzahl) — bei Unsicherheit als "unbelegt" markieren, NICHT erfinden
- **Erwartete Groessenordnung vs. Friktion:** Schaetzung der Bruttokante in bps oder Vol-Punkten je Trade/Periode, gegen die gemessenen Kosten (Perp 11/15 bps Taker-RT, 4 bps Maker-RT; Optionen 2/3 bp Index je Fill, vega/S 5,2 bp je Vol-Punkt)
- **Daten:** was aus dem Bestand reicht, was nachzuladen waere (Endpunkt, Volumen, Aufwand)
- **Rechenaufwand:** CPU/GPU, Groessenordnung, PC-tauglich?
- **Kapitalfreies Mess-Gate (Entwurf):** Metrik, Fenster (REZENZ-Klausel!), Schwelle mit Herleitung des Rauschbodens, FDR-Familie
- **Was ihn a priori toetet:** 
- **Bezug zu Kompendium D/E:** welche toten Ansaetze er NICHT wiederholt, welche offenen Faeden er nutzt
- **Vertrauen:** hoch/mittel/niedrig mit Begruendung
Am Ende: Rangliste der Kandidaten, und ein Abschnitt "Was ich NICHT vorschlage und warum".
Ziel: 5-8 Kandidaten je Auftrag, Tiefe vor Breite. Keine Wiederholung des Kompendiums.
