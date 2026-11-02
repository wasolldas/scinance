# Konto Zone X (Exploration) - append-only (DEC-104 E4 (c))

> Zweck: Jede Explorationsabfrage auf Zone-X-Daten (vor 2024-07-01; DEC-104 E4 (a)) wird hier **vor der Rechnung**
> eingetragen und **nach der Rechnung** mit dem Ergebnis als Schaetzer/CI/Ausschlussgrenze ergaenzt. Nie ein Verdikt.
> Das Konto ersetzt fuer Zone X die Verbrauchsregel DEC-99 (5); es ist die Buchung, die eine Exploration erst erlaubt.
> Siegel- und Zonenregeln: Zone V (W1/W2) und Zone K (ab 2026-07-01) duerfen hier **nicht** erscheinen.
> Oeffentliches Repo: keine Hostnamen, keine Zugangsdaten, keine Marktniveaus; Nuisance-Ausgaben nach DEC-103 N1 (2c).

## Regeln der Buchung

1. Vor der Rechnung: Datum, Familie (DEC-58 E2 / F-WEEK-Zuordnung), Statistik (exakt), Fenster (Zone X, Datumsgrenzen),
   Varianten (Anzahl K und Liste oder Erzeugungsregel), Code-Hash (sha256 des Skripts, das im Repo liegt - keine Zahl
   ohne versioniertes Skript), Zweck (Zensus S0/S1, Screen S2, Nullwelt, Kostenmodell).
2. Nach der Rechnung: Schaetzer, 95-%-CI, obere einseitige Ausschlussgrenze (95 %), Shrinkage-Hinweis, Selektions-K
   kumuliert fuer diese Familie, Datei der Ausgabe (Repo-Pfad, sha256).
3. Jede Registrierung, die Richtung oder Groessenordnung aus einer Konto-Zeile bezieht, zitiert die Zeilennummer und
   rechnet den Prior selektionsbereinigt (DEC-99 (3), DEC-104 E3 (c)).
4. Historische Oeffnungen vor dem 2026-11-02 stehen in den C.17-Listen der Registrierungen und werden im Konto-Inventar
   (PRD_ANALYSE 9.2 Nr. 6) nachgetragen; sie zaehlen fuer K der jeweiligen Familie.

## Eintraege

| Nr. | Datum | Familie | Statistik | Fenster (Zone X) | K / Varianten | Code (Repo-Pfad, sha256) | Zweck | Ergebnis (Schaetzer; 95-%-CI; Ausschlussgrenze) | Ausgabe-Datei |
|---|---|---|---|---|---|---|---|---|---|
| - | - | - | (noch keine Zone-X-Abfrage unter DEC-104) | - | - | - | - | - | - |
