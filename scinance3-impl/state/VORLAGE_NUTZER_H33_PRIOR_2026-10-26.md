# Entscheidungsvorlage an den Nutzer: H-33 (Kurzfrist-Reversal) - Prior UNBELEGT, Registrierung blockiert (DEC-102 E3)

> Orchestrator, 2026-10-26. Grundlage: `state/herleitung_h33/` (ENTSCHEIDUNGSVORLAGEN, ERSTFASSUNG_H33_entwurf,
> power_h33.json, nuisance_neg.json; REVIEW_H33.md = Zustimmung mit Auflagen zur Herleitung, bedingtes Vorab-VETO gegen
> eine C10-Registrierung auf W1/W2), DEC-102 (+Nachtrag 1). Keine Outcome-Rechnung; W1/W2 nicht geoeffnet.

## 1. Befund in drei Saetzen
1. Die Literatur liefert fuer "Kurzfrist-Reversal 1-4 Wochen" keinen Prior fuer das Bybit-USDT-Perp-Universum: Reversal
   zeigt sich nur bei sehr kleinen/illiquiden Spot-Coins (Wochenvolumen < 100 Tsd. USD); sobald ein Groessen- oder
   Umsatzfilter greift, zeigt die Literatur ~0 oder Momentum. Unser Universum (lebende Perps 343..545 je Woche, Listung
   setzt Derivate-Umsatz voraus) ist keiner Gruppe belegbar zuzuordnen; das Zaehl-Indiz zeigt eher auf "breit" bis
   "gross/liquide".
2. Die einzige Lesart, unter der eine Variante testbar (C10) wuerde, ist "klein/illiquide" (R1, IC 0,039..0,048 auf
   fm8-Skala). Sie liegt genau auf dem Niveau der Pilotwerte (0,038 / 0,050 / 0,045) - eine Wahl von R1 waere von einer
   pilotgeleiteten Wahl nicht unterscheidbar, und der Pilot darf den Prior nicht bestimmen (DEC-102 E3).
3. Neu gefunden: Die Persistenz-Null der Drittfassung (AR(1) auf den Wochenrenditen von W1/W2, 2025 gerechnet) zeigt fuer
   W2 einen richtungsgleichen Eigen-Autokorrelationsanteil (bis ~0,02 fm8 in Reversal-Richtung, etwa die Haelfte der
   Schwelle). W2 ist damit fuer rev1 nicht voll ergebnisblind: ein PASS waere nicht konfirmatorisch, ein DROP schon.

## 2. Die Zahlen (Lesart S bindend: Pilot-Streuung als Nuisance; Lesart T nur Bericht)

| Variante | MDE80 W1 / W2 (S) | MDE80 W1 / W2 (T, Bericht) | Literatur R3 "breit" | R1 "klein/illiquide" (= Pilot-Niveau) |
|---|---|---|---|---|
| rev1 (1 Woche) | 0,0395 / 0,0389 | 0,0184 / 0,0161 | 0,0015..0,0144 -> GL-012 | 0,048 -> C10 (S), Endpower m=3 0,70 |
| rev2 (2 Wochen) | 0,0418 / 0,0418 | 0,0202 / 0,0176 | 0,0019..0,0027 -> GL-012 | 0,041 -> knapp (Marge 4e-7), vorher unentscheidbar |
| rev4 (4 Wochen) | 0,0429 / 0,0431 | 0,0236 / 0,0200 | 0,0062..0,0091 -> GL-012 | 0,039 -> GL-012 |

Prior-Gitter (gemeinsame Power W1 x W2 unter S): 0,010 -> 0,02; 0,015 -> 0,06; 0,020 -> 0,12; 0,025 -> 0,22; 0,033 -> 0,45;
0,048 -> 0,85 (rev1). Unter S braucht C10 einen Prior von mindestens 0,0395 (rev1) - das liegt ueber jeder belegten
Literaturzahl fuer ein Universum mit Groessenfilter. Vollstaendige Tabelle: `herleitung_h33/ENTSCHEIDUNGSVORLAGEN.md` 2.6.

## 3. Optionen
- **(D) Default (Empfehlung des Orchestrators und des Reviews):** H-33 ist GL-012 vor der Registrierung (Prior UNBELEGT).
  Kein Bau, kein Vorlauf v7, W1/W2 bleiben fuer fm8-Reversal ungeoeffnet und stehen spaeteren Hypothesen zur Verfuegung.
  Ein GL-Vermerk (GL-036) haelt das fest. Tritt bei Stille ein.
- **(L) Lockerung:** Du waehlst R1 oder einen Gitterwert >= 0,0395 als Prior. Dann: Etikett "Lockerung, pilotgeleiteter
  Prior, Richtung nach Pilot, Autokorrelationsanteil in W2 vorab gesehen", Feststellung "ein PASS auf W1/W2 ist nicht
  konfirmatorisch" (nur ein DROP ist aussagekraeftig), Aufhebung des Review-Vetos durch dich, danach v7 (2 x 2 h),
  Bau (Richtung konfigurierbar, Modus ohne Pilot), Registrierung, Positivkontrolle, Test. Aufwand ~1-2 Tage. Ergebnis
  bestenfalls "nicht widerlegt", nie "bestaetigt".
- **(B) Blindes Fenster:** H-33 erst auf Daten ab 2026-07-01 (Reihenfolge-Frage DEC-98 E4 (b)). Mit einem Literatur-
  Prior <= 0,0144 waere auch dort erst nach grob der siebenfachen Fensterlaenge (Jahre) ein Test moeglich - praktisch
  dieselbe Lage wie bei der VRP.
- **(P) PDFs nachliefern:** Dobrynskaya 2023, LTW JF 2022, Shen/Urquhart/Wang 2020 koennten R3 stuetzen oder verwerfen;
  die Universums-Zuordnung (kein USD-Umsatz je Perp in der Akte) wuerde dadurch nicht aufgeloest.

## 4. Was nicht folgt
Kein Verdikt ueber Reversal oder Momentum; keine Aussage ueber W1/W2 ausser dem C.17-Hinweis; GL-035 unveraendert.
