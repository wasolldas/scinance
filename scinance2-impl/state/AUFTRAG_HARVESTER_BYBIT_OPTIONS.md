# Auftrag an das Data-Harvest-Projekt: Bybit-Options-Aufzeichnung

> **Adressat:** Data-Harvest-Projekt (`E:\Claude\Projects\Data Harvest\data-harvest`),
> NICHT dieses Repo. Erstellt 2026-08-21 nach DEC-43.
> **Zweck:** Ohne diesen Strom ist die Bybit-Options-Seite des Programms
> (H-26b Tradability, C-33 VRP-Pilot) dauerhaft nicht messbar — es existiert
> heute **keine einzige Zeile** Bybit-Options-Quotedaten.

## 1. Warum dieser Auftrag an den Harvester geht und nicht an Scinance

Es gibt zwei Aufzeichnungssysteme:

| System | Schreibt nach | Wird von den Messungen gelesen? |
|---|---|---|
| Scinance C-36 Recording-Engine (`src/bybit_edge/recorder/`) | `data/parquet/recording_f0/{stream}/{date}/` | **NEIN** — kein Treiber liest diesen Pfad |
| **Data-Harvest-Projekt** | `data/harvest/raw/{exchange}/{stream}/symbol=…/date=…/` + `state/harvest_manifest.sqlite` | **JA — alle Wellen 4–8** |

Der bekannte `option_tickers`-Defekt (GL-004: Subscribe erfolgreich, 0 Frames,
WS-Abbruch alle ~30 s mit `1011 keepalive ping timeout`) betrifft die
**Scinance-Engine**. Selbst repariert wuerde sie in einen Pfad schreiben, den
keine Hypothese liest. Die Aufzeichnung muss deshalb im Harvester entstehen.

## 2. Der entscheidende Hebel: der Harvester kann es bereits

Der Harvester zeichnet **Deribit-Optionen erfolgreich auf**:
`deribit/tickers` mit **5.964 Symbolen** ueber ~38 Tage, dazu
`deribit/markprice.options` und `deribit/dvol`. Das heisst: der Umgang mit
einer grossen, staendig wechselnden Optionskette (Symbol-Churn durch Verfaelle,
Batch-Subscribes, Reconnect-Handling) ist dort **bereits geloest**. Der Auftrag
ist damit kein Neubau, sondern die Uebertragung eines funktionierenden Musters
auf eine zweite Boerse.

## 3. Was aufgezeichnet werden soll

**Strom:** Bybit v5 **Option**-WS (eigener Endpunkt, getrennt vom
Linear-Endpunkt — der bereits als `bybit/tickers` laeuft und NUR Perp/Linear
enthaelt, 3.751 Symbole, kein Optionsinhalt).

**Zielbenennung im Baum (Vorschlag, konsistent zum Bestand):**
`raw/bybit/option_tickers/symbol=<BTC-26DEC26-100000-C>/date=<YYYY-MM-DD>/`

**Pflichtfelder — der eigentliche Punkt des Auftrags:**
Die Aufzeichnung MUSS **bid1Price, bid1Size, ask1Price, ask1Size** enthalten.
Grund: Die Scinance-Engine hatte ein Schema OHNE bid/ask (nur markPrice,
markIv, Greeks, OI) — damit waere ein Options-Spread selbst bei laufender
Aufzeichnung **nie messbar** gewesen. Der Spread ist bei Optionen die
entscheidende Friktionsgroesse; ohne bid/ask ist die gesamte
Tradability-Frage unbeantwortbar.
Zusaetzlich wuenschenswert (falls im selben Frame vorhanden): markIv, bid1Iv,
ask1Iv, underlyingPrice, delta/gamma/vega/theta, openInterest.

**Rohdaten-Prinzip:** wie bei allen anderen Stroemen das **vollstaendige
Payload-JSON** speichern (`payload_json`), nicht ein vorab gefiltertes
Feld-Subset. Was heute weggelassen wird, fehlt spaeter unwiederbringlich.

## 4. Zu verifizieren (NICHT aus dem Gedaechtnis uebernehmen)

> **NACHTRAG 2026-08-24 (WP-5): Punkt 2 ist ERLEDIGT — und positiv.**
> Der Nutzer hat auf seiner Maschine die vollstaendigen REST-Ketten gezogen
> (BTC 762 / ETH 658 Symbole, gepinnt unter `state/wp5_20260824/`).
> `/v5/market/tickers?category=option` liefert **bid1Price, bid1Size,
> ask1Price, ask1Size, bid1Iv, ask1Iv** sowie markPrice, markIv,
> underlyingPrice, delta/gamma/vega/theta, openInterest, volume24h,
> turnover24h. Zweiseitig quotiert sind 98 % (BTC) / 97 % (ETH) der Symbole.
> **Konsequenz fuer den Bauaufwand:** ein zusaetzliches Orderbook-Topic je
> Optionssymbol ist NICHT noetig — der Ticker-Strom allein genuegt. Das war
> der teuerste Zweig des Auftrags und er entfaellt.
> **Einschraenkung, die bestehen bleibt:** verifiziert ist der **REST**-Ticker.
> Dass der **WS**-Frame dieselben Felder fuehrt, ist damit sehr wahrscheinlich,
> aber nicht bewiesen. Punkt 1 (Endpunkt/Topic-Format), Punkt 3
> (Subscribe-Limits) und Punkt 4 (Keepalive — der GL-004-Verdacht) bleiben
> unveraendert offen und sind vor dem Bau zu pruefen.
> **Notausgang, falls der WS-Frame doch kein bid/ask fuehrt:** REST-Polling
> derselben Endpoints in festem Intervall. Zwei Aufrufe (baseCoin=BTC, =ETH)
> decken die gesamte Kette ab — genau das tut
> `handoff_local/snap_bybit_optchain.ps1` bereits als Ueberbrueckung.


