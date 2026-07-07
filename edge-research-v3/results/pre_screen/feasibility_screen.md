# PRE-SCREEN — Feasibility-Check aller 20 IC-Vorschläge (`data-feasibility-scout`)

**Stand:** 2026-07-07. Geprüft: alle 20 IC-Vorschläge aus `results/discipline_scan/*.md` gegen
(1) reale Datenbindung (`results/audit_inventory.md`, selbst nicht live verifiziert), (2)
GL-012-Erreichbarkeit (H-07-Lehre: max\|z\|=√(N−1)=2.0 bei N=5 lag strukturell — unabhängig von T —
unter der Schwelle 2.5), (3) Reifegrad. Kein Datenlauf, kein Manifest-Zugriff möglich (siehe Audit §0).

**Methodische Leitlinie für den GL-012-Check in dieser Runde:** Ich unterscheide scharf zwei Arten von
Nicht-Erreichbarkeit, weil sie unterschiedliche Konsequenzen haben:
- **Strukturell (→ STRUKTURELLER DROP):** die limitierende Größe ist eine fixe, nicht wachsende
  Struktur-Konstante (z. B. Symbolzahl N=5) — mehr Kalenderzeit ändert daran nichts, exakt das H-07-Muster.
- **Data-gated (→ WEITERLEITEN, Reifegrad data-gated):** die limitierende Größe ist T (Kalendertage,
  Ereigniszahl, Backfill-Fortschritt) — wächst mit der Zeit/dem laufenden Deep-Backfill und ist daher
  PRINZIPIELL erreichbar, nur jetzt noch nicht.
Ergebnis vorweg: Keiner der 20 Vorschläge reproduziert das strukturelle H-07-Muster 1:1 — mehrere
Disziplin-Agenten haben die N=5-Falle bereits selbst erkannt und ihre Metrik-Wahl entsprechend
degenerationsresistent geschnitten (s. IC-NET-1, IC-RMT-1/3). Der GL-012-artige Perzentil-Fall
(IC-CLIM-2) wird unten explizit vorgerechnet, ist aber T- statt N-gebunden und daher data-gated, nicht
strukturell.

---

## Kopftabelle

