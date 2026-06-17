# Morning Report — 2026-06-17 (ANALYZE, Welle 2)

**Auswertung:** gate-auditor gegen `state/hypothesis_registry.md` (H-04/H-05/H-06 + WINDOW_MAX_BARS-Nachtrag DEC-12 + F-WAVE2-Nachtrag) + PRD §4/§8.
**Lauf:** `handoff_local/results/wave2_20260617_090618/` (User-T3, 5/5 OK, rc=0; zweistufige F-WAVE2-BH-FDR sauber durchgelaufen).
**Formale Gate-Urteile:** `state/gate_log.md` (GL-006/007/008, append-only).

> Hinweis: Dieser Report löst den Welle-1-Morgen-Report (2026-06-12) ab. Die Welle-1-Urteile bleiben vollständig in `gate_log.md` GL-001…GL-005 dokumentiert.

---

## 1. Management-Summary — die drei Welle-2-Urteile

| Gate | Hypothese | Urteil | Kern |
|---|---|---|---|
| **GL-006** | H-04 · C-17/C-41 Lead-Lag | **WEITER (Mess-Existenz)** | gerichtete Info BTC→ETH existiert messbar, Lead=BTC stabil über beide Fenster — **NICHT handelbar, Kapital bleibt PARK** |
| **GL-007** | H-05 · C-01 OFI-Vorzeichen | **DROP** | keine ≥2-Fenster-positive-Konsistenz; einziger robuster Effekt ist INVERS (ETH) → C-01 + C-09-OFI-Bein + C-14-OFI-Erbe fallen |
| **GL-008** | H-06 · C-07 Permutation Entropy | **DROP** | PRE-Gate ρ ≥ 0.30 in ALLEN Fenstern verfehlt (max +0.0145); zusätzlich AUC-Lift +0.0072 < +0.03 |

**F-WAVE2 Stage 2 (Über-Familie):** in keiner Hypothese wurde ein Stage-1-Survivor gekillt (H-04 12/12, H-05 3/3, H-06 2/2 — 0 verloren). Stage 2 hat **kein** Urteil verändert; die Urteile folgen aus den Registry-Kriterien jenseits der reinen FDR-Survivorschaft (Lead-Stabilität bei H-04; Vorzeichen-Konsistenz/Inversion bei H-05; PRE-Gate/AUC bei H-06).

---

## 2. H-04 — der erste nicht-triviale Nicht-DROP des Frameworks (mit Kapitalfreiheits-Caveat)

Nach fünf vorangegangenen Negativ-/PENDING-Urteilen (GL-001..GL-005: H-01/H-02/H-03 alle DROP) ist **H-04 das erste Gate, das tatsächlich besteht** — und es ist bewusst als **kapitalfreies Mess-Gate** konstruiert, sodass „bestanden" KEINE handelbare Behauptung ist.

**Was bestanden ist:** Auf BTC/ETH-Perp existiert über 2 disjunkte Fenster ein surrogat-signifikanter (p=0.0050 WCOH, FDR-sig + Stage-2-sig), reproduzierbarer gerichteter Informationsfluss mit BTCUSDT als stabilem Lead-Symbol — bestätigt auf BEIDEN registrierten Achsen (TE/C-17 und WCOH/C-41).

**Heikle Bewertung — bidirektionale Signifikanz in Fenster 0:** In F0 sind beide TE-Richtungen FDR-sig (Kopplung in beiden Richtungen). Entschieden wurde streng nach Registry-Wortlaut (Lesart B): Das Kriterium verlangt „Lead-Symbol bleibt konsistent / kippt nicht", NICHT „Rückrichtung muss insignifikant sein". BTC ist in beiden Fenstern dominant — WCOH-Lead=BTC in F0+F1, und BTC→ETH-TE hat bei jedem gematchten Lag höhere obs-Stat als ETH→BTC. Lead-Symbol = [BTC, BTC], kippt nicht. Lesart A (bidirektional=Kippen) würde einen nicht-registrierten Schwellwert nachschieben (Torpfosten-Verschiebung §2) und wird verworfen. Beide Lesarten sind in GL-006 dokumentiert.

**Kapitalfreiheits-Caveat (verbindlich):** Die signifikanten Lags sind **1–3 s** = tiefes HFT-Territorium. PRD §4 Z.133 wörtlich: „keine handelbare Kante (abgegraste 30–60s-HFT-Anomalie) → bleibt PARK." WEITER heißt **ausschließlich**: gerichtete Information existiert messbar. Es wurde KEINE Edge-/bps-/Sharpe-/Tradability-Aussage nachregistriert. **Kapital-Status bleibt PARK**; das Mess-WEITER entsperrt KEIN Kapitalmodul. Tradability wäre eine **NEUE H-04b** (eigener Eintrag, eigener Lauf, L2-Tiefen-Stream).

---

## 3. H-05 — DROP + INC-02-Bestätigung + H-05b-Empfehlung

