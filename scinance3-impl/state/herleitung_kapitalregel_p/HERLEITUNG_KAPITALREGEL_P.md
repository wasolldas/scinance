# Herleitung: Kapitalregel Klasse P ohne MinTRL (DEC-107 (5), P-10, WD-12) - 2026-11-04

Rolle: Herleitung. Auftrag: `BRIEF_kapitalregel_klasse_p.md` (Punkte 1-7). Gelesen (nur die genannten Abschnitte):
PRD v3 1.3, 1.4, 2b, 2c, 3.2, 3.3, 4.1, 4.6, 5.2, 5.3 (VR-f13, VR-a02, VR-g08, VR-g13, VR-g14, WD-12, P-10); PRD v2 2 (L-12),
3.6, 8.1, 8.2; decisions.md DEC-58 E1 (e), DEC-93, DEC-97, DEC-104 E1/E3/E8, DEC-107; KRITIK_PRD K-12; Kompendium C.2 und
Verdikt-Kuerzel; gate_log GL-033/GL-034. Keine Marktdaten, keine Siegeldatei, nichts im Repo geaendert.

Rechnungen: `calc/kapital_sim.py` (Seed 20261104, numpy/scipy, Laufzeit 49 s), Ergebnisse `kapital_results.json`
(Abschnitte S0..S6), Stdout `kapital_sim.out`. Marken: [R] Rechnung, [U] Urteil, [V] Vermutung, [sek] Sekundaerbeleg, UNBELEGT.

Notation: `prem_t` registrierte Praemienserie je Periode und Einheit Notional; `mu_hat` gepoolter Schaetzer, `SE` seine
Standardabweichung nach VR-b09 (c = max(1, c_hat)); `z` = 2,8070 (alpha_test 0,0025; t-artig bei geschaetzter SE,
DEC-107 (1)(a)); `sigma` Streuung von `prem_t` je Periode; `k` registrierte Kosten je Periode und Einheit Notional
(Tradability-Gate, `constants_hash`); `L` Notional je Einheit Kapital (Hebel); `u = 1/L` Kapital je Einheit Notional.

---

## 1. Was ein P-A-PASS freigibt - die Kapitalregel

### 1.1 Die logische Bruecke: PASS ist eine Konfidenzaussage, keine Sharpe-Aussage

Der Mess-PASS der Klasse P lautet (DEC-107 (1)(a)): `T = mu_hat / SE >= z` **und** Stabilitaetstest nicht verworfen.
Die erste Bedingung ist aequivalent zu

    mu_L := mu_hat - z * SE >= 0,

d. h. die **einseitige untere Konfidenzgrenze der Praemie zum Niveau 1 - alpha_test (0,9975) ist nichtnegativ** [R, Umformung].
Damit gilt fuer jede Funktion f mit f(x) = 0 fuer x <= 0 und f monoton:

    P(f(mu_L) > 0 | Null) = P(PASS | Null) <= alpha_test.

Das ist der ganze Hebel: eine Kapitalregel, die ausschliesslich aus `mu_L` (nicht aus `mu_hat`) rechnet, **erbt die
Fehlerrate des Mess-Gates**, ohne dass ein Sharpe-Quotient, ein MinTRL (Lo 2002 [sek], VR-f13) oder irgendeine
oekonomische Groesse in die PASS-Bedingung wandert. Die risikoadjustierte Frage wird nicht beantwortet, sie wird **umgangen**:
die Unsicherheit der Praemie steckt in `mu_L` (Abzug von z SE), die Unsicherheit des Risikos in drei getrennten
Risikobeinen (1.3). Das Etikett "Praemien-EXISTENZ" (VR-f13 Auflage (1)) bleibt wahr; falsch wird nur der Nachsatz
"daher PARK, nicht WEITER" - der naechste Schritt ist ein Tradability-Schritt (Abschnitt 2), kein Kapitalschritt.

### 1.2 Die vier Bausteine (a)-(d) des Briefs

**(a) Praemien-Schaetzer und CI-Untergrenze.** `mu_L = mu_hat - z SE` mit `ci_basis = alpha_test` (einseitig 0,9975).
Netto gegen die registrierten Kosten des Tradability-Gates: `mu_net = max(0, mu_L - k)`. Warum nicht die CI95-Grenze
(1,6449 SE)? Beide Varianten sind durch den PASS-Indikator gegated und haben dieselbe P(Kapital > 0 | Null); die
CI95-Variante springt aber an der PASS-Grenze von 0 auf (2,8070 - 1,6449) SE = 1,1621 SE [R] und empfiehlt bei einem
falschen PASS im Mittel 1,459 SE statt 0,297 SE, also das **4,9-fache** Kapital [R, S0 `E_muL95_given_pass_null_SEunits`].
Die alpha_test-Grenze ist stetig an der PASS-Grenze (mu_L -> 0, Kapitalbedarf -> unendlich, Position -> 0): kein Klippeneffekt,
keine Anreizkante. Empfehlung: `ci_basis: alpha_test` [U].

**(b) Ruin-Kapital mit mu = CI-Untergrenze.** Fuer eine Diffusion mit Drift mu und Varianz sigma^2 je Periode (feste
Notional-Einheit, additiv) ist die Ruinwahrscheinlichkeit aus Startkapital u exakt `exp(-2 mu u / sigma^2)` [R, Standard;
Lundberg/Bachelier, hier als VR-f13-Formel vorausgesetzt]. Aufgeloest:

    u(eps) = sigma^2 / (2 mu_net) * ln(1/eps)        (Kapital je Einheit Notional)
    L_ruin = 1/u(eps) = 2 mu_net / (sigma^2 ln(1/eps)) (Notional je Einheit Kapital)