| IC | Datenbindung real | GL-012-Check | Reifegrad | Empfehlung |
|---|---|---|---|---|
| IC-RMT-1 | JA (Basis-Bestand, OI-Caveat) | BESTANDEN | sofort testbar (Auflage: T/N neu ziehen falls OI-gekappt) | WEITERLEITEN |
| IC-RMT-2 | JA (Basis-Bestand) | BESTANDEN | sofort testbar | WEITERLEITEN |
| IC-RMT-3 | JA (Basis-Bestand, Binance-Liq.) | BESTANDEN | sofort testbar (Tagesfallback als Sicherheitsnetz) | WEITERLEITEN |
| IC-RMT-4 | JA, aber nur Live-only ~3 Wochen, N unverifiziert | BESTANDEN | data-gated (Mehrregime; N-Verifikation am Feed) | WEITERLEITEN |
| IC-EVT-1 | JA (Returns) / unklar (Disjunktheit Options-Snapshots) | BESTANDEN (Returns-Seite) | data-gated (≥2 disjunkte Snapshot-Tage unverifiziert) | WEITERLEITEN |
| IC-EVT-2 | JA (Stream existiert), ~3 Wochen | BESTANDEN i.d.Sache, aktuell zu wenig Ereignisse | data-gated (≥30 Kaskaden, Aug.–Okt. 2026) | WEITERLEITEN |
| IC-EVT-3 | JA nominell, Backfill-Tiefe unverifiziert | nicht hart entscheidbar (kein Manifest) | data-gated (Manifest-Coverage-Check nötig) | WEITERLEITEN |
| IC-NET-1 | JA (Struktur) / knapp (Stress-GT ~3 Wochen) | BESTANDEN (N=5-Falle bereits umgangen) | data-gated (Stress-Validierung) | WEITERLEITEN |
| IC-NET-2 | JA (Basis-Bestand + Funding-GT) | BESTANDEN (N≈13 nicht degeneriert) | sofort testbar | WEITERLEITEN |
| IC-NET-3 | JA, OI-Layer koppelt Fenster auf ~30 Tage | BESTANDEN | sofort testbar (im OI-gedeckelten Fenster) | WEITERLEITEN |
| IC-MECH-1 | JA (Stream existiert), ~3 Wochen | BESTANDEN i.d.Sache | data-gated (Ereignisdichte, Aug.–Okt. 2026) | WEITERLEITEN |
| IC-MECH-2 | JA (Basis-Bestand) | BESTANDEN | sofort testbar | WEITERLEITEN |
| IC-MECH-3 | **NEIN** (adlAlert ungeklärt/mgl. defekt) | nicht sinnvoll rechenbar | data-gated/blockiert | WEITERLEITEN |
| IC-MECH-4 | JA, aber an neue Listings gekoppelt | BESTANDEN i.d.Sache | data-gated (analog C-20) | WEITERLEITEN |
| IC-CLIM-1 | JA (Basis-Fenster) / NEIN (2. OOS-Fenster existiert noch nicht) | GESCHEITERT jetzt, prinzipiell erreichbar (T-gebunden) | data-gated (2.–3. Jahr Deep-Backfill) | WEITERLEITEN |
| IC-CLIM-2 | JA (Basis-Bestand) | GESCHEITERT jetzt (~1–5 Ereignisse/Symbol bei N=100 Tagen), T-gebunden nicht N-gebunden | data-gated (mehr T bzw. Perzentil senken) | WEITERLEITEN |
| IC-CLIM-3 | JA (=IC-CLIM-1) | GESCHEITERT jetzt, T-gebunden, SRS hat eingebauten Konservativismus | data-gated (=IC-CLIM-1) | WEITERLEITEN |
| IC-DEND-1 | JA (34 Serien, Basis-Bestand) | BESTANDEN (34 ≫ 5, keine N-Degeneration) | sofort testbar (Basisversion); Multi-Regime-Robustheit data-gated | WEITERLEITEN |
| IC-DEND-2 | JA (Basis-Bestand) | BESTANDEN | sofort testbar | WEITERLEITEN |
| IC-DEND-3 | JA (=IC-DEND-1-Serien) | BESTANDEN | sofort testbar | WEITERLEITEN |

**Ergebnis:** 0/20 STRUKTURELLER DROP, 9/20 sofort testbar, 11/20 data-gated (alle als WEITERLEITEN an
`critic`, keiner geht direkt ins PARK-Register über den Selbstkill-Mechanismus — der `critic`/
`friction-tradability-auditor` können data-gated ICs unabhängig davon aus anderen Gründen droppen).

---