Die PRD-v1/CS-02-Richtung „sign(OFI)=+ (Aggression-Folge)" ist **widerlegt**: KEIN Symbol/δ ist in BEIDEN Fenstern FDR-sig + positiv. Der einzige positive FDR-Survivor (BNBUSDT w0 d1s/d5s) bricht in Fenster 1 zusammen (kippt teils ins Negative). Das harte Ein-Fenster-Kriterium (negatives Vorzeichen in ≥ 1 Fenster) ist auf mehreren Symbolen verletzt → **DROP für C-01 + C-09-OFI-Bein + C-14-OFI-Erbe** (PRD §4 Z.131, kaskaden-wirksam).

**INC-02/E-04 reproduziert:** Der einzige robuste, FDR-signifikante OFI-Effekt ist **INVERS** — ETHUSDT w0 d1s: corr **−0.0550**, p=0.0050, inverse_significant. Das ist die MM-Replenishment-Lesart und bestätigt die iter-3/S2-2023-Forensik (E-04 hit_sum 0.179, fälschlich invertiertes Vorzeichen) unabhängig auf read-only-Bestandsdaten. Die ETH-Spalte ist über beide Fenster durchgängig negativ.

**Empfehlung (NICHT selbst registriert):** Der inverse ETH-Befund ist Auslöser für eine **NEUE H-05b-Pre-Registration** (MM-Replenishment als Haupt-These, ≥2-Fenster-Konsistenz, FDR, kapitalfrei). Registry-Disziplin §2: kein Torpfosten-Verschieben — H-05b ist eigener Eintrag/eigener Lauf, **WP-0/Orchestrator-Arbeit**. Caveat: Auch H-05b müsste ≥2-Fenster-Konsistenz erst nachweisen (ETH-Inversion bislang nur in w0 d1s FDR-sig, Vorzeichen aber über beide Fenster konsistent negativ).

---

## 4. H-06 — PRE-Gate-Fail (hartes DROP)

PRE-Gate ρ ≥ 0.30 ist in **keinem** der 10 Symbol×Fenster-Paare erreicht: ρ ∈ [−0.0059, +0.0145], Maximum +0.0145 (BNB w1) — ~20× unter der Schwelle, mehrere negativ. „ρ < 0.30 in EINEM Fenster → DROP" ist massiv erfüllt → **hartes DROP**. Das PRE-Gate ist ein Korrelations-Floor außerhalb F-WAVE2 — Stage 2 irrelevant.

Doppelt verfehlt: Selbst die 2 Haupt-Gate-FDR-Survivor (XRP w1 d15/d60min) liefern AUC-Lift **+0.0072 / +0.0072 < +0.03** und liegen beide im selben Fenster (≥2-Fenster-Existenz auch nicht erfüllt). PE trägt keine bedingte Vol-Information oberhalb des ρ-Floors.

---

## 5. Nächste Schritte (Folge-WPs, Prioritätsreihenfolge)

1. **WP-W2-A · H-05-Konsequenz formalisieren (sofort, kein Lauf).** C-01 → DROP im State; **C-09-OFI-Bein** und **C-14-OFI-Erbe** als „gesperrt (OFI-Vorzeichen falsifiziert)" markieren. Kaskade aus PRD §4 Z.131 dokumentieren.
2. **WP-W2-B · H-05b-Pre-Registration (WP-0/Orchestrator).** Inverse MM-Replenishment-These als neuer Registry-Eintrag H-05b mit vorregistriertem Gate (inverse Richtung Haupt-These, ≥2-Fenster-Konsistenz, FDR α=0.10 über neue/gleiche F-OFI-Erweiterung, kapitalfrei). NICHT vom gate-auditor registriert. Danach eigener read-only-Lauf.
3. **WP-W2-C · H-04 als Mess-Befund einfrieren + H-04b-Entscheidung (DEC-xx).** H-04 WEITER (Mess-Existenz) im State festhalten; Kapital-Status PARK explizit markieren. Entscheiden, ob eine Tradability-Hypothese H-04b überhaupt sinnvoll vorregistriert wird — angesichts 1–3s-Lags (HFT, PRD §4 „bleibt PARK") ist die reversibelste Option, KEINE H-04b zu starten und H-04 als kapitalfreien Existenz-Befund zu archivieren. Begründung als DEC-xx.
4. **WP-W2-D · H-06-DROP formalisieren.** C-07 → DROP; PE-Stack ohne Anker (PRE-Gate-Fail). Kein Folge-Lauf.

**Heute Nacht laufen sollte:** kein neuer Pflicht-Lauf zwingend — die drei Welle-2-Gates sind entschieden. Falls H-05b registriert wird (WP-W2-B), kann der nächste Overnight den H-05b-Inversions-Lauf (≥2 Fenster, FDR) tragen. H-04/H-05/H-06 NICHT erneut (Urteile stehen; Re-Runs nur als neue Hypothesen mit neuen Registry-Einträgen).
