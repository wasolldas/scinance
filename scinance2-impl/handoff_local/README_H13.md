# H-13 · Tail-Form-Konsistenz xi_P vs. xi_Q (F-TAILSHAPE, KAPITALFREI, **DATA-GATED/GESPERRT**)

> Registrierter Eintrag: `scinance2-impl/state/hypothesis_registry.md` →
> „### H-13 · Tail-Form-Konsistenz" (Welle 4). Code komplett gebaut und gegen
> synthetische Harvester-Bäume getestet (`tests/unit/test_c13_tailshape.py`);
> **KEIN Lauf gegen echte Daten erfolgt.**

## Sperrstatus

**H-13 ist GESPERRT.** Die risikoneutrale Seite hängt am Live-Fenster
`markprice.options` (Deribit, forward-only seit ~2026-06-16). Entsperr-Bedingung
(Teil der Pre-Registration, wächst mit Kalenderzeit, Schwelle wird **NICHT**
gesenkt): am realen Feed existieren zwei Snapshot-Tage **D1 < D2** mit

1. `|log(RV_5d(D1) / RV_5d(D2))| >= log(1.5)` (vol-regime-disjunkt),
2. `>= 10` Kalendertage Abstand,
3. je Tag/Symbol `>= 12` Strikes mit `0.01 <= |Delta| <= 0.5` im 20–45-DTE-Tenor.

**Deterministische Tageswahl (kein Cherry-Picking):** D1 = frühester Tag, der
(3) erfüllt; D2 = frühester späterer Tag, der (1)+(2)+(3) gegenüber D1 erfüllt.
Die Suche läuft **programmatisch** über alle verfügbaren Snapshot-Tage
(`snapshot_selection.py`); nichts ist hartcodiert. Ohne gültiges Paar melden
CLI und Runner einen sauberen SKIP (exit 2):
*„H-13 gesperrt — keine 2 vol-regime-disjunkten Snapshot-Tage im Live-Fenster gefunden."*

Interpretation der Entsperrung (dokumentierte Festlegung): Die D1/D2-Suche
läuft **je Symbol** (BTC-RV für BTC, ETH-RV für ETH); entsperrt ist, sobald
**mindestens ein** Symbol ein gültiges Paar hat — das registrierte Gate
verlangt ohnehin nur `>= 1 Symbol in {BTC, ETH}`. Symbole ohne gültiges Paar
werden nicht gemessen (ihre Zellen fehlen in F-TAILSHAPE).
`RV_5d` = Root-Mean-Square der 1-min-Log-Returns über die 5 Kalendertage
strikt VOR dem Snapshot-Tag (Skalierung kürzt sich im Ratio).

## Start

```powershell
powershell -ExecutionPolicy Bypass -File .\run_h13.ps1     # Windows (PS 5.1)
```
```bash
bash scinance2-impl/handoff_local/run_h13.sh               # Linux/macOS
```

Ablauf: (1) `H13_UNLOCK_CHECK` (`scripts/c13_tailshape.py --check-unlock-only`,
nur D1/D2-Suche, kein Fit; rc 2 = gesperrt → SKIP), (2) nur bei rc 0:
`H13_TAILSHAPE` (voller Lauf, 500 Bootstrap-Reps je Seite, Seed 42).
Exit: 0=OK · 1=FAIL · 2=SKIP. Ergebnisse: `results/h13_<ts>/h13/…` +
`SUMMARY_<datum>.md`. Env: `HARVEST_DIR`, `HANDOFF_DRY_RUN` (+`HANDOFF_DRY_RC`).

## Methodik (vorregistriert, nicht verhandelbar)

- **xi_P (physisch):** trailing 60 Handelstage 1-min-Log-Returns (Bybit-Perp
  `publicTrade`, Tage strikt vor dem Snapshot-Tag, kein Lookahead). POT mit
  **fixem** u_P = empirisches 99,5%-Quantil der 1-min-Verluste; GPD-MLE
  (`scipy.stats.genpareto.fit`, loc=0 auf Exzessen); SE via Block-Bootstrap
  (60-min-Blöcke, 500 Reps, Schwelle je Replikat neu). Mean-Excess-Diagnostik
  wird als **nicht-urteilstragende** Sekundärinfo mitgeschrieben.
  **Hill-Gegenprobe** mit k = Anzahl Exzedenzen über u_P.
- **xi_Q (risikoneutral):** Deribit `markprice.options`-Snapshot 08:00 UTC →
  SVI-Fit (Raw-SVI, w(k)=a+b(ρ(k−m)+√((k−m)²+σ²)), Least-Squares) →
  Breeden-Litzenberger-RND (numerische zweite Ableitung der Black-76-Call-
  Preise) → **GPD-PWM** (Hosking/Wallis; robuster als MLE bei kleinen
  Stichproben) auf der RND-Exzess-Verteilung unterhalb des 5%-RND-Quantils
  (linker Tail); SE via Strike-Bootstrap (Resampling mit Zurücklegen, SVI+RND
  je Replikat neu, 500 Reps).
