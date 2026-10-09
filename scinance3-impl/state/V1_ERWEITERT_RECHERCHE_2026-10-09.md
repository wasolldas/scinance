# V-1 erweitert: Bybit-USDT-Perp Funding-Regeln (Primaerquellen-Recherche)

Abrufdatum aller Quellen: 2026-10-09 (Systemdatum der Sitzung). Nur Lesen im Web, nichts im Repo geaendert, keine Commits.
Auftrag: Funding-Querschnitts-Kandidat auf Bybit-USDT-Perpetuals, Vorfrage "erweiterte V-1".

## 0. Zugriffslage und Belegqualitaet (bitte zuerst lesen)

Direkter Abruf der Bybit-Seiten war NICHT moeglich:
- WebFetch: `getaddrinfo ENOTFOUND` fuer www.bybit.com, announcements.bybit.com, learn.bybit.com, bybit-exchange.github.io, prnewswire/streetinsider/aap.com.au. web.archive.org: "unable to fetch".
- curl ueber den Agent-Proxy: `CONNECT tunnel failed, response 403` fuer alle diese Hosts (auch api.bytick.com, google.com, duckduckgo.com); api.bybit.com antwortet HTTP 403. Das ist eine Proxy-/Allowlist-Sperre, nicht nur die CloudFront-Geo-Sperre. Ich habe nichts umgangen. Ein Versuch, die Proxy-Doku zu lesen, wurde vom Berechtigungssystem verweigert und nicht wiederholt.

