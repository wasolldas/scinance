# SCINANCE 3.0 - VERFASSUNG UND ORCHESTRIERUNGS-PROTOKOLL

> **Mission:** Ein Falsifikations-Programm, das AUSSCHLIESSLICH dort sucht,
> wo die 11-15-bp-Friktionswand irrelevant wird - Risikopraemien (Klasse P),
> Tages- bis Wochen-Horizont mit breitem Universum (Klasse W), kalendarisch
> exogene Ereignisse (Klasse E) - und das VORHER misst, ob eine Klasse
> ueberhaupt testbar ist. Massgebliche Dokumente: `PRD_SCINANCE3.md`
> (Verfassungstext, Welle 1, Kandidaten), `state/decisions.md` (DEC-51+),
> `state/hypothesis_registry.md` (H-27+), `state/gate_log.md` (GL-032+).
> Die 2.0-Akte (`../scinance2-impl/`) ist append-only abgeschlossen und
> wird nur zitiert, nie geaendert.

## AUTONOMIE-PROTOKOLL (unveraendert aus 2.0)
1. Das PRD ist die Verfassung; Registry-Disziplin (Pre-Registration,
   append-only, kein Torpfosten-Verschieben in KEINE Richtung) gilt fuer
   jeden Lauf. Kein Lauf ohne registrierten Eintrag; Urteil nur gegen das
   registrierte Gate; Gate-Auditor hat Veto.
2. Bestehende Repo-Konventionen schlagen Praeferenz; bei Stille entscheidet
   der Orchestrator fuer die reversibelste Option und protokolliert DEC-xx.
3. **Niemals den Nutzer fragen**, ausser: fehlende Zugriffsrechte/Secrets,
   Aktionen mit Geldeinsatz, destruktive Operationen auf bestehenden Daten.
   Offene Nutzer-Entscheidungen (PRD Par. 8) werden mit dokumentiertem
   Default weiterbearbeitet, nie still entschieden.
4. **Kein Live-Order-Code.** Keine Keys, keine privaten Endpunkte, keine
   Orders. Oeffentliche Endpunkte (Bybit v5, Deribit public) frei nutzbar.

## SCHUTZGUETER (duerfen nie brechen)
- Data-Harvest-Baum `data/harvest` read-only; nie hineinschreiben, nie
  cachen. Manifest-Wahrheit ist `harvest_manifest.backup.sqlite`
  (`bar_cache.resolve_manifest_path`).
- Recorder C-36 (`src/bybit_edge/recorder/`, Scheduled Task) laeuft weiter,
  bis die Sunset-Review (PRD Par. 8.3) entschieden ist.
- Test-Suite (1.495 Tests, Baseline in `survey/BASELINE_TESTS.txt`) wird
  erweitert, nie reduziert; die vier Forensik-Tests bleiben byteidentisch;
  `_legacy_v1/` wird nicht importiert ausser von seinen eigenen Tests.
- Lokale Kopplungen (drei Scheduled Tasks, Junction, `start.bat`,
  `scinance2-impl/handoff_local/*`): Pfade nie verschieben ohne Stub.

## DIE VIER ZAHLEN, DIE 3.0 REGIEREN (hergeleitet, zitierfaehig)
| Groesse | Wert | Folge |
|---|---|---|
| Horizont-Friktions-Kurve | perfektes 1-s-Orakel 0,71 bp vs 11 bp Wand; Mindesthorizont p=0,55: 6,6 h Taker / 53 min Maker; Wochen-IC 0,05: 2,7 Tage | kein Kandidat unter Tageshorizont ausser als Kosten-/Zensus-Messung |
| Sharpe-Nachweisdauer (Lo 2002) | T_min ~ 6,2/SR^2 Jahre; SR 0,5 -> 25 Jahre | Sharpe wird berichtet, nie geurteilt; urteilstragend ist die Praemie |
| IC-Nachweisgrenze | N=5: 0,098; Rauschboden SD_null wird in WP-7 GEMESSEN (Permutation), nie unterstellt | breites Universum ist Existenzbedingung der Klasse W |
| Ein-Fenster-DROP bei Power 0,5 | verwirft 3 von 4 echten Effekten | DEC-52 (kontrolliert, nie kandidatenspezifisch) |

## VERFASSUNGSREGELN
- **Unveraendert aus 2.0:** alle Methoden-Lehren C.1-C.19 des Kompendiums
  (`survey/ERKENNTNIS_KOMPENDIUM.md` Abschnitt C) - insbesondere C.2
  (Mess-Gate != Tradability-Gate: KEINE oekonomische Groesse in einer
  PASS-Bedingung; die Wand ist Etikett), C.4 (struktureller Nulleffekt vor
  der Schwelle), C.7 (N=2 beweist nichts), C.8 (Inhaltsprobe statt
  Namensschluss), C.10 (hartes Ein-Fenster-DROP, ausser DEC-52 greift),
  C.12 (Feasibility vor dem Lauf), C.14 (loud fail), C.18 (REZENZ).