mit **mu_net statt Punktschaetzer**. MC-Pruefung S6: kappa 0,5 (eps 0,0183): Ruin 0,0166 gegen stetig 0,0183, mit
Siegmund-Korrektur fuer den diskreten Schritt 0,0163 [R, sek: Siegmund 1985 / Broadie-Glasserman-Kou 1997]; kappa 0,25:
0,00013 gegen 0,00034 (MC-SE 0,00009) - Groessenordnung bestaetigt, die stetige Formel liegt auf der Seite der Strenge.

**(c) Stress-Episoden-N als Risikomass (PRD 3.6 Auflage (4)).** Die Diffusionsformel kennt keine Spruenge. Das
Sprungrisiko wird nicht in sigma hineingerechnet (das waere eine Gaussifizierung der Peso-Verluste), sondern als eigenes
Bein mit **eigenem N**: `N_stress` = Zahl der STRESS_ABS-Episoden (VR-g13) in den Konfirmationsdaten, `s_up` = groesster
beobachteter Episodenverlust der Strategie je Einheit Notional. Nichtparametrisch gilt fuer iid stetige Verluste
`P(naechste Episode > max der N beobachteten) = 1/(N+1)` [R, Ordnungsstatistik]: N 3 -> 25 %, N 9 -> 10 %, N 10 -> 9,1 %,
N 19 -> 5 % (S0 `p_next_worse_than_max`). Bein:

    L_str = stress_loss_tol / s_up   falls N_stress >= stress_n_min,   sonst 0 (UNBELEGT -> kein Kapital).

