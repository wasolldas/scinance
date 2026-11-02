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
| 1 | 2026-11-02 (Eintrag; Lauf nach Rueckkehr des Datendienstes) | Nullwelt/Nuisance Klasse W | IK-05: Eigenwerte der Pearson-Korrelationsmatrix der Marktresiduen e = r - beta r_M (r = ln(C_t/C_t-1) lineare USDT-Perps aus rest.kline1d ALL; r_M gleichgewichtetes Tagesmittel; beta OLS ueber das Fenster) auf dem balancierten Teilpanel (Symbole >= 90 % Abdeckung, nur Tage mit allen Symbolen); Ausgabe: K, T, Top-20-Eigenwerte, MP-Kante (1+sqrt(K/T))^2, Anzahl > Kante, Anzahl >= 6,25, erklaerte Varianz; dasselbe fuer Roh-Renditen, drei Teilfenster und Rang-Korrelation | 2021-01-01..2024-06-30 | K = 1 (eine Konfiguration: coverage-min 0,9, min-days 250) | src/bybit_edge/research/zone_x/{common,ik05_rmt,run_zone_x_1}.py (sha256 common 5e6e12b3..., ik05_rmt 6f4dd910..., run b32a1450...) | S1 (Streuung/Struktur; keine Mittel, keine Vorzeichen) | ausstehend | ausstehend (zone_x_1.json, Pfad beim Lauf) |
| 2 | 2026-11-02 (Eintrag; Lauf wie Nr. 1, dieselbe Ausgabe) | Nullwelt/Nuisance Klasse W | IK-04: Exzess-Kurtosis und Schiefe der Tagesrenditen r und der Marktresiduen e je Symbol (Ausgabe nur Quantile q10/q25/q50/q75/q90 ueber Symbole, gesamt und je Umsatz-Terzil); Querschnitts-SD der r je Tag (Quantile ueber Tage, Mittel ueber Tage, ACF Lag 1..5); ACF Lag 1..5 von |r_M|; effektive Clusterzahl n_eff fuer 365 Tage; Anteil fehlender Tage | 2021-01-01..2024-06-30 | K = 1 | src/bybit_edge/research/zone_x/{common,ik04_moments,run_zone_x_1}.py (sha256 ik04_moments 8802b7e8...) | S1 | ausstehend | ausstehend (wie Nr. 1) |