Ich konnte die Bybit-API aus meiner Umgebung nicht abfragen (Proxy blockt).
Die folgenden Punkte bitte vor dem Bau gegen die **aktuelle** Doku bzw. ein
Live-Sample pruefen — die Feldnamen oben sind eine begruendete Erwartung,
keine verifizierte Tatsache:

1. Exakter WS-Endpunkt fuer `category=option` und das Topic-Format
   (vermutlich `tickers.<symbol>`).
2. Ob bid/ask im Ticker-Frame liegen oder ein separates Orderbook-Topic
   noetig ist (`orderbook.25.<symbol>` o. ae.).
3. Subscribe-Limits: maximale Args pro Subscribe-Nachricht und maximale
   Topics pro Verbindung — bei einer vollen BTC+ETH-Kette sind das
   Groessenordnungen von tausend Symbolen, also mehrere Verbindungen.
4. **Keepalive:** Der GL-004-Defekt (`1011 keepalive ping timeout` alle ~30 s
   bei erfolgreichem Subscribe und 0 Frames) deutet genau hierauf. Pruefen,
   welches Ping-Intervall/-Format der Option-Endpunkt verlangt und ob es vom
   Linear-Endpunkt abweicht. Das ist der wahrscheinlichste Grund, warum die
   Scinance-Engine nie Daten bekam.

**Verifikation auf deiner Maschine (PowerShell, public, keine Keys):**

```powershell
# 1) Wie viele Optionssymbole, und welche Felder hat EIN Ticker?
$t = (Invoke-RestMethod "https://api.bybit.com/v5/market/tickers?category=option&baseCoin=BTC").result.list
$t.Count
$t[0] | Format-List *

# 2) DER KERNTEST: sind bid/ask ueberhaupt im Ticker-Frame?
$t[0].PSObject.Properties.Name -match 'bid|ask|Iv|delta'

# 3) Instrumentendefinition (Strike, Verfall, Tick-Size) fuer den Symbol-Refresh
(Invoke-RestMethod "https://api.bybit.com/v5/market/instruments-info?category=option&baseCoin=BTC&limit=2").result.list[0] | Format-List *
```

Punkt 2 entscheidet den Aufwand: liefert er `bid1Price`/`ask1Price`, genuegt
der Ticker-Strom allein. Liefert er sie NICHT, braucht der Harvester
zusaetzlich ein Orderbook-Topic je Optionssymbol — deutlich mehr Verbindungen,
mehr Volumen, und das muss VOR dem Bau feststehen.

*(Hinweis: `curl` ist in PowerShell ein Alias fuer `Invoke-WebRequest`, und
`head` gibt es dort nicht — die Unix-Pipe schlaegt fehl.)*

## 5. Betriebliche Anforderungen (aus den Programm-Lehren)

- **Manifest-Pflege:** Der Strom muss in `harvest_manifest.sqlite` mit
  `status='DONE'` je Tag gefuehrt werden — alle Entsperr-Bedingungen des
  Programms (H-11, H-21, H-26) fragen `done_days` ab, nicht Ordner-Existenz.
- **Symbol-Churn:** Optionssymbole verfallen. Taegliche Aktualisierung der
  Instrumentenliste, sonst laeuft die Subscription leer (und faellt genau
  nicht auf, weil „Subscribe ok" trotzdem gemeldet wird — die GL-004-Falle).
- **Laut scheitern:** Wenn ein Tag 0 Frames liefert, muss das im Manifest
  sichtbar sein (nicht DONE) und nicht als leerer, aber „fertiger" Tag
  erscheinen. Ein stiller Nulltag ist schlimmer als ein fehlender.
- **Volumen-Erwartung:** Deribit liefert bei ~6.000 Symbolen handhabbare
  Mengen; Bybit-Optionen sind deutlich duenner besetzt. Kein Kapazitaets-
  Problem erwartet, aber vor dem Dauerbetrieb einen Tag messen.

## 6. Was danach freigeschaltet ist

- **Options-Spread-Zensus** auf Bybit (analog WP-4 fuer Perps, das dort in
  86 Minuten eine ganze Strategieklasse erledigt hat).
- **H-26b** (Tradability der VRP-Ernte) wird ueberhaupt erst registrierbar.
- **C-33** (der einzige Options-PILOT des PRD) beginnt seine 12-Monats-Uhr —
  sie steht heute bei **null**, und jeder Tag ohne Aufzeichnung verschiebt
  den fruehestmoeglichen Kapital-Entscheid um einen Tag nach hinten.

**Das ist der Grund, warum dieser Auftrag Prioritaet hat, obwohl er nichts
sofort misst: er ist der einzige Posten im Programm mit einem
Zwoelf-Monats-Vorlauf.**
