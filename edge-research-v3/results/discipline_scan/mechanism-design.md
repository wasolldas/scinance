# DISCIPLINE-SCAN — mechanism-design (Auktions-/Spieltheorie, ADL/Insurance-Fund/Marktdesign)

**Stand:** 2026-07-07. Datenlage laut `results/audit_inventory.md` — **nicht live verifiziert** (kein
Manifest-Zugriff in dieser Sandbox), alle Reifegrad-Angaben sind Dokumenten-Übernahme aus `reference/DATASET.md`.

## Schritt 1 — Methodenrecherche (Pflicht)

Recherchierte, mit Quelle belegte Bybit-Mechaniken (WebSearch, 2026-07-07):

1. **ADL-Ranking** — Bybit rankt Gegenpartei-Positionen nach *leveraged return* (Effektiv-Leverage ×
   PnL%); "Light"-Indikator in 5 Stufen (je 20% Perzentil der Ranking-Queue). Exakte interne Formel
   proprietär, aber Rangordnungsprinzip dokumentiert. [Bybit Help "Auto-Deleveraging (ADL) Mechanism";
   learn.bybit.com "What Is Auto-Deleveraging (ADL)?"]
2. **ADL-Trigger als harter Schwellenwert** — 8h-PnL-Drawdown-Ratio eines Trading-Pairs relativ zum
   8h-Hoch der Insurance-Fund-Balance; Trigger bei ≥30%, Stopp bei ≤25%. Seit 19.12.2025 zusätzlich
   Dual-Pool-Struktur (New-Listing-Pool, Portfolio-Pool bis 9 korrelierte Kontrakte), gleicher
   30%/8h-Schwellenwert für beide Pools. [Bybit "Insurance Fund"; Ankündigung "enhanced insurance fund
   mechanism", Dez. 2025]
3. **Liquidation-Engine als IOC-Orderbuch-Exekution** — Liquidation läuft NICHT direkt gegen eine
   Gegenpartei, sondern als IOC-Order gegen das offene Orderbuch bis zur Bankrott-Preis-Grenze
   (Mark-Price-Trigger, Dual-Price-Mechanismus gegen LTP-Manipulation). Überschuss ggü. Bankrott-Preis
   → Insurance Fund; Fehlbetrag → Insurance Fund zahlt, sonst ADL. [Bybit "FAQ — Order Execution and
   Liquidation"; "Liquidation Process (USDC Perpetual & Futures)"; "Insurance Fund"]
4. **Gestaffelte Risk-Limit-Tiers (Margin-Kinks)** — Positionswert-Schwellen mit diskretem
   MMR-Sprung (Bsp. BTCUSDT: ≤2.000.000 USDT → 0,5% MMR; ab 2.600.000 USDT → 0,56%). Tier steigt
   automatisch mit Positionswert, nicht mit gewähltem Leverage. [Bybit "Risk Limit (Perpetual and
   Expiry Contracts)"; "Margin Parameters"]
5. **Funding-Rate-Formel** (Premium-Index + Clamp-Funktion, Impact-Bid/Ask vs. Index-Preis) —
   recherchiert, aber verworfen (s.u.).

**Erwogene, aber verworfene Kandidaten (Grund):**
- **Funding-Rate-Formel jenseits Timing** (Premium-Index-Clamp) — zu nah an C-22/CS-12 ("Funding-Uhr"),
  Abgrenzung Formel-vs-Timing zu unscharf → Selbstkill, nicht als IC eingereicht.
- **Sozialisierter Verlust/Clawback** (ältere Börsen-Norm) — Bybit nutzt dieses Modell nachweislich
  NICHT mehr (ADL hat es strukturell ersetzt); keine testbare Bybit-eigene Mechanik vorhanden.
- **Order-Matching-Priorität** — Bybit dokumentiert Standard-Price-Time-Priority ohne
  Sonderregel; kein eigenständiger spieltheoretischer Hebel gefunden, daher nicht isoliert als IC.
- **Dual-Price-Mechanismus (Mark-Price vs. LTP)** — reiner Manipulationsschutz ohne eigene
  Vorhersage über das Trigger-Verhalten hinaus; als Kontext in IC-MECH-3 integriert statt eigener IC.

---

### IC-MECH-1 — ADL-Trigger-Antizipation am dokumentierten 30%/8h-Drawdown-Kante
Fachgebiet: Mechanism Design/Spieltheorie
Kernfrage: Verändert sich Orderfluss/Spread-Verhalten VOR Erreichen der dokumentierten
Insurance-Fund-8h-Drawdown-Schwelle (≥30% vom 8h-Hoch) messbar — als spieltheoretische Antizipation
eines bekannten, regelbasierten Automatismus — unabhängig von der Kaskaden-Form NACH dem Trigger?
Erwogene Alternativen: Funding-Rate-Formel (verworfen, C-22/CS-12-Nähe); Clawback-Modell (verworfen,
bei Bybit nicht implementiert); Dual-Price-Mechanismus (verworfen als eigener IC, nur Kontext).
Mechanik-Quelle: Bybit "Insurance Fund" + Dez-2025-Ankündigung "enhanced insurance fund mechanism"
(30%/8h-Trigger, Stopp 25%, Dual-Pool).
Datenbindung: `insurance` (insurance.USDT je Symbol, Bybit Live seit ~2026-06-16, DATASET.md §4) —
~3 Wochen Historie zum Audit-Datum, nicht live verifiziert.
Nicht-Redundanz zu C-22/CS-12/C-27–29: C-27–29 fragen nach der statistischen FORM der Preis-Kaskade
NACH dem Liquidations-Trigger (Omori/Avalanche); hier geht es um Verhaltensänderung VOR/AN der
dokumentierten Regel-Schwelle selbst (andere Messgröße: Drawdown-Ratio-Annäherung, nicht Preis-Nachbeben).
Kein Funding-Timing-Bezug (nicht C-22/CS-12).
Friktions-Rolle: capital_free (reine Existenzfrage vor jeder Handelsregel).
Rechenaufwand: CPU.
Status: data-gated. Entsperr-Bedingung: ausreichende Ereignisdichte von Drawdown-Annäherungen,
analog zur C-27/28/29-Kaskaden-Reife-Schwelle (~7 Insurance-Events/h → ≥30 Ereignisse, erwartet
Aug.–Okt. 2026 laut PROGRAM_FINAL_REPORT §7/§8).

### IC-MECH-2 — Risk-Limit-Tier-Bunching (Margin-Kink-Vermeidung)
Fachgebiet: Mechanism Design/Verhaltensökonomik (Bunching-an-Kink, Saez-artig)
Kernfrage: Clustern Order-/Trade-Notionals sich systematisch knapp UNTERHALB der dokumentierten
Risk-Limit-Tier-Kanten (z.B. BTCUSDT 2.000.000 USDT, MMR-Sprung 0,5%→0,56%), wie es ein
Bunching-Modell an einer diskreten Margin-Strafe-Regel vorhersagt?
Erwogene Alternativen: ADL-Ranking-Formel (separat als IC-MECH-3 behandelt, hier nicht dupliziert);
Order-Matching-Priorität (verworfen, Standard-Price-Time ohne Sondermechanik).
Mechanik-Quelle: Bybit "Risk Limit (Perpetual and Expiry Contracts)" + "Margin Parameters"
(dokumentierte Tier-Kanten je Symbol).
Datenbindung: `publicTrade` (Bybit, Basis-Bestand 2026-03-27…heute, alle 5 Symbole, SOFORT NUTZBAR
laut audit_inventory.md §1.3) — Größenverteilung um die AKTUELLEN Tier-Kanten (zeitpunktgenau
nachzuschlagen, da Margin Parameters periodisch angepasst werden — PRE-SCREEN-Bedingung).
Nicht-Redundanz zu C-22/CS-12/C-27–29: Betrifft weder Funding-Timing noch Kaskaden-Form, sondern
Positionsgrößen-Clustering an einer Margin-Kante — eigenständige Messgröße.
Friktions-Rolle: capital_free (Struktur-/Verhaltensfakt, keine direkte Preis-Strategie).
Rechenaufwand: CPU.
Status: **sofort testbar** (einziger IC dieses Agenten ohne Abhängigkeit von den kurzen
Insurance-/ADL-Live-Streams).

### IC-MECH-3 — ADL-Zwangsschließung vs. Orderbuch-Liquidation: Adverse-Selection-Asymmetrie
Fachgebiet: Mechanism Design/Marktmikrostruktur-Auktionstheorie (Kyle 1985, Glosten-Milgrom)
Kernfrage: Erzeugt die dokumentierte Zwei-Klassen-Exekution — ADL schließt direkt gegen eine
Gegenpartei zum bestehenden Preis (kein Orderbuch, keine Slippage), gewöhnliche Liquidation läuft
als IOC-Order GEGEN das Orderbuch bis zur Bankrott-Preisgrenze — eine systematisch unterschiedliche,
vorhersagbare Kurswirkung je nach Liquidationstyp (informierte vs. uninformierte Zwangsliquidität)?
Erwogene Alternativen: bereits oben behandelt (IC-MECH-1/2); zusätzlich verworfen: reine
L2-Tiefe-Rekonstruktion als Standalone-Methode (Dateninfrastruktur, kein neuer spieltheoretischer Hebel).
Mechanik-Quelle: Bybit "Auto-Deleveraging (ADL) Mechanism"; "FAQ — Order Execution and Liquidation";
"Liquidation Process (USDC Perpetual & Futures)" (IOC-Exekution, Bankrott-Preis-Logik).
Datenbindung: `allLiquidation` (Bybit Live, ~3 Wochen, orderbuch-Liquidationen) UND `adlAlert`
(Gegenpartei-Zwangsschließungen) — **adlAlert laut audit_inventory.md/PROGRAM_FINAL_REPORT §7 als
"UNGEKLÄRT/möglicherweise defekt" (offene Reparatur-WP `adl_alerts-Bybit-Topic-Klärung`) markiert.**
Nicht-Redundanz zu C-22/CS-12/C-27–29: Andere Messgröße als C-27–29 (Exekutions-MECHANISMUS-Differenz
je Liquidationstyp, nicht Kaskaden-Form); kein Funding-Timing-Bezug.
Friktions-Rolle: capital_free zunächst (Existenzfrage vor jeder Handelsregel).
Rechenaufwand: CPU.
Status: **data-gated/BLOCKIERT** — Kernsignal hängt am ungeklärten `adlAlert`-Topic; ohne dessen
Reparatur nicht einmal die Existenzfrage stellbar. Entsperr-Bedingung: adl_alerts-Topic-Reparatur-WP
abgeschlossen UND Ereignisdichte analog C-27–29-Schwelle (Aug.–Okt. 2026).

### IC-MECH-4 (PARK, niedrige Priorität) — Insurance-Fund-Dual-Pool-Regimewechsel am Tag-30-Übergang
Fachgebiet: Mechanism Design/Reserve-Adäquanz (spekulativ, gemäß Agenten-Rolle nur als PARK
einzureichen)
Kernfrage: Steigt die dokumentierte Drawdown-Trigger-Häufigkeit diskret am Tag-30-Übergang eines
neuen Bybit-Listings, weil das New-Listing-Insurance-Pool-Schutznetz sich zu diesem Zeitpunkt
regelbasiert ändert (Wechsel in den Portfolio-Pool)?
Mechanik-Quelle: Bybit-Ankündigung "enhanced insurance fund mechanism" (Dez. 2025) — New-Listing-Pool
(30 Tage, Mindestgröße 8 Mio. USD) vs. Portfolio-Pool (bis 9 korrelierte Kontrakte).
Datenbindung: `insurance` + neue Bybit-Perp-Listings — strukturell dieselbe Datenabhängigkeit wie
C-20 (N=10–20 frische Symbole, Wochen-Monate-Vorlauf).
Cross-Domain-Hinweis: Überschneidet sich in der DATENABHÄNGIGKEIT (nicht der Messgröße) mit C-20
(MOMENT Zero-Shot auf Neulistings, PROGRAM_FINAL_REPORT §7) — deshalb bewusst nicht als Voll-IC,
sondern PARK, um keinen doppelten "Wecker" zu erzeugen; bei C-20-Reife ggf. gemeinsam prüfen.
Rechenaufwand: CPU.
Status: PARK. Entsperr-Bedingung: identisch mit C-20 (neue Listings, Wochen-Monate-Horizont).

---

## Zusammenfassung für Orchestrator

3 Voll-IC-Vorschläge (IC-MECH-1 bis 3) + 1 PARK-Kandidat (IC-MECH-4). Nur **IC-MECH-2** ist sofort
testbar ohne Abhängigkeit von den kurzen Live-Streams. IC-MECH-1 ist data-gated (Ereignisdichte).
IC-MECH-3 ist data-gated/BLOCKIERT durch das ungeklärte `adlAlert`-Topic — explizit an
`data-feasibility-scout` zu melden, da das der Kern-Datenabhängigkeit dieses Agenten am stärksten
im Weg steht. Keine Redundanz zu C-22/CS-12 (Funding-Timing) oder C-27–29 (Kaskaden-Form) — alle
vier Vorschläge fragen nach der Mechanik-REGEL selbst, nicht ihrer statistischen Preis-Nachwirkung.