- **Null/p:** H0: xi_P = xi_Q je Symbol × Tag; p aus der kombinierten
  Bootstrap-Verteilung (Block- × Strike-Bootstrap, äußeres Produkt, auf die
  Null verschoben, zweiseitig, +1-Korrektur).
- **Gate (wörtlich):** WEITER, wenn für ≥ 1 Symbol an BEIDEN Tagen
  sign(Δξ) identisch UND |Δξ| ≥ 0,15 UND Bootstrap-p ≤ 0,05 nach BH-FDR
  α = 0,10 über **F-TAILSHAPE** (2 Symbole × 2 Tage) UND Hill-Gegenprobe
  widerspricht dem GPD-Vorzeichen nicht. DROP sonst — hartes
  Ein-Fenster-/Ein-Tag-Kriterium, kein Graubereich. Payload ist gate-neutral
  (`capital_free=true`, `data_gated=true`); der gate-auditor urteilt.

## Annahmen zum Options-Payload (dokumentiert, da neuer Loader)

Baum: `data/harvest/raw/deribit/markprice.options/symbol=<BTC|ETH>/date=<d>/*.parquet`
mit `ts_exchange_ms` + `payload_json` (Konvention wie Bybit-Streams). Payload
je Tick laut DATASET.md:
`{"params":{"channel":"markprice.options.btc_usd","data":[{"instrument_name":…,"mark_iv":…,"iv":…},…]}}`
(zusätzlich toleriert der Loader: direktes `params`-Objekt, direkte
`data`-Liste, einzelner Instrument-Eintrag).

1. **Instrument-Name:** Deribit-Standard `<UND>-<DDMMMYY>-<STRIKE>-<C|P>`
   (z. B. `BTC-27JUN26-70000-C`), Regex-Parse von Expiry/Strike/Typ;
   `d` als Dezimaltrenner im Strike wird unterstützt.
2. **IV-Einheit:** `mark_iv`/`iv` > 3 gilt als PROZENT und wird durch 100
   geteilt (Deribit quotiert IV in Prozent, z. B. 55.0). `mark_iv` hat
   Vorrang vor `iv`.
3. **Snapshot:** alle Ticks 08:00 UTC ± 30 min, letzter Mark je Instrument
   gewinnt; ist das Fenster leer, wird der zeitlich nächste Tick des Tages
   genommen (Fallback, im Payload sichtbar via Tageswahl-Diagnostik).
4. **Forward:** bevorzugt explizites Feld `forward_price` /
   `underlying_price` / `index_price` (Median über die Einträge des Expiry);
   sonst Put-Call-Parität in Inverse-(Coin-)Einheiten:
   `C_coin − P_coin ≈ 1 − K/F` → F = linearer Nulldurchgang der
   (K, C−P)-Paare aus `mark_price`.
5. **Delta:** explizites `delta`-Feld, falls vorhanden; sonst
   **Black-76-Approximation aus der Mark-IV mit r = 0**:
   `d1 = (ln(F/K)+0,5·σ²T)/(σ√T)`, Call-Delta = N(d1), Put-Delta = N(d1)−1.
   (Der `markprice.options`-Stream liefert i. d. R. keine Greeks — die
   Delta-Filterung 0,01 ≤ |Δ| ≤ 0,5 basiert dann vollständig auf dieser
   Approximation.)
6. **Smile-Wahl:** im 20–45-DTE-Band das Expiry mit den MEISTEN Strikes im
   Delta-Band (Gleichstand: nächstes an 30 DTE, dann frühestes) —
   deterministisch. Je Strike zählt die IV der OTM-Seite (K ≥ F: Call,
   K < F: Put; Fallback auf die andere Seite).
7. **Numerische Trunkierung:** RND-Grid über Log-Moneyness [−2,5; +1,5]
   (801 Punkte); Masse unterhalb ~8 % des Forwards wird ignoriert
   (dokumentierte Näherung, identisch für alle Zellen und Bootstrap-Reps).

## Kapitalfreiheit

Reine Mess-/Konsistenzfrage ohne Round-Trip per Definition — im gesamten
Modul existiert **keine Kosten-/Ertragsrechnung** (von den Tests erzwungen).
Eine Tail-/Skew-Handelsfolge wäre eine NEUE **H-13b**, NICHT impliziert.

## Tests (Sandbox, alles synthetisch)

`PYTHONPATH=src python3 -m pytest tests/unit/test_c13_tailshape.py -q` —
deckt ab: xi_P-Recovery an bekanntem wahren ξ, Hill-Konsistenz,
Instrument-Parser, SVI+RND-Sanity, GPD-PWM-Recovery, deterministische
D1/D2-Selektion (positiv + sauberes „nicht gefunden"), Gate-Positiv-Detektion,
Null-Kontrolle, Kapitalfreiheits-Wächter, End-to-End gegen einen synthetischen
Harvester-Baum (Unlock-Check findet D1/D2, voller Lauf rc=0).
