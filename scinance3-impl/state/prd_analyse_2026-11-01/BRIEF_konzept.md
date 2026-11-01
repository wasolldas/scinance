# Auftrag (Grundsatzanalyse): Konzeptionelle und strukturelle Luecken; unentdeckte Forschungsfelder
Lies zuerst state/prd_analyse_2026-11-01/REGELN_UND_LESELISTE.md (Regeln gelten), dann die Leseliste vollstaendig, besonders PRD
Abschnitte 1-3, 9, 11 (Wissenschafts-Exkurs), Kompendium C/D/E, Bilanz Teil C, A2-Akte Teil C (PILOT_ROUTE), das
Dateninventar und die Code-Modulliste. Ausgabe: state/prd_analyse_2026-11-01/KONZEPT_UND_FORSCHUNGSFELDER.md.

Die Grundidee des Programms war, Methoden aus Naturwissenschaft und Technik (Falsifikation, Vorregistrierung, Messung
vor Hypothese, Rauschboden, Nullmodelle, Positivkontrollen) auf grosse Tradingdaten anzuwenden. Denke grundsaetzlich:
1. Wie weit ist diese Idee realisiert, und wo ist sie in Buchhaltung umgeschlagen? Welche "wissenschaftlichen"
   Instrumente fehlen ganz (z. B. ein generatives Marktmodell, Simulations-basierte Inferenz, Modellvergleich statt
   Punkt-Hypothesen, Mess-Invarianten, Skalengesetze, Informationstheorie, Netzwerk-/Lead-Lag-Strukturen, Ereigniszeit
   statt Kalenderzeit, Regime-/Zustandsmodelle, Extremwerttheorie, Hawkes-/Punktprozesse fuer Liquidationen, Mikro-zu-
   Makro-Aggregation)? Welche davon sind auf den vorhandenen Daten (publicTrade 2020-2026 fuer 5 Symbole, orderbook
   2023-2026, tardis options_chain 2019-2026, Options-Ticker ab 2026-06, Liquidationen ab 2026-06, Funding/OI, DVOL,
   Tagespanel aller USDT-Perps) sofort anwendbar?
2. Strukturelle Luecke "Horizont-Schere": 2.0 testete Mikrostruktur auf Mikrostruktur-Horizonten (Friktion toetet),
   3.0 testet Praemien auf Wochen-/Jahreshorizont mit wenigen Beobachtungen (Power toetet). Ist der ungenutzte Mittelweg
   "Grosse-Daten-Merkmale (Orderfluss, Liquidationen, OI, Optionsfluss, Funding-Dynamik) als Praediktoren fuer
   Tages-/Wochenrenditen" a priori tot (Kompendium D pruefen!) oder nie geprueft? Rechne analytisch vor, welche
   Effektgroessen (Korrelation/IC auf Tagesbasis) mit ~2.000-2.400 Tagen BTC/ETH bei Power 0,80 aufloesbar waeren und
   was das in bp je Tag gegen die Friktionswand bedeutet. Welche OOS-Disziplin braeuchte ein solcher Weg?
3. Fenster-Politik: "Einmal-Gut", Blind-Siegel, REZENZ und Pilot-Verbrauch erzeugen jahrelange Wartezeit. Entwirf ein
   alternatives, gleich strenges Datenregime fuer eine automatische Institution, das Explorations-, Validierungs- und
   versiegelte Konfirmationszonen trennt, Mehrfachtests ueber die ganze Institution verbucht (Alpha-Spending/FDR-Budget),
   und blinde Zonen rollierend freigibt, ohne dass je ein Ergebnis zweimal gesehen wird. Benenne, was daran Lockerung
   und was Verschaerfung gegen heute ist, und was der Nutzer entscheiden muss.
4. Unentdeckte Forschungsfelder: liste 8-12 konkrete Felder/Hypothesenfamilien, die (a) zur Mission passen (Wand
   irrelevant oder kapitalfreie Messung), (b) auf heutigen Daten testbar sind oder mit einem klaren Datenauftrag an
   Data-Harvest testbar werden, (c) nicht in Kompendium D stehen oder dort nur horizontabhaengig gestorben sind. Je Feld:
   Mechanismus und Zahler, Statistik, benoetigte Daten (vorhanden/nachzubestellen), grobe Power-Einschaetzung aus
   bekannten Nuisance-Zahlen (analytisch, keine Datenrechnung), Friktions-Etikett, Risiken (Data-Snooping, Regime).
   Beispiele zum Pruefen, nicht zum Uebernehmen: Liquidations-Kaskaden und Nachlauf; OI-/Funding-Dynamik als
   Positionierungsmass; Optionsfluss/GEX aus der tardis-Kette 2019-2026; Term-Struktur der Basis (A4-Vorlaeufer auf
   Deribit-Futures seit 2017?); Cross-Venue-Lead-Lag auf Tagesbasis; Volatilitaets-Regime und Praemien-Konditionierung;
   Delisting-/Listing-Ereignisse im Panel; Wochentags-/Intraday-Saisonalitaet im Querschnitt; Stablecoin-/On-Chain-Daten
   (fehlen); Makro-Ereignisse.
5. Was haben wir uebersehen, das nichts mit Statistik zu tun hat (Organisation, Agentenpolitik, Kostenstruktur, Rolle des
   Nutzers, Dokumentationslast, Fehlerkultur wie der Varianzzerlegungs-Kanal B-2)?
Form: nummerierte Thesen T-1.. mit Beleg, Gegenargument, Richtung, Zustaendigkeit; dann die Felder-Tabelle; dann
"Was NICHT folgt". Kurzfassung <= 12 Zeilen.
