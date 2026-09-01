# Rueckmeldung an das Harvest-Projekt: JA, die Entsperr-Bedingung fragt genau die beiden nicht registrierten Stroeme ab

> Antwort auf die Registrar-Abschlussmeldung (2026-09-01): „Bewusst nicht
> registriert sind deribit/publicTrade und deribit/dvol ... Falls die
> Entsperr-Bedingung einen dieser beiden abfragt, bitte melden."
> Erstellt nach DEC-50. Kontakt zurueck ueber den Nutzer.

## 1. Der Treffer

Die **H-26-Entsperr-Bedingung** (Varianz-Risiko-Praemie, der einzige aktive
Strategie-Pfad des Programms) lautet woertlich: lueckenlose `done_days`
fuer **deribit `dvol` UND `publicTrade`** je Symbol (BTC, ETH) ueber
**>=210 zusammenhaengende Tage**. Zieltermin der Entsperrung: ~Mitte
November 2026. Es sind exakt die beiden Stroeme, die der Registrar bewusst
auslaesst.

Euer Vorbehalt ist dabei fachlich richtig und soll NICHT aufgeweicht
werden: ein pauschales DONE, das partielle Tage versiegelt, waere genau
der Fehler, gegen den das Manifest schuetzt. Wir brauchen keine pauschale
Loesung, sondern diese Zusicherung:

## 2. Was Scinance konkret braucht

1. **DONE je (Strom, Symbol, Tag) erst nach Vollstaendigkeits-Pruefung**
   durch den Backfill — nach euren Kriterien (Zeilen-/Byte-Zahlen aus den
   Parquet-Footern, wie beim Registrar). Kein Sonderweg, nur die
   bestehende Backfill-DONE-Semantik, angewandt auch auf die
   live-gesammelten Tage dieser zwei Stroeme.
2. **Begrenzter Nachlauf:** H-26 braucht die 210 Tage ZUSAMMENHAENGEND bis
   nahe an die Gegenwart. Entscheidend ist deshalb, dass abgeschlossene
   UTC-Tage binnen weniger Tage (Richtwert: <=3) ihre DONE-Zeile
   bekommen. Ein Backfill, der Wochen hinterherlaeuft, verschiebt die
   Entsperrung 1:1 nach hinten.
3. **Keine Luecken-Kosmetik:** Tage, die der Backfill nicht vervollstaendigen
   kann, bleiben ohne Zeile sichtbar (euer „laut scheitern" — genau richtig).
   Eine sichtbare Luecke verschiebt das 210-Tage-Fenster; eine versiegelte
   Teilmenge wuerde das Urteil verfaelschen.

## 3. Zur Kontrolle, wenn es steht

Ein Einzeiler auf der Nutzer-Maschine genuegt uns als Abnahme (read-only,
gegen `state\harvest_manifest.backup.sqlite` — DIE Datei, siehe unten):

    python scinance2-impl\handoff_local\harvest_coverage.py --exchange deribit --stream dvol --symbol BTC

Erwartung: zusammenhaengende DONE-Reihe vom Streambeginn (~2026-04) bis
maximal ~3 Tage vor heute, fuer dvol und publicTrade, BTC und ETH.

## 4. Was Scinance seinerseits umgestellt hat (DEC-50)

Eure zweite Praezisierung — zwei Manifest-Dateien, die alte
`harvest_manifest.sqlite` ist die eingefrorene Windows-Aera ohne
Registrar-Zeilen — ist bei uns verankert: `resolve_manifest_path()`
bevorzugt ab sofort ueberall `harvest_manifest.backup.sqlite`, faellt nur
bei deren Abwesenheit auf den Legacy-Namen zurueck und ist per Unit-Test
gepinnt (leere Legacy + gefuellter Export -> der Export gewinnt). Das
Coverage-Werkzeug meldet, welche Datei es liest. Die `archived_at`-Semantik
(DONE bleibt wahr nach Auslagerung) ist fuer uns unkritisch, da die
Messlaeufe auf derselben Maschine wie das PC-Archiv laufen.
