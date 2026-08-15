# WP-1 · L2-Zensus-Befund — Entscheidung zur L2-TILT-Registrierung

> Auswertung des Zensus-Laufs 2026-08-14 (768 s, rc=0, 0 Fehlertage) gegen die
> in `WELLE6_KANDIDATEN_SYNTHESE_2026-08-10.md` §3 VORAB fixierte
> Entscheidungsregel. Rohdaten: `state/wp1_20260814/l2_census.{json,md}`.

## 1. Hauptbefund: Die Snapshot+Delta-Lesart ist BESTAETIGT — ueber die GESAMTE Historie

Lane C hatte per Byte-Arithmetik argumentiert, reine 500-Level-Snapshots wuerden
~17 TB allein fuer BTC bedeuten (unplausibel), und die Snapshot+Delta-Lesart als
wahrscheinlich markiert. Der Zensus entscheidet das jetzt empirisch — und zwar
deutlicher als erwartet: **schon das historische `orderbook.500`-Regime ist
Snapshot+Delta**, nicht erst das Live-Regime.

| Symbol | Regime | Zeitraum (gesampelt) | Delta-Zeilen (Sample) | Snapshots (Sample) | Tiefe Snapshot | Tiefe Delta |
|---|---|---|---:|---:|---|---|
| BTC | `orderbook.500` | 2023-01-18..2025-08-13 | 56.695.351 | 135 (~2/Tag) | exakt 500 | 0..1000 je Update |
| BTC | `orderbook.1000` | 2026-06-22..2026-08-13 | 787.944 | 7 | exakt 1000 | 0..1393 |
| ETH | `orderbook.500` | 2023-01-18..2024-05-10 | 29.751.490 | 74 (~2/Tag) | exakt 500 | 0..1152 |
| ETH | `orderbook.1000` | 2026-06-19..2026-08-13 | 1.284.968 | 13 | exakt 1000 | — |

Typischer Tag: 144k–864k Delta-Records + ~2 Voll-Snapshots. Damit ist die
17-TB-Angst vom Tisch: die realen Volumina liegen bei ~0,4–1,3 GB/Tag (BTC).

**Konsequenz nach der vorab fixierten Regel:** Der Zensus faellt NICHT gegen
die Delta-Lesart aus → **die Registrierungs-Vorbedingung fuer L2-TILT (H-22)
ist ERFUELLT.** Der Preis steht ebenfalls fest: Die Feature-Extraktion ist eine
**Snapshot+Delta-Buchrekonstruktion** (Replay je Tag ab Snapshot), kein simples
Snapshot-Lesen. Das gehoert als Aufwands- und Fehlerquellen-Klausel in die
H-22-Registrierung.

## 2. Sequenz-Integritaet: hervorragend

BTC: 66 nicht-monotone Update-ID-Schritte auf 56,7 Mio geprueften Records
(~1,2e-6) — praktisch exakt einer je Sample-Tag, konsistent mit dem
Sequenz-Neustart beim periodischen Snapshot, also erwartetes Verhalten, kein
Datenfehler. ETH `orderbook.1000` zeigt 32 Brueche auf 1,28 Mio (2,5e-5,
8/Tag) — hoeher, aber fuer eine Rekonstruktion mit Snapshot-Resync unkritisch.
**Interpretations-Hinweis (Zensus-Eigenart):** die Seq-Spalte ist je TOPIC
gezaehlt und erscheint in beiden Typ-Zeilen desselben Topics doppelt; die
Bruchzahlen duerfen nicht ueber Typ-Zeilen addiert werden.

## 3. Die Abdeckungsloecher — die eigentliche Einschraenkung fuer H-22

- **BTC:** 964 von 1304 Kalendertagen (74 %). Gesampelte `orderbook.500`-Tage
  enden 2025-08-13, `orderbook.1000` beginnt 2026-06-22 — dazwischen liegt im
  Sample NICHTS. Die Luecke 2025-08..2026-06 ist real (Inventur: 74 %).
- **ETH:** 533 Tage (41 %). `orderbook.500` endet im Sample bereits
  **2024-05-10**, `orderbook.1000` beginnt 2026-06-19 — ein ~2-Jahres-Loch.

**Konsequenz fuer die H-22-Registrierung:** Das gemeinsame Welle-6-
Fensterschema (L 2021-06..2022-12 / OOS-1 2023 / OOS-2 2024-07..2025-12) ist
fuer L2-TILT NICHT verwendbar — L2 beginnt erst 2023-01-18, und OOS-2 faellt
fuer ETH fast vollstaendig ins Loch. H-22 braucht EIGENE, gegen die
tagesgenaue Abdeckung registrierte Fenster (BTC-first; ETH nur, wo Abdeckung
existiert). Vor der Registrierung ist eine tagesgenaue Abdeckungsliste zu
ziehen (billig: Verzeichnis-Listing, kein Datenlesen) — sie wird Teil des
Registry-Eintrags.

## 4. Naechste Schritte (Reihenfolge unveraendert nach Synthese §6)

1. WP-0 fertigstellen (BTC komplett; ETH/XRP/SOL/BNB nach OOM-Fix — DEC-36).
2. Pre-Registration H-19..H-22 mit WP-0-Fingerabdruecken; H-22 mit eigenen
   Fenstern gegen die L2-Abdeckungsliste; ueberall die DEC-31/33-Pflichtzeile
   (struktureller Nulleffekt der Metrik im Feasibility-Check).
3. Laeufe: DRIFT → TAIL-AFTERMATH → LIQ-TAG → L2-TILT.