Was ging:
1. API-Doku DIREKT und im Volltext: oeffentliches GitHub-Repo `bybit-exchange/docs` (Quelle von bybit-exchange.github.io), per raw.githubusercontent.com und flachem git-Klon (Scratchpad, HEAD `2fb5bae7`, Commit-Datum 2026-10-09, Merge PR #897; aeltester erreichbarer Commit 2024-04-23). Wortlaut ist exakt. Status "PRIMAER (direkt)".
2. Help-Center, Announcements, Contract Rules: nur ueber WebSearch. Das Tool liefert eine aufbereitete Zusammenfassung der Suchtreffer (bybit.com-Seiten), in der Zitate woertlich wiedergegeben werden, aber kein ungefilterter Seitentext. Status "PRIMAER (Snippet)": Seite ist Bybit-eigen, Wortlaut nur indirekt gesehen, Restunsicherheit bei Details. Mehrfach unabhaengig abgefragte Aussagen sind als "mehrfach bestaetigt" vermerkt.
3. Die Bybit-Pressemitteilung vom 2025-10-29 kenne ich nur ueber Verteiler-Kopien (PRNewswire, Manila Times, Chainwire u. a.) in Suchtreffern. Bybit-eigene Fassungen (bybit.com/en/press/post/...-bltcd0548e9d1b5c84a und announcements.bybit.com/en/article/bybit-to-introduce-automatic-funding-rate-adjustment-for-perpetual-contracts-blt2c875cbad4b89667/) tauchen als URL/Titel im Suchindex auf, ihr Text war nicht lesbar. Deshalb Status "[sek]" fuer alles, was NUR dort steht (Ausnahmeliste, Datum, Rueckwechsel-Wortlaut).

Kein Belegbestand wurde erfunden. Was nicht auffindbar war, heisst UNBELEGT.

---

## Frage 1: Funding-Rate-Formel, Premium-Index, Clamp, Zins-Term I

**Antwort**
- Aktuelle Formel (Help Center): `F = clamp[ P + clamp(I - P, +0.05%, -0.05%), Funding Rate Upper Limit, Funding Rate Lower Limit ]`. Also ist die Form "F = P + clamp(I - P, +-0,05 %)" richtig, aber zusaetzlich aeusserlich nochmals auf Cap/Floor (Frage 2) begrenzt. Die aeltere Fassung ohne aeusseren Clamp lautete laut Suchtreffer: wenn (I - P) innerhalb +-0,05 %, dann F = P + (I - P) = I.
- Clamp-Grenze: im Formeltext FEST 0,05 %. Eine Skalierung mit dem Intervall wird im gelesenen Text NICHT genannt. (Das ist eine Abwesenheit im Snippet, kein ausdruecklicher Beleg fuer "nicht skaliert": Status fuer "unskaliert" = UNBELEGT im strengen Sinn, Formeltext spricht dafuer.)
- Zins-Term: `I = 0.03% / (24 / Funding Interval)`. Also anteilig skaliert: 8h = 0,01 %, 4h = 0,005 %, 2h = 0,0025 %, 1h = 0,00125 % (Rechnung aus der Formel). Beispiel im Text: BTCUSD "0.01% per funding interval, assuming the funding interval is 8 hours". Ausnahme: fuer bestimmte Paare (genannt: USDCUSDT, ETHBTCUSDT) ist I = 0 %.
- Premium-Index P: Bybit berechnet I und P jede Minute und bildet darueber einen "N-Hour TWAP" (N = Funding-Intervall). Gewichtung linear aufsteigend, spaetere Minuten zaehlen mehr. Beispiel 8h: `(PI_1*1 + PI_2*2 + ... + PI_480*480) / (1 + 2 + ... + 480)`. "incorporating the Premium Index values from the previous settlement period up to the current time". Folgerung (mein Schluss, nicht woertlich): bei 1h-Intervall sind es 60 Minutenwerte, bei 4h 240.
- Minuten-Premium-Index (Help Center): `P = [Max(0, Impact Bid Price - Index Price) - Max(0, Index Price - Impact Ask Price)] / Index Price`. Impact-Preise = mittlerer Ausfuehrungspreis fuer die "Impact Margin Notional" (in USDT je Symbol konfiguriert).
- KONFLIKT: Die Seite "Contract Rules" nennt (laut Suchtreffer) eine abweichende, vermutlich aeltere Formel mit Mark Price im Zaehler und "+ Funding rate of current interval"; die Seite announcement-info/fund-rate sprach laut Suchtreffer von "Fair Buy Price". Welche Fassung die Produktion beschreibt, ist ungeklaert. Das Help Center (Update laut Suchtreffer Mai 2026) ist die juengste. Die API bietet P direkt: `GET /v5/market/premium-index-price-kline` (linear, USDT und USDC Perp, Intervalle 1 ... M), Doku direkt gelesen.
- Unterschied je Kontraktklasse: Es gibt EINEN Help-Center-Artikel fuer alle Klassen, mit derselben Formel. Dokumentiert ist nur die Ausnahme I = 0 fuer einzelne Paare (USDCUSDT, ETHBTCUSDT). Die Contract-Rules-Seite fuehrt fuer Inverse eine Altformel `I = (USD interest - underlying interest) / interval` mit 0,06 % bzw. 0,03 % Tageszins und ergibt ebenfalls 0,01 % je 8h (alt). Eine klassenspezifische Abweichung (USDT vs. USDC vs. inverse) ist NICHT belegt: UNBELEGT.
- Historischer Hinweis (Backtest relevant): Bybit-Blog "Changes in Funding Rate - USDT Perpetual Contracts and Inverse Perpetual Contracts": von 2022-06-30 00:00 UTC bis 2022-07-05 stellte Bybit die Funding-Abrechnung schrittweise auf "settled immediately" auf Basis der Rate des laufenden Intervalls um. Nur Anfangszusammenfassung gesehen. Vor Juli 2022 gilt moeglicherweise ein anderes Abrechnungsregime.

**Woertliche Zitate (kurz, via Snippet)**
- "Funding Rate (F) = clamp [Average Premium Index (P) + clamp (Interest Rate (I) - Average Premium Index (P), 0.05%, -0.05%), Funding Rate Upper Limit, Funding Rate Lower Limit]"
- "Interest Rate (I) = 0.03% / (24 / Funding Interval)"
- "Exceptions exist: For specific trading pairs (e.g., USDCUSDT or ETHBTCUSDT), the interest rate (I) will default to 0%."
- "Bybit calculates the Interest Rate (I) and the Average Premium Index (P) every minute by performing an N-Hour Time-Weighted-Average-Price (TWAP)"
- "Premium Index (P) = [Max (0, Impact Bid Price - Index Price) - Max (0, Index Price - Impact Ask Price)]/Index Price"

**URLs**
- https://www.bybit.com/en/help-center/article/Introduction-to-Funding-Rate (Spiegel: .../What-is-funding-rate-and-predicted-rate, .../article/?id=000001123&language=en_US/)
- https://www.bybit.com/en/contract-rules (Altformel, Konflikt)
- https://www.bybit.com/en/announcement-info/fund-rate/
- https://blog.bybitglobal.com/en-US/post/changes-in-funding-rate---usdt-perpetual-contracts-and-inverse-perpetual-contracts-bltf0339e13159f97bc/
- https://bybit-exchange.github.io/docs/v5/market/premium-index-kline (direkt gelesen)

**Status**: Formel, I, TWAP, P-Formel = PRIMAER (Snippet), mehrfach bestaetigt. "Clamp unskaliert" = Textbefund, strikt UNBELEGT. Klassenunterschied = UNBELEGT. Konflikt Contract Rules / fund-rate-Seite offen.

---

## Frage 2: Cap/Floor der Funding-Rate

**Antwort**
- Formel (Help Center): `Upper Limit = min((IMR - MMR) x 0.75, MMR)`, `Lower Limit = -(Upper Limit)`. IMR/MMR sind laut Suchtreffer die Anforderungen des NIEDRIGSTEN Risk-Limit-Tiers je Symbol. Also symbolabhaengig (ueber die Margin-Parameter).
- Koeffizient 0,75 ist nicht starr: Bybit kann ihn bei grosser Futures-Spot-Abweichung anpassen. Die Bandbreite wird in zwei indexierten Fassungen unterschiedlich angegeben (0,5 bis 1 bzw. 0,75 bis 1). Welche aktuell gilt: UNBELEGT.
- Bybit kann Limits bei Volatilitaet "temporarily" anpassen ("to encourage the Perpetual Contract's price to return to a reasonable range").
- In der Praxis zusaetzlich symbolweise manuelle Limit-Aenderungen per Announcement, Titel "Changes to Funding Rate Limits for XXXUSDT Perpetual Contracts" (gesehen: SNTUSDT ab 2025-04-10 06:55 UTC, SENTUSDT ab 2026-01-29 14:05 UTC; ferner Titel zu COAIUSDT, AIAUSDT, KEYUSDT, ESPUSDT, GMTUSDT, RENUSDT, ZRCUSDT, SOONUSDT, STPTUSDT). In den Intervall-Announcements zu DATAUSDT (2026-07-09) und ONUSDT (2026-08-05) steht je Settlement "Max funding rate +2.5% / -2.5%". Die Cap ist also NICHT immer die Formel, sondern kann pro Symbol hart gesetzt werden. Die konkreten Vorher/Nachher-Zahlen der Limit-Announcements waren in den Snippets nicht sichtbar.
- Ablesen je Symbol per API (direkt gelesen, siehe Frage 6): `instruments-info` -> `upperFundingRate`, `lowerFundingRate` (String; Beschreibung "Upper limit of funding date" / "Lower limit of funding date"; seit 2024-02-06 laut Changelog). Zusaetzlich `tickers` -> `fundingCap` ("Funding rate upper and lower limits") und WS-Ticker `fundingCap`. Das sind jeweils nur AKTUELLE Werte, keine Historie.
- Plausibilitaet (Rechnung, Beispieldaten der Doku, kein Beleg): Das Beispiel-JSON fuer BTCUSDT in instruments-info zeigt `upperFundingRate 0.00375`, `lowerFundingRate -0.00375`, `fundingInterval 480`. 0,00375 = (1 % - 0,5 %) x 0,75 passt zur Formel mit IMR 1 %, MMR 0,5 %. Die Doku-Beispiele sind aber nicht zwingend Echtdaten (z. B. Ticker-Beispiel BTCUSD `fundingCap 0.005`; Pre-Listing-Beispiel mit 0.05 und 480).

**Woertliche Zitate**
- "Funding Rate Upper Limit = min((Initial Margin Rate - Maintenance Margin Rate) x 0.75, Maintenance Margin Rate)"
- "Under normal circumstances, the funding rate limit = +/- Min ((IMR-MMR) x 0.75, MMR)"
- "During periods of significant market volatility, Bybit may temporarily adjust the upper and lower limits of the Funding Rate"
- API: `upperFundingRate | string | Upper limit of funding date`; `fundingCap | string | Funding rate upper and lower limits`

**URLs**
- https://www.bybit.com/en/help-center/article/Introduction-to-Funding-Rate
- https://announcements.bybit.com/en/article/changes-to-funding-rate-limits-for-sentusdt-perpetual-contracts-blt960bceb369e19627/
- https://announcements.bybit.com/article/changes-to-funding-rate-limits-for-sntusdt-perpetual-contracts-bltb0990d9f9d8c276c/
- https://announcements.bybit.com/en/article/changes-to-funding-rate-intervals-for-datausdt-perpetual-contracts--art68f15b140faa/
- https://announcements.bybit.com/en/article/changes-to-funding-rate-intervals-for-onusdt-perpetual-contracts--arta88b960ef418/
- https://bybit-exchange.github.io/docs/v5/market/instrument ; .../market/tickers ; .../websocket/public/ticker (Repo-Dateien docs/v5/market/instrument.mdx Z.138-150, tickers.mdx Z.126-129)
- https://bybit-exchange.github.io/docs/changelog/v5 (Eintrag 2024-02-06)

**Status**: Formel PRIMAER (Snippet). API-Felder PRIMAER (direkt). Koeffizienten-Bandbreite UNBELEGT (zwei Fassungen). Manuelle Symbol-Overrides: PRIMAER (Snippet, nur Titel/Effektivzeit).

---

## Frage 3: Funding-Intervalle und Zuordnung zu Symbolen

**Antwort**
- Standard: 8h (Settlement 00:00, 08:00, 16:00 UTC). Help Center sagt ausdruecklich, jedes Paar kann eigene Intervalle und Limits haben.
- Beobachtete Intervalle: 8h und 4h (Announcements DATAUSDT 2026-07-09 "4 hours", ONUSDT 2026-08-05 "8 hours"; Pre-Market: 4h), 1h (manuell seit 2022 fuer einzelne Symbole, und seit 2025-10-30 automatisch). 2h wird nur in der Pressemitteilung als Rueckwechsel-Ziel genannt ("two, four, or eight hours"); ein konkretes Symbol mit 2h-Announcement habe ich NICHT gefunden. 2h als realer Zustand: nur [sek]-Indiz.
- API-Hinweis: `fundingIntervalHour` "currently only supports whole hours"; `fundingInterval` in Minuten (Beispiel 480). Ganzzahlige Stunden und 60/120/240/480 Minuten sind damit konsistent.
- Zuordnung: pro Symbol durch Bybit, per Announcement "Changes to Funding Rate Intervals for XXXUSDT Perpetual Contracts" (Vorher/Nachher-Tabelle, Effektivzeit in UTC, Max-Funding-Rate je Settlement). Eine allgemeine, veroeffentlichte Zuordnungsregel (z. B. Volatilitaet, Marktkapital) wurde NICHT gefunden: UNBELEGT. Der Help-Center-Satz "Bybit may adjust the funding time interval based on the live market situation ..." stammt aus aelteren Texten.
- Neulisting-Default 4h: Nur im Artikel "USDC Perpetual Session Settlement Mechanism" ("For new listings, the default funding rate interval and session settlement interval are set to 4 hours") gesehen, also fuer USDC-Perps. Fuer USDT-Perps NICHT belegt: UNBELEGT. Pre-Market-Perps: Call-Auction-Phase Funding 0, Continuous-Phase fix 0,005 % alle 4h (Help Center, Snippet).
- Warnung: Ein Bybit-Learn-Artikel behauptet "all trading pairs ... 8 hours" und widerspricht dem Help Center (Help Center gilt als massgeblich).

**Woertliche Zitate**
- "Each trading pair may have different funding intervals and funding rate limits" (sinngemaesse Wiedergabe im Snippet des Help Centers)
- "This value currently only supports whole hours" (API, tickers.mdx)
- "Funding interval (minute)" (API, instruments-info)
- "Starting Jul 9, 2026, 10:50AM UTC, Bybit will adjust the funding rate intervals for DATAUSDT Perpetual Contracts" (Announcement)

**URLs**
- https://www.bybit.com/en/help-center/article/Introduction-to-Funding-Rate
- https://www.bybit.com/en/help-center/article/USDC-Perpetual-Session-Settlement-Mechanism
- https://announcements.bybit.com/en/article/changes-to-funding-rate-intervals-for-datausdt-perpetual-contracts--art68f15b140faa/
- https://announcements.bybit.com/en/article/changes-to-funding-rate-intervals-for-onusdt-perpetual-contracts--arta88b960ef418/
- https://learn.bybit.com/en/bybit-guide/what-bybit-funding-rate-fee (widersprechender Learn-Text)

**Status**: 8h/4h/1h existieren: PRIMAER (Snippet + API-Doku). 2h: [sek] (nur Pressemitteilung, kein Symbol). Zuordnungsregel: UNBELEGT.

---

## Frage 4: Auto-Switch-Regel

**Antwort**
- Datum: wirksam ab 2025-10-30 08:00 UTC, "full rollout" bis 2025-11-03 06:00 UTC, Pressemitteilung vom 2025-10-29. Die Annahme "um 2025-10-30" ist bestaetigt, aber nur ueber die Pressemitteilungs-Kopien: [sek]. Bybit-eigene Announcement-Seite existiert (Titel "Bybit to Introduce Automatic Funding Rate Adjustment for Perpetual Contracts", Kategorie latest_activities), Text nicht lesbar. Stuetzende PRIMAER-Zeitleiste: Der Docs-Repo-Commit `b36a54ff` "funding rate changes" (2025-10-13, doris-xiao-bybit) fuegte `fundingIntervalHour`, `fundingCap`, `basisRateYear` zu REST tickers hinzu; Changelog meldet WS-Ticker-Felder am 2025-10-16 und REST tickers am 2025-10-23. Das passt zur Vorbereitung, nennt das Startdatum aber nicht.
- Bedingung: Erreicht die Funding-Rate eines Perpetuals beim Settlement ihr voreingestelltes Cap bzw. Floor, schaltet das System die Settlement-Frequenz automatisch auf 1x pro Stunde. Der Satz steht auch im Help Center (Introduction to Funding Rate und Funding Fee Calculation), mehrfach bestaetigt: PRIMAER (Snippet).
- Beispiel der Pressemitteilung: Kontrakt mit 4h-Intervall und +-2 %-Limit; erreicht die Rate um 8:00 (UTC+8) 2 %, wird auf stuendlich umgestellt und das naechste Settlement ist 9:00 (UTC+8); bei 1 % um 8:00 bleibt alles unveraendert. Die Umstellung "is typically completed within about four minutes" (sichtbar um 8:04).
- Dauer und Rueckwechsel: Veroeffentlichte Regel nur sinngemaess: "the system may revert to longer intervals (every two, four, or eight hours) depending on market conditions, without prior notice" (eine andere Kopie: "programmed to revert ... as market conditions normalize"). Es gibt KEINE veroeffentlichte numerische Bedingung (Schwelle, Anzahl Perioden, Mindestdauer) und es steht nicht fest, dass auf das urspruengliche Intervall zurueckgegangen wird (Ziel kann 2h, 4h oder 8h sein). Der Help-Center-Text nennt laut mehrfacher Suche keine Rueckwechsel-Regel. => Rueckwechsel-Bedingung und Dauer: UNBELEGT.
- Vorab-Ankuendigung: Nein. Help Center: "Future updates to funding rate limits and settlement frequencies will be adjusted dynamically without separate announcements." Der Wechsel wird erst nach dem Settlement (ca. 4 Minuten spaeter) in der Plattform/API sichtbar. Ein Vorlauf in Minuten/Stunden ist nicht zugesagt.
- Manuelle Intervallwechsel VOR dem Datum: Ja, regelmaessig per Announcement "Changes to Funding Rate Intervals for XXXUSDT Perpetual Contracts". Gesehen (Effektivzeit laut Snippet, neues Intervall in den Snippets meist nicht sichtbar):
  - KAITOUSDT 2025-03-05 04:35 UTC; ZRCUSDT 2025-06-29 03:10 UTC; OMNIUSDT 2025-07-29 12:15 UTC; IPUSDT 2025-08-31 01:50 UTC (announcements.bybitglobal.com); LINEAUSDT 2025-09-13 05:50 UTC; AIAUSDT 2025-10-09 08:30 UTC; FUSDT 2025-10-21 08:35 UTC; MEUSDT 2025-10-27 14:05 UTC.
  - Weitere Titel ohne Datum im Snippet: HYPERUSDT, ZETAUSDT, HIVEUSDT, GASUSDT, RAREUSDT, SNTUSDT, LPTUSDT, TSLAUSDT, STPTUSDT ("Limits and Intervals"), "Adjustment of Funding Rate Interval for CYBERUSDT Contract", "Adjustment of Funding Rate Interval, Upper and Lower Limit of Funding Rate for USDCUSDT Perpetual Contract".
  - Fruehe 1h-Umstellung: Blog "Funding Intervals for Several Perpetual Contracts to be Adjusted": SLPUSDT, FLOWUSDT, STXUSDT, XEMUSDT von "every 8 hours to once per hour". Datum nicht aus Bybit-Text lesbar. Indiz [sek]: CCXT-Issue #12024 vom 2022-02-19 zeigt SLP stuendlich. Ein Drittanbieter-Text (CScalp) nennt zusaetzlich EGLDUSDT und ENJUSDT mit 1h.
- Auch NACH dem Datum laufen manuelle Announcements weiter (DATAUSDT 2026-07-09 -> 4h, Cap +-2,5 %; ONUSDT 2026-08-05 -> 8h, Cap +-2,5 %). Beide setzen laut Snippet ein "After Adjustment"-Intervall; das "Before" war nicht sichtbar. Ob sie einen vorherigen Auto-1h-Zustand zuruecksetzen, ist UNBELEGT.
- Vorlauf der manuellen Announcements: Veroeffentlichungszeitpunkt war in den Snippets nicht sichtbar, nur die Effektivzeit. Der Vorlauf ist UNBELEGT.
- Eine Aenderung der Auto-Switch-Regel nach 2025-10-30 (Updates, neue Ausnahmen) habe ich nicht gefunden (kein Beleg fuer Aenderung, aber auch kein Gegenbeleg).

**Woertliche Zitate**
- "When a Perpetual Contract's funding rate reaches its preset upper or lower limit during settlement, the system will automatically switch the settlement frequency to once per hour." (Help Center, mehrfach; gleichlautend in der Pressemitteilung)
- "Future updates to funding rate limits and settlement frequencies will be adjusted dynamically without separate announcements." (Help Center)
- "may revert to longer intervals - every two, four, or eight hours - depending on market conditions, without prior notice" (Pressemitteilung, via Suchtreffer-Wiedergabe)
- "The adjustment is typically completed within about four minutes." (Pressemitteilung)
- "Bybit will update the funding intervals for SLPUSDT, FLOWUSDT, STXUSDT and XEMUSDT Perpetual Contracts from every 8 hours to once per hour." (Bybit-Blog, via Snippet)

**URLs**
- https://www.prnewswire.com/news-releases/bybit-launches-dynamic-settlement-frequency-system-for-perpetual-contracts-302598179.html (Pressemitteilung, Verteiler)
- https://www.bybit.com/en/press/post/bybit-launches-dynamic-settlement-frequency-system-for-perpetual-contracts-bltcd0548e9d1b5c84a (Bybit-eigen, Text nicht gelesen)
- https://announcements.bybit.com/en/article/bybit-to-introduce-automatic-funding-rate-adjustment-for-perpetual-contracts-blt2c875cbad4b89667/ (Bybit-eigen, Text nicht gelesen)
- https://www.bybit.com/en/help-center/article/Introduction-to-Funding-Rate ; https://www.bybit.com/en/help-center/article/Funding-fee-calculation
- https://blog.bybit.com/en-US/post/funding-intervals-for-several-perpetual-contracts-to-be-adjusted-bltff480818ab02cc66/
- https://announcements.bybit.com/article/changes-to-funding-rate-intervals-for-kaitousdt-perpetual-contracts-blt65b35ff6db844664/ (und ZRCUSDT, OMNIUSDT, LINEAUSDT, AIAUSDT, FUSDT, MEUSDT analog)
- https://github.com/ccxt/ccxt/issues/12024 ([sek], 2022)
- https://github.com/bybit-exchange/docs/commit/b36a54ff (Repo-Historie, direkt)

**Status**: Bedingung "Cap erreicht -> 1h" und "keine separate Ankuendigung": PRIMAER (Snippet), mehrfach. Datum 2025-10-30: [sek] (Pressemitteilung). Rueckwechsel-Regel/Dauer: UNBELEGT (nur qualitativ, [sek]). Vorab-Ankuendigung Auto-Switch: PRIMAER (Snippet) = keine. Manuelle Wechsel vor dem Datum: PRIMAER (Snippet: Titel + Effektivzeit); Zieldauer/Vorlauf UNBELEGT.

---

## Frage 5: Ausnahmelisten / feste Intervalle

**Antwort**
- Ausgenommen vom Auto-Switch "initially": BTCUSDT, BTCUSDC, BTCUSD, ETHUSDT, ETHUSDC, ETHUSD, ETHBTCUSDT, ETHWUSDT (Pressemitteilung; in allen gesehenen Kopien gleich). Ausserdem: Bybit kann das Feature fuer einzelne Kontrakte nach Liquiditaets-/Volatilitaetsgesichtspunkten abschalten ("may be disabled for certain contracts"). Eine laufend gepflegte oder spaeter erweiterte Ausnahmeliste habe ich nicht gefunden: UNBELEGT. "initially" heisst, die Liste kann sich geaendert haben.
- Feste 1h-Symbole: Es gibt keine veroeffentlichte Dauerliste "fest 1h". Historisch wurden SLPUSDT, FLOWUSDT, STXUSDT, XEMUSDT (Blog, Datum unklar, vermutlich 2022) manuell auf 1h gesetzt; ob sie noch 1h haben, ist UNBELEGT (hier hilft nur instruments-info). Pre-Market-Perps: fest 4h in der Continuous-Phase (Help Center).
- Ob die Ausnahme fuer BTC/ETH "fuer immer" gilt, ist nicht zugesichert (Formulierung "initially"). Das tatsaechliche Intervall von BTCUSDT/ETHUSDT ist nur aus instruments-info ablesbar; das Doku-Beispiel zeigt fundingInterval 480 (Beispieldaten, kein Beleg).

**Woertliche Zitate**
- "will not initially apply to BTCUSDT, BTCUSDC, BTCUSD, ETHUSDT, ETHUSDC, ETHUSD, ETHBTCUSDT, or ETHWUSDT Perpetual Contracts" (Pressemitteilung, via Suchtreffer-Wiedergabe)
- "may be disabled for certain contracts based on liquidity or volatility considerations" (ebenso)

**URLs**: wie Frage 4 (Pressemitteilung PRNewswire / Manila Times: https://www.manilatimes.net/2025/10/29/tmt-newswire/pr-newswire/bybit-launches-dynamic-settlement-frequency-system-for-perpetual-contracts/2210901 / Chainwire: https://chainwire.org/2025/10/29/bybit-launches-dynamic-settlement-frequency-system-for-perpetual-contracts/).

**Status**: Ausnahmeliste = [sek] (Pressemitteilungs-Kopien; Bybit-Originaltext nicht lesbar). Aktuelle Liste/Fixed-1h-Liste = UNBELEGT.

---

## Frage 6: API-Felder fuer Intervall und Wechsel

Alle Aussagen direkt aus dem Repo `bybit-exchange/docs` (HEAD 2026-10-09), Dateien `docs/v5/...`. Status PRIMAER (direkt).

**Antwort**
- `GET /v5/market/instruments-info` (category=linear): `fundingInterval` (integer, "Funding interval (minute)"), `upperFundingRate`, `lowerFundingRate` (string). Nur AKTUELLER Stand. Hinweis der Doku: Standard 500 Eintraege, fuer alle linear-Symbole Paginierung per `cursor`/`limit` noetig. Die Doku zeigt fundingInterval im Repo seit mindestens 2024-04-23 (frueher erreichbarer Commit); `upperFundingRate`/`lowerFundingRate` laut Changelog seit 2024-02-06.
- `GET /v5/market/tickers` (linear/inverse): `fundingRate`, `nextFundingTime` (ms), `fundingIntervalHour` (string, Stunden, "currently only supports whole hours"), `fundingCap` (string). Neu laut Changelog-Eintrag 2025-10-23 (Docs-Commit 2025-10-13).
- WebSocket `tickers.{symbol}`: `fundingIntervalHour`, `fundingCap` (nur Perpetual; "for Futures, this field will not return"), `fundingRate`, `nextFundingTime`. Neu laut Changelog 2025-10-16.
- `GET /v5/market/funding/history` (category linear, inverse): Antwortfelder NUR `symbol`, `fundingRate`, `fundingRateTimestamp` (ms). KEIN Intervallfeld je Record. Das Intervall muss aus den Zeitabstaenden aufeinanderfolgender `fundingRateTimestamp` rekonstruiert werden (oder als Snapshot-Reihe von instruments-info/tickers gespeichert werden). Doku-Text: "Each symbol has a different funding interval ... To query the funding rate interval, please refer to the instruments-info endpoint." Paging: nur `startTime` -> Fehler; nur `endTime` -> 200 Records bis `endTime`; keines -> 200 Records bis jetzt; `limit` 1-200.
- Historie der Intervallwechsel: Die Doku nennt keinen Endpunkt, der vergangene Intervall- oder Cap-Aenderungen liefert (Repo-Suche nach funding interval: nur die oben genannten Felder). Beleg dafuer: UNBELEGT im Sinn "kein Endpunkt vorhanden", Befund = keiner gefunden.
- Hilfsmittel fuer Announcement-Mining: `GET /v5/announcements/index` (locale Pflicht; `type`, `tag` z. B. "Derivatives", `USDT`; `page`, `limit`; Felder `title`, `description`, `url`, `dateTimestamp`, `publishTime`). Damit lassen sich manuelle Intervall-/Limit-Announcements samt `publishTime` (Vorlauf!) maschinell sammeln. Der Auto-Switch erzeugt KEINE Announcements.
- `GET /v5/market/premium-index-price-kline` liefert den Premium-Index (P) je Kline, relevant fuer eine eigene Nachrechnung von F.

**Woertliche Zitate**
- history-fund-rate.mdx: "Each symbol has a different funding interval. For example, if the interval is 8 hours and the current time is UTC 12, then it returns the last funding rate, which settled at UTC 8."
- Response: `> symbol`, `> fundingRate | Funding rate`, `> fundingRateTimestamp | Funding rate timestamp (ms)`
- instrument.mdx Z.138: `> fundingInterval | integer | Funding interval (minute)`
- tickers.mdx Z.126: `> fundingIntervalHour | string | Funding interval hour - This value currently only supports whole hours`; Z.129: `> fundingCap | string | Funding rate upper and lower limits`

**URLs**
- https://bybit-exchange.github.io/docs/v5/market/instrument
- https://bybit-exchange.github.io/docs/v5/market/history-fund-rate
- https://bybit-exchange.github.io/docs/v5/market/tickers
- https://bybit-exchange.github.io/docs/v5/websocket/public/ticker
- https://bybit-exchange.github.io/docs/v5/announcement
- https://bybit-exchange.github.io/docs/changelog/v5
- Repo: https://github.com/bybit-exchange/docs (lokaler Klon im Scratchpad: bybitdocs/docs)

---

## Hinweise fuer V-1 (mein Schluss, KEIN Beleg)

1. Wegen Auto-Switch seit 2025-10-30 (ohne Ankuendigung, mit intraday-Wechsel nach Cap-Treffer) und manueller Wechsel davor ist ein statisches "Symbol -> Intervall" falsch. Intervall je Funding-Record aus Abstaenden von `fundingRateTimestamp` ableiten und Raten auf Stundenbasis normieren (Rate / Intervall in h). Fuer Zeitraeume davor/danach getrennt auswerten.
2. Selektionseffekt: Ein Cap-Treffer loest 1h-Funding aus, d. h. der Extremwert ist genau der Punkt, an dem sich die Zahlungsfrequenz aendert. Der Zahlungsstrom nach Extremen ist damit nicht mit dem 8h-Modell vergleichbar.
3. Cap ist symbolweise veraenderlich (Formel plus manuelle Overrides); `upperFundingRate`/`fundingCap` nur als Momentaufnahme taeglich snapshotten.
4. Die Pre-Oct-2025-Phase kennt manuelle 4h/1h-Wechsel je Symbol (Announcements); die Wechselzeitpunkte lassen sich zusaetzlich ueber `/v5/announcements/index` und die Timestamp-Abstaende rekonstruieren.

---

## Offene Punkte (UNBELEGT)

- Bybit-eigener Volltext der Auto-Switch-Announcement/Pressemitteilung (nur Titel/URL, Inhalt ueber Verteiler-Kopien).
- Numerische Rueckwechsel-Regel (Schwelle, Anzahl Perioden, Mindestdauer, Zielintervall).
- Aktuelle Ausnahmeliste vom Auto-Switch; ob sie sich seit 2025-10-30 geaendert hat.
- Intervall-Skalierung des +-0,05 %-Clamps (Text nennt keine).
- Bandbreite des Cap-Koeffizienten (0,5-1 vs 0,75-1).
- Reale 2h-Symbole.
- Vorlauf (Veroeffentlichung vs. Effektivzeit) der manuellen Intervall-Announcements.
- Klassenspezifische Unterschiede (USDT/USDC/inverse) ueber die genannte I = 0-Ausnahme hinaus.
- Vorher-Werte der Announcements DATAUSDT/ONUSDT (ob Reset eines Auto-1h-Zustands).

---

## Tabelle: Regel | Wert | Quelle | Status

| Regel | Wert | Quelle | Status |
|---|---|---|---|
| Funding-Formel | F = clamp[P + clamp(I-P, +0.05%, -0.05%), Lower, Upper] | Help Center "Introduction to Funding Rate" | PRIMAER (Snippet) |
| Clamp-Grenze | fest 0,05 %, keine Intervall-Skalierung im Text genannt | dito | PRIMAER (Snippet) / "unskaliert" UNBELEGT |
| Zins-Term I | 0.03% / (24 / Intervall_h): 8h 0,01 %; 4h 0,005 %; 2h 0,0025 %; 1h 0,00125 % | dito | PRIMAER (Snippet) |
| I-Ausnahmen | I = 0 fuer z. B. USDCUSDT, ETHBTCUSDT | dito | PRIMAER (Snippet) |
| Premium-Index-Mittel | N-h TWAP, linear steigende Gewichte (8h: 1..480 Minuten) | dito | PRIMAER (Snippet) |
| Minuten-Premium | [max(0, ImpactBid-Index) - max(0, Index-ImpactAsk)] / Index | dito; Contract Rules weicht ab | PRIMAER (Snippet), Konflikt offen |
| Klassenunterschied I | keiner dokumentiert ausser I=0-Paare | Help Center | UNBELEGT |
| Cap/Floor | +-min((IMR-MMR)*0.75, MMR), IMR/MMR niedrigster Risk-Tier | Help Center | PRIMAER (Snippet) |
| Koeffizient 0,75 anpassbar | Bandbreite 0,5-1 bzw. 0,75-1 (uneinheitlich) | Help Center (zwei Fassungen) | UNBELEGT (Bandbreite) |
| Cap-Overrides | symbolweise Announcements "Changes to Funding Rate Limits"; z. B. +-2,5 % bei DATAUSDT/ONUSDT | announcements.bybit.com | PRIMAER (Snippet) |
| Cap je Symbol ablesen | instruments-info upperFundingRate/lowerFundingRate; tickers/WS fundingCap | API-Doku (Repo) | PRIMAER (direkt) |
| Intervalle | Standard 8h; 4h, 1h real beobachtet; Pre-Market 4h | Help Center, Announcements | PRIMAER (Snippet) |
| 2h-Intervall | nur als Rueckwechsel-Option genannt, kein Symbol gefunden | Pressemitteilung | [sek] |
| Zuordnung Symbol -> Intervall | pro Symbol durch Bybit, per Announcement; keine Regel veroeffentlicht | Help Center, Announcements | PRIMAER (Snippet) / Regel UNBELEGT |
| Auto-Switch Bedingung | Rate = Cap/Floor beim Settlement -> 1x pro Stunde | Help Center, Pressemitteilung | PRIMAER (Snippet) |
| Auto-Switch Startdatum | 2025-10-30 08:00 UTC; Vollausrollung bis 2025-11-03 06:00 UTC | Pressemitteilung 2025-10-29 (PRNewswire u. a.) | [sek] |
| Umstellungsdauer | ca. 4 Minuten (8:00 -> 8:04 UTC+8) | Pressemitteilung | [sek] |
| Vorab-Ankuendigung Auto-Switch | keine ("without separate announcements") | Help Center | PRIMAER (Snippet) |
| Rueckwechsel | "may revert ... every two, four, or eight hours ... depending on market conditions, without prior notice"; keine Schwelle/Dauer | Pressemitteilung | [sek]; numerische Regel UNBELEGT |
| Manuelle Wechsel vor 2025-10-30 | ja, z. B. KAITOUSDT 2025-03-05, ZRCUSDT 2025-06-29, OMNIUSDT 2025-07-29, IPUSDT 2025-08-31, LINEAUSDT 2025-09-13, AIAUSDT 2025-10-09, FUSDT 2025-10-21, MEUSDT 2025-10-27 | announcements.bybit.com | PRIMAER (Snippet) |
| Fruehe 1h-Umstellung | SLP, FLOW, STX, XEM von 8h auf 1h (ca. 2022) | blog.bybit.com; CCXT #12024 | PRIMAER (Snippet) / Datum [sek] |
| Manuelle Wechsel nach 2025-10-30 | DATAUSDT 2026-07-09 -> 4h; ONUSDT 2026-08-05 -> 8h | announcements.bybit.com | PRIMAER (Snippet) |
| Ausnahmen Auto-Switch | BTCUSDT, BTCUSDC, BTCUSD, ETHUSDT, ETHUSDC, ETHUSD, ETHBTCUSDT, ETHWUSDT "initially"; Abschaltung je Kontrakt moeglich | Pressemitteilung | [sek]; aktuelle Liste UNBELEGT |
| Feste 1h-Symbole | keine Dauerliste veroeffentlicht | - | UNBELEGT |
| instruments-info Intervall | fundingInterval (Minuten, integer), nur aktuell | bybit-exchange.github.io v5/market/instrument | PRIMAER (direkt) |
| tickers Intervall | fundingIntervalHour (Stunden, ganzzahlig), fundingCap; REST seit Changelog 2025-10-23, WS seit 2025-10-16 | v5/market/tickers, websocket ticker, changelog | PRIMAER (direkt) |
| funding/history | nur symbol, fundingRate, fundingRateTimestamp; Intervall je Record NICHT enthalten, aus Zeitabstaenden rekonstruieren | v5/market/history-fund-rate | PRIMAER (direkt) |
| Intervall-Wechselhistorie per API | kein Endpunkt gefunden; Announcements-API `/v5/announcements/index` nur fuer manuelle Wechsel | v5/announcement | PRIMAER (direkt) / Historie-Endpunkt UNBELEGT |