- **Beschlossen fuer 3.0:** DEC-51 Power-Konvention (alpha 0,05 einseitig in
  registrierter Richtung, Power 0,80, Cluster-Einheit, Selektions-K,
  Ueberlappung); DEC-52 kontrollierte Ein-Fenster-Regel nur bei Per-Fenster-
  Power < 0,6, gepooltes alpha 0,01, Retro-Check veroeffentlicht; DEC-53
  Ergebnis-Artefakt-Pflicht (Cluster-Serie + Bootstrap-Replikate/Seed, sonst
  KEIN VERDIKT); DEC-54 Repo-Struktur; DEC-55/56 Stress-Kanon (STRESS_REL
  als Abdeckungs-Nachweis, STRESS_ABS fuer Liquiditaetsfragen); DEC-57
  GPU-Default 0.
- **Zwoelf Pflichtzeilen jeder Registrierung** (PRD Par. 3.3): Power,
  Entscheidungsrelevanz (mit oekonomischer Mindestmagnitude als ETIKETT),
  Cluster-Einheit, Selektions-Deflation, adversariales Fixture,
  Kostenmodell-Bindung (`constants_hash`, ungemessene Konstanten RAISEN),
  Irreversibilitaets-Probe, Positivkontroll-Vorschaltung, Kapital/Steuer/
  Venue, Stress-Episode, Ergebnis-Artefakte (DEC-53), Test-Pflichten T0-T7.
- **Sequenz-Zwang:** Zensus (WP-7/9/10, V-1..V-5) VOR jedem Alpha-Slot;
  Regelaenderungen VOR dem ersten Kandidaten, der sie braucht; keine
  Registrierung durch einen Agenten - nur der Orchestrator registriert.

## ZUSTANDSMASCHINE
```
ZENSUS(WP-7,WP-9,WP-10,V-1..V-5) -> FEASIBILITY-BEFUND (binaer, Konsequenz vorab)
  -> REGISTRIERUNG (Orchestrator, nach Opus-Herleitung + Opus-Review)
  -> [BUILD -> VERIFY(T0-T7)]* -> POSITIVKONTROLLE (allein, zuerst)
  -> LAUF (Nutzer-PC, T3-Runner) -> GATE_CHECK (nur gegen registriertes Gate)
  -> GL-Eintrag -> Portfolio-Sicht (Konstante aus WP-10) -> naechste Welle
```

## MODELL- UND TEAMPOLITIK (Token-Effizienz, bindend)
| Rolle | Modell |
|---|---|
| Orchestrator (Entscheidungen, Registrierung, Gate-Urteile, Verfassung) | **Fable 5.1, immer** |
| Bau von Zensus/Backfill/Treibern nach Spezifikation | Sonnet |
| Gate-Design, Rauschboden-/Power-Herleitungen, PRD-Text | Opus + zweiter Opus als adversarischer Reviewer |
| Kartierung, Inventur, Dokumentpflege, Listen | Sonnet (Haiku fuer reine Listen) |
| Fable 5.1 als Subagent | nur bei Widerspruch zwischen Herleitung und Review, den der Orchestrator nicht selbst entscheiden kann |
Regeln: Subagenten schreiben Volltexte in Dateien, an den Orchestrator gehen
Kurzfassungen (<= 10 Zeilen); jede Abnahme (Tests, Fingerprints, Diff-
Grenzen) vollzieht der Orchestrator selbst nach, nie auf Zuruf.

## TESTPYRAMIDE
T0 Unit / T1 DEC-39-Trio (positiv, null, adversarial) / T2 Determinismus
N>=3 mit Fingerprint / T3 Checkpoint-Round-Trip / T4 Gate-Arithmetik auf
konserviertem Payload / T5 Konstanten-Pin / T6 Legacy-Import-Sperre / T7
Artefakt-Round-Trip (DEC-53). Sandbox: T0-T2 + Fixture-Laeufe; Nutzer-PC:
alle Netz-Backfills (Egress-Proxy blockt Boersen-APIs in der Sandbox) und
alle Laeufe > Minuten, als Ein-Befehl-PowerShell-Runner (5.1, ASCII), die
nie mit offenem Prompt abbrechen und rc != 0 bei Vorbedingungs-Fehlern geben.

## ARBEITSREGELN
1. Kontext-Hygiene: Dateipfade statt Volltexte.
2. Git: kleine Commits je Schritt, Branch `claude/subagent-prd-development-T16fE`
   (bis der Nutzer anders entscheidet), nie force-push, nie History-Rewrite.
3. Sprache: Doku Deutsch (ASCII-safe), Code/Kommentare Englisch.
4. Jede Zahl im Programm hat eine Herleitung oder eine Quelle; Sekundaer-
   belege tragen [sek], Fehlendes heisst UNBELEGT und blockiert die
   abhaengige Konstante (RAISE), nie ein Default.