### Feasibility-Check IC-RMT-1
Datenbindung real: JA — Bybit `publicTrade`/`rest.fundingRate`/`rest.openInterest`, Binance
`liquidationSnapshot`, alle Basis-Bestand 2026-03-27…heute, laut Audit SOFORT NUTZBAR (nicht live
verifiziert). Caveat: Binance-OI strukturell nur ~30 Tage Rolling-Historie — falls das Panel alle 4
Feature-Typen zeitgleich braucht, kappt die OI-Spalte das gemeinsame Fenster auf ~30 statt ~102 Tage.
GL-012-Erreichbarkeits-Check: BESTANDEN. N=20 Spalten (4 Feature-Typen × 5 Symbole). Volles Fenster:
T≈2440h → T/N≈122 (≫10er-Faustregel für MP-Asymptotik). OI-gekapptes Fenster: T≈720h (30 Tage) →
T/N=36 — immer noch klar über 10. Kein hartkodierter Schwellenwert wird gegen eine N-gebundene
Extremwertgrenze getestet (anders als H-07): Tracy-Widom-Fluktuationsstatistik + RIE ersetzen bewusst
die feste Schwelle durch eine datengetriebene Referenzverteilung — der Agent hat das GL-012-Muster
selbst methodisch umgangen.
Reifegrad: sofort testbar, Auflage: T/N-Rechnung explizit für den OI-gekappten Fall wiederholen, bevor
Pre-Registration das Fenster fixiert.
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-RMT-2
Datenbindung real: JA — Minutenbars BTC/ETH auf bybit, binance, deribit, alle drei laut Audit im
Basis-Bestand fertig.
GL-012-Erreichbarkeits-Check: BESTANDEN. N=6 (2 Symbole × 3 Börsen), T=1440 Min/Tag → T/N=240 je
rollierendem Tagesfenster. Referenzverteilung ist der MP-Bulk je Fenster, kein hartkodierter Wert gegen
eine N-gebundene Grenze.
Reifegrad: sofort testbar.
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-RMT-3
Datenbindung real: JA — Binance `liquidationSnapshot`, Basis-Bestand (bewusst nicht Bybit
`allLiquidation`, das nur ~3 Wochen Live-Historie hätte).
GL-012-Erreichbarkeits-Check: BESTANDEN. N=5, T≈2440h (stündlich) → T/N≈488; Tagesfallback T/N≈14
(vom Agenten selbst benannt, knapp aber >10). Vergleich zweier Nullmodelle (Gaussian-Wishart vs.
Lévy-stabil), kein fixer Schwellenwert gegen eine N-gebundene Extremgrenze. Einziges Risiko: viele
Nullen in Stundenbuckets (Punktereignis-Sparsity) — das ist ein Power-, kein Erreichbarkeitsproblem.
Reifegrad: sofort testbar, mit Tagesaggregation als Fallback falls Stundenbuckets zu dünn.
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-RMT-4
Datenbindung real: JA, aber ausschließlich Live-only-Fenster (Deribit `markprice.options`,
forward-only seit ~2026-06-16, ~3 Wochen) — kein Backfill davor möglich. N (aktive Strikes) laut Autor
selbst ungeprüft (Schätzung 40–150).
GL-012-Erreichbarkeits-Check: BESTANDEN — kein hartkodierter, N-gebundener Schwellenwert; selbst im
pessimistischen Fall (N=150, T≈30.000 Minutenticks) T/N≈200. Das eigentliche Problem ist nicht die
Erreichbarkeit der Schwelle, sondern die Anzahl der abgedeckten Marktregime (nur 1 in 3 Wochen).
Reifegrad: data-gated. Einzelregime-Snapshot wäre isoliert sofort testbar, aber die N-Schätzung ist
unverifiziert UND das Fenster deckt nachweislich nur ein Regime ab — in Summe data-gated bis (a) N am
realen Feed verifiziert und (b) Live-Fenster auf ≥3 Monate gewachsen ist (Entsperr-Bedingung des Autors).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-EVT-1
Datenbindung real: JA für die statistische Seite (Basis-Bestand-Returns BTC/ETH, ~102 Tage, mehrere
hundert Exzedenzen für hohe Perzentil-Schwellen laut Autor erreichbar). Nur bedingt JA für die
risikoneutrale Seite — Deribit `markprice.options` Live-only, ~3 Wochen; ob darin ≥2 vol-regime-
disjunkte Snapshot-Tage liegen, ist ohne Feed-/Manifest-Zugriff NICHT verifizierbar.
GL-012-Erreichbarkeits-Check: BESTANDEN für die Returns-Seite (POT-Exzedenzen skalieren mit T, kein
fixer N-Deckel). Für die Vergleichsseite nicht abschließend entscheidbar — das vom Autor selbst
gesetzte Selbstkill-Kriterium (<2 disjunkte Punkte) kann in dieser Sandbox nicht geprüft werden.
Reifegrad: data-gated (Entsperr-Bedingung: reale Prüfung am Feed, dass ≥2 vol-regime-disjunkte
Snapshot-Tage im Live-Fenster liegen — sonst greift der Selbstkill des Autors).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-EVT-2
Datenbindung real: JA (Stream existiert: Bybit `allLiquidation`/`insurance`), aber nur ~3 Wochen
Live-Historie.
GL-012-Erreichbarkeits-Check: BESTANDEN in der Sache — Extremal-Index ist eine Cluster-Dichte-Schätzung,
die mit mehr Ereignis-Zeit wächst, kein N-fixierter Deckel. Aktuell aber weit unter der für einen
stabilen Cluster-Schätzer nötigen Ereigniszahl (Autor-Analogie zu C-27/28/29: ≥30 Ereignisse nötig, ~3
Wochen liefern nach grober Schätzung deutlich weniger).
Reifegrad: data-gated (Entsperr-Bedingung: ≥30 Kaskaden-Ereignisse, laut PROGRAM_FINAL_REPORT §8
analog erwartet Aug.–Okt. 2026).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-EVT-3
Datenbindung real: JA nominell (BitMEX ab 2014-11-22, Deribit ab 2019-03-30, Tardis seit 2019), aber
alle drei Streams laut Audit DEEP-BACKFILL-IM-AUFBAU — kein Manifest-Zugriff, `done_days` unbekannt.
GL-012-Erreichbarkeits-Check: nicht hart entscheidbar (T unbekannt, Backfill-Fortschritt nicht
einsehbar). In der Sache BESTANDEN-artig (Multi-Zyklen-Frage skaliert mit T/Backfill-Fortschritt, kein
N-Deckel), aber Datenverfügbarkeit unverifiziert.
Reifegrad: data-gated (Entsperr-Bedingung: Manifest-Coverage-Check bestätigt `done_days` für
BitMEX/Deribit/Tardis tatsächlich zurück bis mind. 2019, idealerweise 2014).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-NET-1
Datenbindung real: JA für Struktur-Konstruktion (Bybit `publicTrade`, Basis-Bestand, alle 5 Symbole,
laut DATASET.md §5 lückenlos). Nur knapp JA für die Stress-Ground-Truth (`allLiquidation`/`insurance`
nur ~3 Wochen Live).
GL-012-Erreichbarkeits-Check: BESTANDEN — und dies ist der zentrale zu prüfende N=5-Fall: der Autor hat
MST-Hub-Zentralität (kollabiert bei N=5 fast zur Paar-Aussage, H-04-Risiko) und Louvain-Community-
Detection (bei N=5 nur eine Handvoll möglicher Partitionen, keine belastbare Bootstrap-Nullverteilung)
selbst als degeneriert erkannt und explizit NICHT als eigenen IC vorgeschlagen — übrig bleiben nur
Aggregatmetriken (Edge-Turnover-Rate, algebraische Konnektivität λ₂(L)), die nicht von der N=5-
Kombinatorik einzelner Knoten abhängen. Geprüft: kein fixer Schwellenwert wird hier gegen eine
N-gebundene Extremgrenze getestet — die N=5-Falle wurde bereits sachgerecht umgangen, kein H-07-Analogon.
Reifegrad: Struktur-Konstruktion sofort testbar; die eigentliche Kernfrage ("steigt Rekonfigurationsrate
VOR Stress-Episoden") braucht aber die Stress-Ground-Truth, die nur ~3 Wochen Historie hat — dafür
data-gated (Entsperr-Bedingung: ausreichend akkumulierte Stress-Events aus dem wachsenden Live-Fenster).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-NET-2
Datenbindung real: JA — `publicTrade` Bybit/Binance/Deribit (+optional BitMEX) im Basis-Bestand;
Funding-Dispersion als bevorzugte Ground-Truth ist ebenfalls Basis-Bestand-lang verfügbar.
GL-012-Erreichbarkeits-Check: BESTANDEN. N≈12-13 ist NICHT degeneriert (2^(N-1)-Partitionsraum real
informativ, im Unterschied zu N=5 in IC-NET-1) — Community-Detection/Zentralitäts-Kontraste sind hier
statistisch sinnvoll auswertbar.
Reifegrad: sofort testbar (bevorzugte Ground-Truth = Funding-Dispersion, Basis-Bestand-lang, umgeht das
kurze Liquidations-Fenster). Offener Punkt: BitMEX-Symbol-Mapping (XBTUSD vs. BTCUSDT) vor
Pre-Registration klären.
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-NET-3
Datenbindung real: JA, aber der OI-Layer ist strukturell auf ~30 Tage Rolling-Historie begrenzt
(Binance-OI-Caveat, evtl. auch Bybit) — koppelt das gemeinsame Multiplex-Fenster auf ~30 statt ~102 Tage.
GL-012-Erreichbarkeits-Check: BESTANDEN. N bis 15 (5×Preis, 5×Funding, 5×OI); selbst im 30-Tage-Fenster
(Minutenraster, ~43.200 Minuten) T/N≈2880 — weit über der 10er-Regel. Kein fixer Schwellenwert gegen
eine N-gebundene Grenze.
Reifegrad: sofort testbar, im OI-gedeckelten 30-Tage-Fenster. Auflage: Bybit-OI-Historientiefe separat
verifizieren (Audit-Caveat bezieht sich primär auf Binance) und Permutationsanzahl für die FDR-Familie
gegen Rechenzeit abschätzen, bevor die Familie fixiert wird.
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-MECH-1
Datenbindung real: JA (Stream `insurance` existiert), aber nur ~3 Wochen Live-Historie.
GL-012-Erreichbarkeits-Check: BESTANDEN in der Sache (Ereignisdichte der Drawdown-Annäherungen wächst
mit Kalenderzeit, kein N-Deckel), aktuell aber weit unter jeder belastbaren Reife-Schwelle.
Reifegrad: data-gated (Entsperr-Bedingung analog C-27/28/29: ausreichende Ereignisdichte, erwartet
Aug.–Okt. 2026).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-MECH-2
Datenbindung real: JA — Bybit `publicTrade`, Basis-Bestand, alle 5 Symbole, laut Audit SOFORT NUTZBAR.
GL-012-Erreichbarkeits-Check: BESTANDEN — Bunching-Test braucht eine große Stichprobe von
Trade-Notionals um bekannte, öffentlich dokumentierte Tier-Kanten; Beobachtungseinheit ist der einzelne
Trade, keine N-Symbol-Degenerationsfrage. Stichprobe im Basis-Bestand-Fenster reichlich groß.
Reifegrad: sofort testbar — einziger IC von `mechanism-design` ohne Abhängigkeit von den kurzen
Live-Streams. Auflage: aktuelle Tier-Kanten zeitpunktgenau nachschlagen (Margin Parameters werden
periodisch angepasst).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-MECH-3
Datenbindung real: NEIN für den Kern der Hypothese. `adlAlert` ist laut Audit/PROGRAM_FINAL_REPORT §7
als "UNGEKLÄRT/möglicherweise defekt" markierte offene Reparatur-WP — die Gegenpartei-
Zwangsschließungs-Seite des Vergleichs ist damit nicht nachweislich messbar. `allLiquidation`
(Orderbuch-Seite) existiert zwar (~3 Wochen Live), aber die Vergleichsseite fehlt strukturell.
GL-012-Erreichbarkeits-Check: nicht sinnvoll rechenbar — eine Schwelle auf einem Datenstrom
vorzuregistrieren, dessen Existenz/Funktionsfähigkeit selbst ungeklärt ist, ist verfrüht.
Reifegrad: data-gated/blockiert (Autor-eigene Einstufung bestätigt) — das Kern-Signal hängt an einem
noch-nicht-verifiziert-nutzbaren Datenfenster, damit NICHT sofort testbar (siehe Aufgabenstellung:
"Kern-Signal an einem noch-nicht-verfügbaren Fenster" ⇒ data-gated).
Empfehlung an critic: WEITERLEITEN (data-gated, mit Vorrang-Hinweis an Orchestrator: adl_alerts-Topic-
Reparatur-WP zuerst klären, sonst bleibt der IC dauerhaft blockiert — Entsperr-Bedingung: Reparatur-WP
abgeschlossen UND Ereignisdichte analog C-27/28/29, Aug.–Okt. 2026).

### Feasibility-Check IC-MECH-4
Datenbindung real: JA (Insurance-Stream + neue Perp-Listings existieren strukturell), aber abhängig von
neuen Bybit-Listings (Wochen-Monate-Vorlauf, analog C-20).
GL-012-Erreichbarkeits-Check: BESTANDEN in der Sache — reine Kalenderzeit-/Ereignis-Abhängigkeit
(neue Listings), kein N-Deckel.
Reifegrad: data-gated (Entsperr-Bedingung identisch mit C-20: neue Listings + Wochen-Monate-Reife).
Autor hat diesen IC selbst bereits als PARK/niedrige Priorität eingereicht.
Empfehlung an critic: WEITERLEITEN (data-gated, niedrige Priorität — de facto PARK-Kandidat, aber kein
struktureller GL-012-Fall, daher kein automatischer Selbstkill durch mich).

### Feasibility-Check IC-CLIM-1
Datenbindung real: JA für das Basis-Fenster (~100–102 Tage BTC/ETH). NEIN für das zweite,
vorregistrierte Out-of-Sample-Fenster — das existiert nur als Zusage ("sobald Deep-Backfill verfügbar"),
nicht real.
GL-012-Erreichbarkeits-Check: GESCHEITERT bei aktuellen Daten. Die vorregistrierte Schwelle verlangt
"CRPS_AnEn < CRPS_HAR-RV auf ≥2 disjunkten Fenstern" — real vorhanden ist derzeit nur 1 Fenster
(Basis-Bestand). WICHTIGER UNTERSCHIED zu H-07: die Fenster-Anzahl ist eine Funktion von T
(Kalenderzeit/Backfill-Fortschritt), nicht einer strukturell fixen Größe wie der Symbolzahl N — mit
fortschreitendem Deep-Backfill wird ein zweites Fenster real verfügbar. Die Schwelle ist also
PRINZIPIELL erreichbar, nur jetzt noch nicht — kein struktureller Deckel.
Reifegrad: data-gated (Entsperr-Bedingung: Manifest-Coverage-Check zeigt `done_days` für BTC/ETH
deutlich über die aktuelle ~100-Tage-Basis hinaus, Ziel ≥2–3 Jahre für mehrere Vol-Regime).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-CLIM-2
Datenbindung real: JA — Basis-Bestand, alle 5 Symbole, `rest.fundingRate`/`rest.openInterest`/
`publicTrade`.
GL-012-Erreichbarkeits-Check: GESCHEITERT bei aktuellem T≈100 Tagen — Rechnung explizit nachvollzogen,
analog zum sqrt(N-1)-Schema: erwartete Trigger-Ereigniszahl ≈ N_Tage × (1−p). Bei p=0.99 (99.
Perzentil): 100 × 0.01 = **1 Ereignis** je Symbol. Bei p=0.95: 100 × 0.05 = **5 Ereignisse**. Für eine
FDR-korrigierte Aussage über 5×4=20 Symbolpaare (Benjamini-Hochberg α=0.10) ist eine Ereigniszahl von
1–5 je Paar strukturell zu klein für belastbare Power — die Schwelle muss vor Pre-Registration auf
Erreichbarkeit geprüft werden, nicht erst nach dem Testlauf, exakt die GL-012-Lehre. **Entscheidender
Unterschied zu H-07**: die limitierende Größe ist hier T (Kalendertage), nicht N (Symbolzahl) — T wächst
mit fortschreitendem Deep-Backfill (BTC/ETH/BNB sind laut Audit die ältesten der 5 Serien), wodurch die
Ereigniszahl bei GLEICHBLEIBENDEM Perzentil linear mit T steigt: bei T=1000 Tagen läge die 99.-Perzentil-
Ereigniszahl bei ~10, die 95.-Perzentil-Zahl bei ~50 — beides in einer für Permutationstests brauchbaren
Größenordnung. Die Schwelle ist also PRINZIPIELL erreichbar, nur mit der aktuellen ~100-Tage-Basis nicht.
Reifegrad: data-gated (Entsperr-Bedingung: Deep-Backfill-Coverage für mind. BTC/ETH/BNB liefert genug
Historie für ≥30 Trigger-Ereignisse pro Symbolpaar — Analogie-Richtwert aus PROGRAM_FINAL_REPORT §8).
Als Sofort-Abschwächung denkbar, aber NICHT ohne Vorab-Fixierung: Perzentil-Schwelle auf 90. absenken
(≈10 Ereignisse/Symbol) — bleibt auch dann dünn für 20 FDR-Paare, daher weiterhin als data-gated statt
sofort testbar eingestuft.
Empfehlung an critic: WEITERLEITEN — ausdrücklich KEIN struktureller Drop, weil die Ereigniszahl mit
wachsendem T skaliert (nicht mit einer fixen Symbolzahl wie bei H-07); wäre die 99./95.-Perzentil-Wahl
jedoch an N=5 SYMBOLE statt an T Tage gekoppelt gewesen, läge hier tatsächlich ein H-07-Analogon vor —
das ist nicht der Fall.

### Feasibility-Check IC-CLIM-3
Datenbindung real: JA — identisch zu IC-CLIM-1 (baut direkt auf dessen Analog-Ensembles auf, kein
eigener neuer Datenstrom).
GL-012-Erreichbarkeits-Check: GESCHEITERT bei aktuellem N (~100 Analog-Läufe) für eine robuste
Spread-Reliability-Slope-Bootstrap-Sampling-Rausch-Korrektur — Literatur verlangt laut Autor "deutlich
mehr als 100 Fälle". Wie bei IC-CLIM-1/CLIM-2 ist dies eine T-, nicht N-Symbol-gebundene Grenze
(dieselbe Deep-Backfill-Abhängigkeit). Zusätzlicher Pluspunkt: SRS ist per Konstruktion so gebaut, dass
sie bei zu kleinem N ehrlich "nicht reliable" statt falsch-positiv "reliable" meldet — ein eingebauter
Selbstschutz gegen genau das GL-012-Risiko einer Scheinsignifikanz bei kleinem N.
Reifegrad: data-gated (identische Entsperr-Bedingung wie IC-CLIM-1). Autor selbst schlägt vor, IC-CLIM-3
bei zu kleinem N explizit als PARK statt WEITER zu kennzeichnen — dem schließe ich mich als Empfehlung an
`critic` an, aber es ist kein automatischer Selbstkill-Fall (kein struktureller N-Deckel).
Empfehlung an critic: WEITERLEITEN (mit ausdrücklicher Empfehlung, bei Fortbestehen des kleinen N eher
PARK als WEITER zu verdikten — Entscheidung bleibt beim critic, nicht bei mir).

### Feasibility-Check IC-DEND-1
Datenbindung real: JA — bis zu 34 Symbol×Stream-Serien im Basis-Bestand (~103 Tage), Kernpointe des
ICs: die Serien-BREITE (34 Streams) trägt die Statistik, nicht die Serien-TIEFE (Jahre) — daher sofort
verfügbar ohne Deep-Backfill.
GL-012-Erreichbarkeits-Check: BESTANDEN für die Basis-Version. Erwartete Pointer-Tag-Rate 5–15% von
~103 Tagen ⇒ ~5–15 Pointer-Tage — klein, aber die für die 60%-Schwelle relevante Größe ist die
Serienzahl (34), nicht die Anzahl der Pointer-Tage; 34 ist komfortabel groß für einen
Prozentsatz-Schwellenwert, ANDERS als N=5 bei H-07. Kein struktureller N-Deckel.
Reifegrad: sofort testbar für die Basis-Version (Kernpointe des Autors: Breite statt Tiefe). Die
robuste/finale Multi-Regime-Kalibrierung der 60%-Schwelle über mehrere Markt-Regime (Bull/Bear/Crash)
ist data-gated (Entsperr-Bedingung: Manifest-Coverage-Check bestätigt `done_days` für BTC/ETH/BitMEX
zurück bis mind. 2019).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-DEND-2
Datenbindung real: JA — Basis-Bestand BTC/ETH auf Bybit/Binance/Deribit, Trades-Serien.
GL-012-Erreichbarkeits-Check: BESTANDEN — kein Alpha-Claim, reine Ausrichtungsprüfung. Schwellenwert
(Segment-Korrelation <0.5 in ≥2 aufeinanderfolgenden Segmenten) aus COFECHA-Praxis übernommen; bei
20-Tage-Segmenten/10-Tage-Overlap über ~103 Tage ergeben sich ≈8–9 Segmente — ausreichend oft prüfbar.
Reifegrad: sofort testbar. Sollte laut Autor priorisiert vor der Multi-Zyklen-Version von IC-DEND-1
laufen (Voraussetzungs-Check für jede tagesgenaue Cross-Exchange-Verrechnung).
Empfehlung an critic: WEITERLEITEN.

### Feasibility-Check IC-DEND-3
Datenbindung real: JA — nutzt dieselben bis zu 34 Serien aus IC-DEND-1, Basis-Bestand.
GL-012-Erreichbarkeits-Check: BESTANDEN — kein Alpha-Claim, reine Kennzahl (EPS-Wert je Kandidaten-N),
keine hartkodierte Schwelle gegen eine N-gebundene Grenze.
Reifegrad: sofort testbar.
Empfehlung an critic: WEITERLEITEN.

---

## Gesamtfazit für Orchestrator/critic

Von 20 IC-Vorschlägen bestehen **alle 20** den GL-012-Erreichbarkeits-Check im strengen Sinn (keiner
reproduziert das strukturelle H-07-Muster einer fixen, nicht wachsenden N-Grenze unter einer
pre-registrierten Schwelle) — **0 STRUKTURELLE DROPS, damit auch 0 automatische Einträge ins
PARK-Register über den Selbstkill-Mechanismus dieses Agenten.** Das ist kein Freibrief: mehrere
Disziplin-Agenten (`network-topology` für IC-NET-1, `econophysics-rmt` für IC-RMT-1/3) haben die N=5-
Falle bereits selbst durch bewusste Metrik-Wahl umgangen (Aggregatmetriken statt Hub-Zentralität/
Community-Detection bei N=5) — das wurde hier verifiziert, nicht nur übernommen.

9 ICs sind **sofort testbar** (IC-RMT-1/2/3, IC-NET-2/3, IC-MECH-2, IC-DEND-1/2/3), 11 sind
**data-gated** mit je konkreter Entsperr-Bedingung. Einzige Datenbindung, die ich als **NEIN** (nicht
real) einstufe, ist der `adlAlert`-Kern von IC-MECH-3 (ungeklärter/möglicherweise defekter Stream). Der
GL-012-artige Perzentil-Fall IC-CLIM-2 (99. Perzentil bei N≈100 Tagen ⇒ nur ~1 Ereignis) wurde explizit
vorgerechnet und als T- statt N-gebunden eingeordnet — data-gated, kein struktureller Drop, aber knapp
und mit expliziter Vorab-Fixierungspflicht für Perzentil/Schwelle.