Vorschlag `stress_n_min = 10` (Ueberschreitungswahrscheinlichkeit 9,1 %; dieselbe Zahl wie die VR-g14-Grenze "Maker im
Stress erst ab >= 10 Stress-Tagen") [U]; `stress_loss_tol` ist Risikopraeferenz des Nutzers (Beispiel 0,20), UNBELEGT bis
PRD 8.2 beantwortet.

**(d) MaxDD-Boden.** `E[MaxDD] = 1,2533 sigma_ann sqrt(T)` fuer die driftlose Diffusion [sek, Magdon-Ismail et al. 2004;
MC S6: 38,4 gegen 39,6 bei T 1000, diskreter Schritt verzerrt nach unten]. Bei Hebel L skaliert der erwartete MaxDD in
Kapitaleinheiten mit L. Bein:

    L_dd = dd_tol / (1,2533 sigma_ann sqrt(T_dd)).

Warum driftlos? Unter der Null ist die Drift null; der driftlose Boden ist also **genau der erwartete Schaden eines
falschen PASS** (mit Drift ist E[MaxDD] kleiner, S6: 24,0 statt 38,4 bei 0,05 sigma Drift). Die Verwendung des Bodens
ist deshalb keine Pessimismus-Setzung, sondern die Null-Welt-Rechnung [R].

### 1.3 Kelly-Bruchteil gegen Ruin-Kapital - dieselbe Familie

Voll-Kelly fuer Gauss-Renditen: `f* = mu/sigma^2` (Hebel). Bruchteil kappa: `L_kelly = kappa mu_net/sigma^2`. Vergleich mit
(b): `L_ruin = (2/ln(1/eps)) mu_net/sigma^2`. Also

    kappa = 2 / ln(1/eps)      <=>      eps = exp(-2/kappa)      [R, S0]

| kappa | 1/4 | 1/3 | 1/2 | 1 | | eps | 0,05 | 0,02 | 0,01 | 0,001 |
|---|---|---|---|---|---|---|---|---|---|---|
| eps = exp(-2/kappa) | 3,4e-4 | 2,5e-3 | 0,0183 | 0,135 | | kappa = 2/ln(1/eps) | 0,668 | 0,511 | **0,434** | 0,290 |

Der im Brief genannte Bruchteil 1/4..1/2 entspricht eps 3,4e-4..1,8e-2; **eps = 0,01 (kappa 0,434) liegt in diesem Band**.
Geometrische Variante (laufend rebalancierter Kapitalanteil): das Vermoegen erreicht nie null, aber
`P(Vermoegen faellt je auf den Anteil x) = x^(2/kappa - 1)` [R; MC S6: Halbierung 0,1148 gegen 0,125 bei kappa 0,5,
diskret korrigiert 0,1145]. Beide Lesarten (additiv: Ruin, geometrisch: Drawdown-Gesetz) fuehren auf dieselbe Kennzahl
2/kappa. Folge: **ein** registrierter Parameter genuegt. Registriert wird `eps` (die Groesse, die VR-f13 bereits als
Berichtszeile fuehrt), `bruchteil` wird als abgeleitetes Etikett ausgewiesen [U].

### 1.4 Kernformel

    L*  = 1[PASS] * min( L_ruin(mu_net, sigma, eps),  L_dd(sigma_ann, dd_tol, T_dd),  L_str(N_stress, s_up) )
    mu_net = max(0, mu_hat - z SE - k)
    Kapital_min = Notional / L*     (L* = 0: kein Kapitalschritt, Tradability-PARK)

Eigenschaften [R]: (i) `L* > 0 => PASS` (nie umgekehrt); (ii) stetig und monoton in mu_hat, fallend in SE, sigma, k;
(iii) `L* = 0` bei fehlendem Beleg eines Beins (k RAISE, N_stress < stress_n_min, s_up UNBELEGT) - stille Defaults sind
nach VR-g14 verboten, also ist UNBELEGT = 0 Kapital, nicht = Worst-Case-Zahl; (iv) der Schaden eines falschen PASS ist
beschraenkt: `E[mu_L | PASS, Null] = SE (phi(z)/alpha - z) = 0,297 SE`, Median 0,205 SE [R, S0/S1].

### 1.5 Was die Regel nicht ist

Sie ist kein Sharpe-Urteil (kein SR-Vergleich mit einer Schwelle; SR tritt nur implizit als mu_L/sigma auf), kein
MinTRL-Test, keine Netto-Renditeaussage (PRD 8.2: Steuer UNBELEGT), keine Order (VR-g08). Sie ist eine registrierte
Funktion, deren Eingaben zum Zeitpunkt des PASS vorliegen (mu_hat, SE aus dem Lauf; sigma, N_stress, s_up aus den
Konfirmationsdaten; k, eps, dd_tol, T_dd, stress_n_min, stress_loss_tol vorab registriert).

---

## 2. Das getrennte Tradability-Gate der Klasse P (C.2)

Der Kapitalschritt ist nie Teil des Mess-PASS. Vorschlag nach dem Praezedenzmuster H-04 (WEITER) -> H-04b (eigener
Registry-Eintrag, eigenes Gate, Anti-Gaming-Klausel; Kompendium C.2/C.3):

| Bein | Inhalt | Regelbezug | Status heute |
|---|---|---|---|
| T1 Kostenmodell | `k` je Periode je Einheit Notional aus `tradability3/constants.py`, `constants_hash` im Ergebnis; RAISE einer benoetigten Konstante => L* nicht berechenbar => Tradability-PARK | VR-g14, PZ-06 | Modul nicht gebaut (WD-08) |
| T2 Fill-Annahmen | Funding-Praemien sind Maker-/Halte-Positionen: Eintritt Maker (p_fill 0,06..0,35, 2i), Halten ohne Umschlag, Stress-Pfad Taker; Maker-Annahmen im Stress RAISE bis Messung mit >= 10 Stress-Tagen | VR-g14 RAISE-Liste, 2i | Lauf 4 massgeblich; Stress RAISE |
| T3 Stress-Abdeckung | `N_stress` STRESS_ABS-Episoden in den Konfirmationsdaten >= `stress_n_min`; `s_up` = groesster Episodenverlust der registrierten Serie (nach PASS aus den Konfirmationsdaten berechnet, Lesestatus "gelesen" im YAML); Erreichbarkeit vorab (VR-f07, E8 (d)) | VR-g13, PZ-10, PZ-27, PRD 3.6 (4) | W1/W2: 2 / 1 STRESS_ABS-Tage (DEC-74 N (1)) -> N_stress <= 3; Zone K: UNBELEGT (WD-13) |
| T4 Kapital/Steuer | `L*` ist dimensionslos; `Notional = L* x C` erst, wenn der Nutzer die Kapitalbasis C nennt; Zeile "Steuerregime UNBELEGT - Par. 8.2"; keine Netto-Aussage ohne Vorbehalt | PZ-09, PRD 8.2 | offen (P-11) |
| T5 Bestaetigung | Pflicht-Bestaetigung auf neuen Daten vor jeder Tradability-Frage: das Gate rechnet fruehestens am naechsten K-Blick bzw. in der naechsten Kohorte nach dem PASS | VR-b15 | ab K1 |
| T6 Anti-Gaming | eps, dd_tol, T_dd, stress_n_min, stress_loss_tol, s_up-Regel vor dem Lauf fixiert, nie abgesenkt, um L* > 0 zu erzwingen | C.3 | - |

**Verdikte des Tradability-Gates:** Tradability-PASS = `L* > 0` mit allen Beinen belegt; Tradability-PARK = `L* = 0`
(Kuerzel PARK im Sinn des Kompendiums "Tradability-Gate verfehlt, Kapital-Status geparkt"); KEIN VERDIKT bei RAISE.
Ein Tradability-PARK kippt den Mess-PASS nicht (C.2 symmetrisch).

**Ausfuehrungsspur (PRD 8.1 Default (b)):** Phase 4 bleibt leer bis Mess-PASS **und** Tradability-PASS **und**
ausdrueckliche Freigabe des Nutzers. Das Gate erzeugt eine Zahl (L*, Kapital_min je Notional) und einen Bericht - **keinen
Live-Order-Code, kein Live-Kapital** (Nutzer 2026-11-04, VR-g08, VR-h06). Die Entscheidungsrelevanz-Zeile des Mess-Gates
nennt als `on_pass` den Tradability-Schritt, nie einen Kapitalbetrag.

**Vorbehalte fuer den Review [U]:** (1) sigma fuer L_ruin/L_dd ist die Streuung der registrierten Praemienserie in den
Konfirmationsdaten (einschliesslich Preisbein, A1: "Summe aus Funding-Akkumulation und Preisbein"), nicht die Vorperioden-
Nuisance allein; bei ueberlappenden Praemien (H-27, c 28,2) ist die Periode der nicht ueberlappende Block. (2) Die
Diffusionsannahme ist fuer die Kalmphase gedacht; die Peso-Protektion liegt allein in T3 (Abschnitt 3.5). (3) `s_up` aus
N_stress Episoden ist ein Minimum-Schaetzer der Tail-Groesse; die 1/(N+1)-Zeile ist Bericht der Luecke, keine Heilung.

---

## 3. Rauschboden der Kapitalregel

### 3.1 Allgemein: Kapital-Power und Schrumpfung

Mit bekannter SE gilt `P(L* > 0 | mu) = q P(Z >= z - (mu - k)/SE) = 0,95 Phi((mu - k)/SE - z)` (q 0,95 Kostenquote des
Stabilitaetstests) [R]. Daraus:

- **Kapital-MDE80 = k + MDE80**: ist MDE80 = SESOI = k, so hat die Kapitalregel an der SESOI die Kapital-Power
  **0,0025** (nicht 0,80) und erreicht 0,80 erst bei mu = **2 SESOI** [R, S0]. Ein Mess-PASS an der SESOI gibt also in der
  Regel Tradability-PARK: die SESOI ist Mess-Massstab (BE-03), nicht Kapital-Massstab.
- **Schrumpfung:** bedingt auf PASS liegt der Median von mu_L bei 0,30 (ohne) bzw. 0,32 (mit Stabilitaetstest) des wahren
  mu an der MDE80 [R, S1 `share_of_true_mu_in_muL_median`]; bei mu/SE 5 bei 0,44. Die Regel empfiehlt an der MDE80
  typischerweise **ein Drittel** der Position, die das wahre mu rechtfertigen wuerde - zusaetzlich zum Faktor kappa.
- **Falscher PASS:** E[mu_L | PASS, Null] 0,297 SE (S1: 0,290 SE MC), mit k > 0 fast immer mu_net = 0 (3.2).

### 3.2 Zahlenbeispiel A1 (Funding-Praemie, GL-033; nur offene Zahlen) [R, S2]

Eingaben: sigma 354,4 bp/Woche (DEC-93; sigma_ann 25,6 %), rho_1 -0,28 (c_hat < 1 -> c = 1; Sensitivitaet c 2,44 =
1/0,41 nach DEC-67 E4), k = Taker-SESOI 36 bp/Woche (DEC-104 E3 (e); [U] als Kostenzeile verwendet), Prior 147,6 bp/Woche
bei theta 1 und 113,1 bei theta_min 0,766 (theta UNBELEGT, GL-033), eps 0,01, dd_tol 0,30 bei T_dd 1 Jahr, stress_n_min
10, stress_loss_tol 0,20, s_up 4 sigma (UNBELEGT, Sensitivitaet 3..6). Voll-Kelly am Prior theta 1: 11,75x (impliziter
Jahres-SR 3,0 - ein weiterer Hinweis, dass dieser Prior nicht belegt ist).

| n Wochen | SE bp | MDE80 bp | mu wahr bp | P(PASS) | P(L* > 0), N_stress <= 3 | P(L* > 0), N_stress 10 | L* Median (q05..q95) | u Median | DD-Bein bindet |
|---|---|---|---|---|---|---|---|---|---|
| 104 | 34,8 | 132,4 | 0 | 0,0023 | 0 | 0,0000 | 0,27 (0,01..0,71) | 3,7 | 0,00 |
| 104 | 34,8 | 132,4 | 36 (SESOI) | 0,037 | 0 | 0,0024 | 0,28 (0,02..0,94) | 3,6 | 0,07 |
| 104 | 34,8 | 132,4 | 113,1 | 0,639 | 0 | 0,264 | 0,59 (0,05..0,94) | 1,7 | 0,31 |
| 104 | 34,8 | 132,4 | 147,6 | 0,878 | 0 | 0,624 | 0,94 (0,11..0,94) | 1,07 | 0,54 |
| 260 | 22,0 | 83,7 | 36 (SESOI) | 0,116 | 0 | 0,0025 | 0,17 (0,01..0,69) | 5,8 | 0,01 |
| 260 | 22,0 | 83,7 | 147,6 | 0,950 | 0 | 0,939 | 0,94 (0,55..0,94) | 1,07 | 0,86 |
| 665 | 13,7 | 52,4 | 36 (SESOI) | 0,404 | 0 | 0,0023 | 0,10 (0,01..0,45) | 10,0 | 0,00 |
| 665 | 13,7 | 52,4 | 113,1 | 0,950 | 0 | 0,947 | 0,94 (0,56..0,94) | 1,07 | 0,80 |

Lesart: (i) **Was die Kapitalregel gewesen waere: 0.** Nicht wegen der Praemie, sondern weil W1/W2 hoechstens drei
STRESS_ABS-Episoden enthalten (< stress_n_min) - und weil A1 ohnehin GL-012 ist (MDE80 132 bp gegen SESOI 36 bp). (ii) Die
**Kapital-MDE80** (P(L* > 0) = 0,80) liegt bei 168 / 120 / 88 bp/Woche fuer 104 / 260 / 665 Wochen, also selbst bei 104
Wochen ueber dem optimistischen Prior 147,6 (Kapital-Power dort 0,62). (iii) Wo L* > 0 ist, bindet bei hoher Praemie das
MaxDD-Bein (0,937x: 30 % Drawdown-Budget bei 25,6 % Vol in einem Jahr), nicht das Ruin-Bein; an der SESOI bindet das
Ruin-Bein mit Medianhebel 0,1..0,3 (Kapital 3,6..10 je Einheit Notional). (iv) Mit c 2,44 (Sensitivitaet) sinken alle
Power-Werte (Prior theta 1 bei 104 Wochen: P(PASS) 0,44, P(L* > 0) 0,21), die Null-Zeile bleibt <= alpha.
(v) P(L* > 0 | Null) ist mit k > 0 praktisch null: `0,95 Phi(-(z + k/SE))` = 5,8e-5 bei 104 Wochen [R].

### 3.3 Zahlenbeispiel H-27 / VRP (GL-034; nur offene Zahlen) [R, S3]

Eingaben: SD der 30-Tage-Praemie 18,6 VP, c 28,2 (12,9 unabhaengige Perioden je Jahr), SE(12 Monate) 5,17 VP, Prior-Band
3,2..10,5 VP, Referenz 7,14 VP (DEC-98 N2), k = SESOI 1,5 VP [U, Kritik K-10]. Kapital je Einheit Vega-Notional in VP
(1 USD je VP Vega braucht u USD Kapital):

| Fenster | SE VP | MDE80 VP | mu wahr VP | P(PASS) | P(L* > 0) | u(0,01) Median VP/Vega (q05..q95) | u am wahren mu - k |
|---|---|---|---|---|---|---|---|
| 12 Mon. | 5,17 | 19,7 | 0 | 0,0023 | 0,0009 | - | - |
| 12 Mon. | 5,17 | 19,7 | 1,5 (SESOI) | 0,0057 | 0,0023 | - | - |
| 12 Mon. | 5,17 | 19,7 | 7,14 | 0,073 | 0,041 | 500 (134..6.468) | 141 |
| 36 Mon. | 2,98 | 11,4 | 7,14 | 0,323 | 0,171 | 629 (185..7.692) | 141 |
| 90 Mon. | 1,89 | 7,2 | 7,14 | 0,795 | 0,544 | 565 (203..5.719) | 141 |
| 90 Mon. | 1,89 | 7,2 | 10,5 | 0,948 | 0,927 | 212 (117..818) | 89 |

Lesart: Mess-Power 0,80 am Referenz-Prior braucht ~91 Monate, Kapital-Power 0,80 ~146 Monate (Faktor (7,14/5,64)^2 = 1,60)
[R]; die empfohlene Kapitalunterlegung liegt am Median beim 3,5-fachen des "wahren" Ruin-Kapitals (500 gegen 141 VP/Vega),
weil mu_net die untere Grenze ist. Das Stress-Bein ist fuer VRP-Fenster ab 2026-07-01 **UNBELEGT** (Erreichbarkeit der
STRESS_ABS-Zelle in Zone K offen, WD-13; DEC-98 N5 (2): "Ein VRP-Urteil ist auf keinem Datenweg vor 2029 erreichbar" gilt
damit auch fuer jeden VRP-Kapitalschritt). Die Kapitalregel haette also auch hier 0 ergeben.

### 3.4 Nullverteilung: P(Kapital > 0 | Null) <= alpha [R, S1/S4]

- z-Niveau (SE bekannt, 2e6 Ziehungen): P(PASS | 0) = P(L* > 0 | 0) = **0,002406** (MC-SE 3,5e-5), analytisch
  0,0025 x 0,95 = 0,002375; <= alpha: ja.
- Serienebene (n 104, geschaetzte SE, Welch-Stabilitaetstest, 3e5 Serien): mit **z** 2,8070 als Grenze **0,00299 > alpha**;
  mit t-Grenze 2,8688 (df 103) 0,00248; mit Stabilitaetstest 0,00235. Folge: die t-artige Grenze (DEC-107 (1)(a)) ist fuer
  die Kapitalregel nicht Kosmetik, sondern Bedingung der Aussage P(Kapital > 0 | Null) <= alpha bei n ~ 100.
- AR(1) rho -0,28 (A1-Nuisance) mit c = max(1, c_hat) = 1: 0,00010 - die Regel "keine Gutschrift fuer negative
  Autokorrelation" (VR-b09) macht die Kapitalregel dort konservativ.
- Power an der nominalen MDE80 (3,8101 SE) mit geschaetzter SE: 0,782 statt 0,80 (t-Grenze, Welch) [R] - Hinweis fuer die
  Power-Zeile, nicht fuer die Kapitalregel.

### 3.5 Peso-Welt (PZ-05-Analogon) [R, S5]

Null-Praemie mit Merton-Spruengen (Rate 1/3 Jahre, -35 %), Kalm-Drift so, dass das Gesamtmittel exakt 0 ist; n 104
Wochen, 3e5 Serien. P(kein Sprung im Fenster) 0,513; **P(Mess-PASS) 0,140** (gegeben kein Sprung 0,274; gegeben >= 1 Sprung
0,000). Der Mess-Test allein ist bei zwei Jahren also nicht Peso-fest - genau deshalb verlangt PZ-05, dass das Gate auf
dem Peso-Fixture durchfaellt (das muss das adversariale Fixture / der strukturelle Nulleffekt leisten, nicht die Kapitalregel).
Fuer den Kapitalschritt: ohne Stress-Bein wuerde ein Peso-PASS mit Medianhebel 2,46x belegt (ein -35-%-Sprung kostet dann
86 % des Kapitals); mit Stress-Bein (stress_n_min >= 1, Sprungtage = Stress-Tage) **0**. Grenze der Aussage [U]: reale
STRESS_ABS-Tage sind marktweit definiert und existieren auch in einem Fenster ohne Strategie-Verlust; der Schutz ist dann
nur die 1/(N+1)-Ueberschreitungszeile, die mit stress_n_min 10 bei 9,1 % liegt.

### 3.6 Was bei den Nuisance-Zahlen der Akte belegbar ist (Antwort auf die Frage des Briefs)

Bei heutiger Nuisance ist **keine positive Kapitalgroesse** belegbar: A1 und H-27 sind GL-012 (kein PASS moeglich), und
selbst unter der Annahme eines PASS waere das Stress-Bein mit N_stress <= 3 (A1) bzw. UNBELEGT (H-27) gleich null. Belegbar
sind nur die Funktion und ihre Fehlerrate: P(Kapital > 0 | Null) <= 0,0024 [R], Kapital-MDE80 = SESOI + MDE80 [R],
Schrumpfung auf ~1/3 an der MDE80 [R]. Ein erster positiver Kapitalwert setzt mindestens voraus: ein Mess-PASS in Zone K
plus Bestaetigung (VR-b15) **und** >= 10 STRESS_ABS-Episoden in den Konfirmationsdaten; bei 99-Perzentil-Definition fallen
im Erwartungswert ~3,65 Stress-Tage je Jahr [R, Konstruktion], also >= 2,7 Jahre Zone K, wenn jeder Tag eine Episode ist,
laenger bei Clusterung - fruehestens 2029 [R, Erwartungswert; Erreichbarkeit UNBELEGT, WD-13].

---

## 4. Verhaeltnis zu L-12 und zur Mission

**Vorher (K-12):** Das bestmoegliche Ergebnis der Klasse P war PARK ("kein Kapitalschritt folgt", PRD 3.6 (2)); L-12
("eine Hypothese, deren bestmoegliches Ergebnis nichts entscheidet, darf nicht eingeplant werden") war woertlich verletzt.

**Nachher:** Ein P-PASS entscheidet drei Dinge [U]: (i) die registrierte Kapitalfunktion L* wird mit den Lauf-Groessen
berechnet und berichtet; (ii) das Tradability-Gate (Abschnitt 2) wird als eigener Eintrag eroeffnet und nach VR-b15 am
naechsten Blick gerechnet; (iii) `decision_relevance.on_pass` lautet "Kapitalregel rechnen, Tradability-Gate registrieren"
- das ist ein Tradability-Schritt im Wortsinn von VR-g08 ("nur den naechsten Mess- oder Tradability-Schritt"). Ein DROP
schliesst die Praemie in der registrierten Konstruktion; GL-012 entscheidet nichts (unveraendert). L-12 ist erfuellt, weil
sich der Zustand des Programms durch den PASS aendert, auch wenn das Tradability-Gate danach PARK sagt: PARK ist dann
ein Tradability-Verdikt mit berichtetem L* = 0 und benannter Luecke (k, N_stress, s_up), nicht ein Verfassungs-PARK.

**Keine oekonomische Groesse in der PASS-Bedingung (C.2, VR-a02, BE-03):** Die PASS-Bedingung bleibt woertlich
`T >= z (t-artig) und Stabilitaetstest nicht verworfen`. Kosten k, eps, dd_tol, stress_n_min, s_up treten erst **nach**
dem PASS in einer anderen Funktion auf. Pruefbar: `L* > 0 => PASS`, nie umgekehrt; die OC-Zeile des Mess-Gates
(P(PASS | 0), P(PASS | SESOI), P(PASS | Prior)) ist von der Kapitalregel unabhaengig (S1: identische PASS-Raten). Die
SESOI bleibt Mess-Massstab und Etikett (BE-03); dass sie im Beispiel auch als Kostenzeile k dient, ist eine Festlegung des
Tradability-Gates, keine PASS-Bedingung.

**Mission:** Der "Pfad vom WEITER zum ersten Euro" (PRD 8.1) ist jetzt definiert, ohne heute Kapital oder Code zu
bewegen: Mess-PASS -> Bestaetigung (VR-b15) -> Tradability-Gate (L* > 0, alle Beine belegt) -> Nutzer-Freigabe ->
Phase 4. Jede Stufe hat ein eigenes Verdikt, eine eigene Akte und einen eigenen Entscheider.

---

## 5. Etikett und Strenge-Quotient

| Dimension | Befund |
|---|---|
| Lockerung | gegenueber PRD 3.6 (2) / VR-f13 (2): ein Kapitalschritt **kann** folgen; Richtung Geldeinsatz -> Entscheider N (DEC-107 (6)(a), (d) "jedem Geldeinsatz") |
| Verschaerfung | zusaetzliches, getrennt registriertes Gate mit vier belegpflichtigen Beinen und Anti-Gaming-Klausel; UNBELEGT = 0 Kapital |
| Strenge-Quotient Mess-Gate | **1,00** [R]: alpha, SE-Regel, SESOI, Stabilitaetstest unveraendert; MDE80 unveraendert |
| Strenge-Quotient Kapitalpfad | Kapital-MDE80 / MDE80 = 1 + k/MDE80 (A1, 104 Wochen: 168,4/132,4 = **1,27**; bei MDE80 = SESOI: **2,0**) [R]; Datenfaktor fuer Kapital-Power 0,80 bei festem mu: (mu/(mu - k))^2 (A1 Prior theta 1: 1,75; H-27 Referenz: 1,60) [R]; Zeitboden aus dem Stress-Bein: >= stress_n_min Episoden (>= 2,7 Jahre Zone K im Erwartungswert, 3.6) |
| Nutzer-Vorlage | Pflicht unabhaengig vom Quotienten (Lockerung und Geldeinsatz, DEC-107 (6)(d)); der Kapitalpfad-Quotient 2,0 an der SESOI liegt zudem ueber 1,3 (E8 (b)) |
| Entscheider | N |
| Geltung | Registrierungen ab Kohorte 1 (BE-06: auch vor dem Stichtag fuer K1 registrierte); fuer bestehende Eintraege (GL-033/034) keine Rueckwirkung, nur Vermerk |
| Rueckbauweg | `capital_rule: null` im YAML und VR-f13 Auflage (2) in der alten Fassung; eroeffnete Tradability-Gate-Eintraege bleiben Akte (PARK); kein Verdikt kippt; es gibt keinen Live-Code, der zu entfernen waere |

---

## 6. Registrierungstext (Vorschlag, Wortlaut)

### 6.1 VR-f13 neu

> **VR-f13 (3.1) Praemie statt Sharpe, Kapitalregel ohne MinTRL (Klasse P).** Urteilstragend `mean(prem)`; Sharpe, MaxDD und
> Tail-Ratio werden berichtet, nie geurteilt, jeweils mit hergeleitetem Rauschboden; `SR_block >= 0,60` und `TR <= 250 Tage`
> sind Deskriptoren; MaxDD-Boden `E[MaxDD] = 1,2533 sigma_ann sqrt(T)`; Ruin-Kapital `u(eps) = (sigma^2 / 2 mu_net) ln(1/eps)`
> als Berichtszeile **mit mu_net = max(0, mu_hat - z_krit SE - k)**. Auflagen: (1) jeder P-A-PASS traegt im PASS-Text
> "Praemien-EXISTENZ; die risikoadjustierte Frage wird nicht geurteilt; naechster Schritt ist das registrierte
> Tradability-Gate (`capital_rule.tradability_gate_ref`)"; (2) **ein Kapitalschritt folgt aus einem P-A-PASS nur ueber die
> registrierte Kapitalregel `L* = 1[PASS] min(L_ruin, L_dd, L_str)` und das getrennt registrierte Tradability-Gate; Kapital > 0
> setzt L* > 0 mit belegten Beinen, Bestaetigung nach VR-b15 und ausdrueckliche Freigabe des Nutzers voraus; kein
> Live-Order-Code, kein Live-Kapital (VR-g08)**; (3) die Beobachtungszahl wird nicht ueberzeichnet; (4) fuer das Risiko ist
> das effektive N die Zahl der STRESS_ABS-Episoden: `L_str = 0`, solange `N_stress < stress_n_min`. Herkunft: PRD 3.6; DEC-58
> E1 (e); DEC-107 (5); HERLEITUNG_KAPITALREGEL_P. Etikett: Lockerung (Kapitalschritt moeglich) mit Verschaerfung (Gate), N.
> Geltung: ab Kohorte 1.

### 6.2 Neue Pflichtzeile(n) im YAML 3.1 (PZ-31 `capital_rule`)

```yaml
capital_rule:                                  # PZ-31; VR-f13 (3.1); nur Klasse P; HERLEITUNG_KAPITALREGEL_P Abschn. 1.4
  formel: "L* = 1[PASS] * min(L_ruin, L_dd, L_str); L_ruin = 2 mu_net / (sigma^2 ln(1/eps)); L_dd = dd_tol / (1.2533 sigma_ann sqrt(T_dd)); L_str = stress_loss_tol / s_up if n_stress >= stress_n_min else 0; mu_net = max(0, mu_hat - z_krit SE - k)"
  ci_basis: alpha_test                         # einseitige untere Grenze zum Niveau 1 - alpha_test (0.9975); nie CI95
  eps: 0.01                                    # registrierte Ruinwahrscheinlichkeit (Design-Parameter, nie abgesenkt)
  bruchteil: 0.4343                            # abgeleitetes Etikett: kappa = 2 / ln(1/eps)
  sigma_quelle: konfirmationsdaten_registrierte_serie   # SD von prem_t je nicht ueberlappender Periode
  dd_tol: 0.30                                 # MaxDD-Budget in Kapitaleinheiten (Risikopraeferenz, N)
  dd_T_years: 1.0
  stress_n_min: 10                             # STRESS_ABS-Episoden (VR-g13) in den Konfirmationsdaten; darunter L_str = 0
  stress_loss_tol: 0.20                        # Kapitalverlust je schlechtester Episode (Risikopraeferenz, N)
  s_up_regel: "max Episodenverlust der registrierten Serie ueber STRESS_ABS-Episoden; Ueberschreitungszeile 1/(N+1)"
  kosten_k: {quelle: constants_hash, wert: <Zahl | RAISE>}   # Tradability-Gate T1; RAISE => L* nicht berechenbar
  tradability_gate_ref: <H-nnb>                # eigener Registry-Eintrag (Muster H-04b), Verdikte Tradability-PASS / PARK
  oc_kapital: {p_cap_pos_0: <>, p_cap_pos_sesoi: <>, p_cap_pos_prior_median: <>, kapital_mde80: <>, seeds: ">= 1000"}
  ausfuehrungsspur: "Phase 4 leer bis Mess-PASS, Tradability-PASS und Nutzer-Freigabe (PRD 8.1 (b)); kein Live-Order-Code"
```

Ergaenzend in `decision_relevance.on_pass`: "Kapitalregel rechnen und berichten; Tradability-Gate <H-nnb> registrieren;
kein Kapitalbetrag". In `report_line` zusaetzlich `mu_L`, `mu_net`, `L_star`, `u_eps`, `n_stress`, `s_up`.

### 6.3 DEC-Nachtrags-Wortlaut (Vorschlag fuer den Orchestrator; Entscheider N)

> **DEC-107 Nachtrag (5a) - Kapitalregel Klasse P ohne MinTRL (P-10, WD-12 aufgeloest).** Vorlage HERLEITUNG_KAPITALREGEL_P
> (Herleitung) und Review (ausstehend). Beschluss: (a) VR-f13 erhaelt die Fassung 6.1; Auflage (2) "kein Kapitalschritt
> folgt" wird durch die registrierte Kapitalregel ersetzt. (b) Neue Pflichtzeile `capital_rule` (PZ-31) fuer Klasse P mit den
> Feldern aus 6.2; `eps`, `dd_tol`, `stress_n_min`, `stress_loss_tol` sind Design-Parameter (kein Gate des Mess-Tests, nicht
> variierbar nach dem Lauf). (c) Das Tradability-Gate der Klasse P ist ein eigener Registry-Eintrag mit den Beinen T1..T6
> (Abschnitt 2); Verdikte Tradability-PASS / Tradability-PARK / KEIN VERDIKT; es rechnet fruehestens am ersten Blick nach dem
> Mess-PASS (VR-b15). (d) Kein Live-Order-Code, kein Live-Kapital; Phase 4 bleibt leer bis zur ausdruecklichen Freigabe.
> (e) Etikett: Lockerung gegenueber PRD 3.6 (2) (Richtung Geldeinsatz) mit Verschaerfung (zusaetzliches Gate);
> Strenge-Quotient Mess-Gate 1,00, Kapitalpfad 1 + k/MDE80; Entscheider N; Geltung ab Kohorte 1. (f) Feststellung: bei
> heutiger Nuisance ist fuer A1 und H-27 kein positiver Kapitalwert belegbar (GL-012; N_stress <= 3 bzw. UNBELEGT);
> GL-033/GL-034 erhalten den Vermerk "Kapitalregel haette 0 ergeben". (g) Rueckbauweg: `capital_rule: null`, VR-f13 alt.
> Was nicht folgt: keine Registrierung, kein Verdikt, keine Zahl einer Hypothese, kein Kapital.

---

## 7. Was nicht folgt, Vorbehalte, Kurzfassung

**Was nicht folgt:** kein Verdikt ueber Funding-Carry oder VRP (GL-033/GL-034 unveraendert); keine Registrierung; keine
Siegeldatei geoeffnet, keine Marktdaten; kein Kapitalbetrag (Kapitalbasis C, Steuer, r_opp UNBELEGT, PRD 8.2); kein
Live-Order-Code; keine Aenderung der PASS-Bedingung, der OC-Zeile oder der Power-Planung des Mess-Gates; keine Aussage,
dass die Kapitalregel Peso-Risiko heilt (sie begrenzt es ueber das Stress-Bein, 3.5); keine Heilung der
Testbarkeitsluecke der Klasse P (K-2: SR_eff >= 2,49 je 12-Monats-Fenster bleibt die Arithmetik des Mess-Tests).
Offen fuer den Review [U]: sigma-Quelle bei ueberlappenden Praemien; Episoden- gegen Tagesdefinition von N_stress
(WD-13); ob s_up aus den Konfirmationsdaten nach PASS gelesen werden darf (Lesestatus) oder aus der Vorperiode kommen
muss; ob stress_n_min 10 oder 19 (5 %) gelten soll - beide Werte sind Risikopraeferenz, nicht Statistik.

**Kurzfassung (<= 12 Zeilen):**
1. Mess-PASS <=> `mu_L = mu_hat - 2,8070 SE >= 0`; die Kapitalregel rechnet nur aus mu_L und erbt so alpha [R].
2. Kernformel: `L* = 1[PASS] min(2 mu_net/(sigma^2 ln(1/eps)), dd_tol/(1,2533 sigma_ann sqrt(T)), stress_loss_tol/s_up)`, `mu_net = max(0, mu_L - k)`; Kapital_min = Notional/L*.
3. Kelly-Bruchteil und Ruin-Kapital sind eine Familie: kappa = 2/ln(1/eps); eps 0,01 = kappa 0,434 (im Band 1/4..1/2) [R].
4. P(Kapital > 0 | Null) = P(PASS | Null) = 0,0024 (MC 2e6; analytisch 0,002375) <= alpha; mit Kosten k > 0 praktisch 0; t-artige Grenze noetig (z-Grenze gaebe 0,0030 bei n 104) [R].
5. Kapital-MDE80 = SESOI + MDE80: an der SESOI Kapital-Power 0,0025, Power 0,80 erst bei 2 SESOI; Schrumpfung auf ~1/3 des wahren mu an der MDE80 [R].
6. A1: Kapitalregel waere 0 (GL-012; N_stress <= 3 < 10); Kapital-MDE80 168 bp/Woche bei 104 Wochen > Prior 147,6 [R].
7. H-27: Kapitalregel waere 0 (GL-012; N_stress UNBELEGT, WD-13); Kapital-Power 0,80 am Referenz-Prior erst nach ~146 Monaten [R].
8. Stress-Bein (N_stress >= 10, s_up) ist die einzige Peso-Protektion des Kapitalschritts; der Mess-Test allein passiert eine Null-Peso-Welt mit 0,14 bei 104 Wochen [R].
9. Tradability-Gate getrennt registriert (T1 Kosten, T2 Fill, T3 Stress, T4 Kapital/Steuer UNBELEGT, T5 Bestaetigung, T6 Anti-Gaming); Phase 4 leer; kein Live-Code, kein Live-Kapital.
10. L-12 erfuellt: ein P-PASS eroeffnet Kapitalfunktion und Tradability-Gate; keine oekonomische Groesse in der PASS-Bedingung (C.2, BE-03).
11. Etikett: Lockerung (Kapitalschritt moeglich) mit Verschaerfung (Gate); Strenge-Quotient Mess-Gate 1,00, Kapitalpfad 1 + k/MDE80 (1,27 A1; 2,0 an der SESOI); N; ab Kohorte 1; Rueckbau `capital_rule: null`.
12. Nicht folgt: kein Verdikt, keine Registrierung, kein Kapitalbetrag, kein Code; erster positiver Kapitalwert fruehestens 2029 (>= 10 STRESS_ABS-Episoden in Zone K, UNBELEGT).
